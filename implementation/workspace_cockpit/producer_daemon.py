#!/usr/bin/env python3
"""Standalone multi-vault filesystem -> Hindsight producer daemon.

This process owns filesystem scan/watch/reconcile and producer writes. It exposes no UI.
The optional Cockpit reads the persisted SQLite projection independently.
"""

from __future__ import annotations

import argparse
import atexit
import os
from pathlib import Path
import signal
import threading

from hindsight_producer import HindsightHTTPClient, HindsightProducer
from document_ocr import PdfOcr
from processing_queue import CoordinatorLock
from server import DEFAULT_EXCLUDED_FOLDERS, WorkspaceIndex, _path_is_within, _root
from vault_profiles import load_vault_configuration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=_root, default=[])
    parser.add_argument(
        "--vault-config",
        default=os.getenv("WORKSPACE_VAULT_CONFIG", ""),
        help="credential-free JSON profiles for one multi-vault producer process",
    )
    parser.add_argument("--max-depth", type=int, default=8, choices=range(1, 17))
    parser.add_argument("--exclude-folder", action="append", default=[])
    parser.add_argument(
        "--state-db",
        default=os.getenv("WORKSPACE_INDEX_DB", "/state/index.sqlite3"),
    )
    parser.add_argument(
        "--processing-queue-db",
        default=os.getenv("WORKSPACE_PROCESSING_QUEUE_DB", ""),
        help="optional absolute shared SQLite path for ordered processing and Cockpit controls",
    )
    parser.add_argument(
        "--coordinator-lock-file",
        default=os.getenv("WORKSPACE_COORDINATOR_LOCK_FILE", ""),
        help="optional absolute advisory lock path; defaults beside the shared queue database",
    )
    parser.add_argument(
        "--reconcile-seconds",
        type=float,
        default=float(os.getenv("WORKSPACE_RECONCILE_SECONDS", "3600")),
    )
    parser.add_argument(
        "--watch-debounce-ms",
        type=int,
        default=int(os.getenv("WORKSPACE_WATCH_DEBOUNCE_MS", "500")),
    )
    parser.add_argument("--no-watch", action="store_true")
    parser.add_argument(
        "--hindsight-url",
        default=os.getenv("WORKSPACE_HINDSIGHT_URL", ""),
    )
    parser.add_argument(
        "--hindsight-bank-id",
        default=os.getenv("WORKSPACE_HINDSIGHT_BANK_ID", ""),
    )
    parser.add_argument(
        "--hindsight-parser",
        default=os.getenv("WORKSPACE_HINDSIGHT_PARSER", "markitdown"),
    )
    parser.add_argument(
        "--hindsight-max-submits-per-reconcile",
        type=int,
        default=int(os.getenv("WORKSPACE_HINDSIGHT_MAX_SUBMITS_PER_RECONCILE", "100")),
    )
    parser.add_argument(
        "--hindsight-max-file-mb",
        type=int,
        default=int(os.getenv("WORKSPACE_HINDSIGHT_MAX_FILE_MB", "100")),
    )
    parser.add_argument(
        "--hindsight-settle-observations",
        type=int,
        default=int(os.getenv("WORKSPACE_HINDSIGHT_SETTLE_OBSERVATIONS", "2")),
    )
    parser.add_argument(
        "--hindsight-source-kind",
        default=os.getenv("WORKSPACE_HINDSIGHT_SOURCE_KIND", "project-sync"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    vault_configuration = None
    if args.vault_config.strip():
        if args.root:
            raise SystemExit("--root cannot be combined with --vault-config")
        try:
            vault_configuration = load_vault_configuration(args.vault_config)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        roots = [(profile.name, profile.root) for profile in vault_configuration.vaults]
    else:
        if not args.root:
            raise SystemExit("provide --root or --vault-config")
        roots = args.root
    state_db = Path(args.state_db)
    if not state_db.is_absolute():
        raise SystemExit("--state-db must be an absolute path")
    if any(_path_is_within(state_db, root) for _, root in roots):
        raise SystemExit("--state-db must remain outside every watched workspace root")
    processing_queue_db = Path(args.processing_queue_db) if args.processing_queue_db.strip() else None
    if processing_queue_db is not None and (
        not processing_queue_db.is_absolute()
        or any(_path_is_within(processing_queue_db, root) for _, root in roots)
    ):
        raise SystemExit("--processing-queue-db must be absolute and outside every watched workspace root")
    ocr_enabled = os.getenv("WORKSPACE_OCR_ENABLED", "true").strip().casefold() in {"1", "true", "yes", "on"}
    ocr_processor = None
    if ocr_enabled:
        ocr_cache = Path(os.getenv("WORKSPACE_OCR_CACHE_DIR", str(state_db.parent / "ocr-cache")))
        if not ocr_cache.is_absolute() or any(_path_is_within(ocr_cache, root) for _, root in roots):
            raise SystemExit("WORKSPACE_OCR_CACHE_DIR must be absolute and outside every watched workspace root")
        ocr_processor = PdfOcr(
            ocr_cache,
            docling_mcp_url=os.getenv("WORKSPACE_OCR_DOCLING_MCP_URL", "http://127.0.0.1:8020/mcp"),
            vision_url=os.getenv("WORKSPACE_OCR_VISION_URL", "http://127.0.0.1:11434"),
            vision_model=os.getenv("WORKSPACE_OCR_VISION_MODEL", "qwen3.8:27b"),
            timeout_seconds=int(os.getenv("WORKSPACE_OCR_TIMEOUT_SECONDS", "180")),
            max_pages=int(os.getenv("WORKSPACE_OCR_MAX_PAGES", "160")),
            max_duration_seconds=int(os.getenv("WORKSPACE_OCR_MAX_DURATION_SECONDS", "2400")),
        )
    reconcile_seconds = vault_configuration.reconcile_seconds if vault_configuration else args.reconcile_seconds
    watch_debounce_ms = vault_configuration.watch_debounce_ms if vault_configuration else args.watch_debounce_ms
    max_depth = (
        {profile.name: profile.max_depth for profile in vault_configuration.vaults}
        if vault_configuration else args.max_depth
    )
    excluded_profile_folders = vault_configuration.excluded_folders if vault_configuration else ()
    required_mounts = (
        {profile.name: profile.mount_root for profile in vault_configuration.vaults}
        if vault_configuration else {}
    )
    if reconcile_seconds < 0.1:
        raise SystemExit("--reconcile-seconds must be >= 0.1")
    if not vault_configuration and args.watch_debounce_ms < 0:
        raise SystemExit("--watch-debounce-ms must be >= 0")
    if args.hindsight_max_submits_per_reconcile < 1:
        raise SystemExit("--hindsight-max-submits-per-reconcile must be >= 1")
    if args.hindsight_max_file_mb < 1:
        raise SystemExit("--hindsight-max-file-mb must be >= 1")
    if args.hindsight_settle_observations < 1:
        raise SystemExit("--hindsight-settle-observations must be >= 1")
    configured_exclusions = [
        value.strip()
        for value in os.getenv("WORKSPACE_EXCLUDED_FOLDERS", "").split(",")
        if value.strip()
    ]
    excluded_folder_names = tuple(
        dict.fromkeys((*DEFAULT_EXCLUDED_FOLDERS, *configured_exclusions, *excluded_profile_folders, *args.exclude_folder))
    )
    authorization = os.getenv("WORKSPACE_HINDSIGHT_AUTHORIZATION", "").strip()
    timeout_seconds = float(os.getenv("WORKSPACE_HINDSIGHT_TIMEOUT_SECONDS", "30"))
    if vault_configuration and processing_queue_db is None:
        processing_queue_db = state_db
    coordinator_lock: CoordinatorLock | None = None
    if processing_queue_db is not None:
        lock_path = (
            Path(args.coordinator_lock_file)
            if args.coordinator_lock_file.strip()
            else processing_queue_db.with_name(processing_queue_db.name + ".coordinator.lock")
        )
        if not lock_path.is_absolute() or any(_path_is_within(lock_path, root) for _, root in roots):
            raise SystemExit("--coordinator-lock-file must be absolute and outside every watched workspace root")
        coordinator_lock = CoordinatorLock(lock_path)
        try:
            coordinator_lock.acquire()
        except (OSError, RuntimeError) as exc:
            raise SystemExit(str(exc)) from exc
        atexit.register(coordinator_lock.release)
    if vault_configuration:
        hindsight_url = args.hindsight_url.strip()
        if not hindsight_url:
            raise SystemExit("multi-vault mode requires WORKSPACE_HINDSIGHT_URL")
        clients = {
            profile.name: HindsightHTTPClient(
                hindsight_url,
                profile.bank_id,
                authorization=authorization,
                timeout_seconds=timeout_seconds,
                parser=profile.parser,
                max_file_bytes=profile.max_file_mb * 1024 * 1024,
            )
            for profile in vault_configuration.vaults
        }
        producer = HindsightProducer(
            roots=roots,
            state_db=state_db,
            clients=clients,
            max_submits_per_reconcile=3,
            max_active_hindsight_operations=3,
            settle_observations=vault_configuration.settle_observations,
            source_kinds={profile.name: profile.source_kind for profile in vault_configuration.vaults},
            metadata_profiles={profile.name: profile.metadata_profile for profile in vault_configuration.vaults},
            project_overview_prompts={
                profile.name: profile.project_overview_prompt
                for profile in vault_configuration.vaults
                if profile.project_overview_prompt is not None
            },
            processing_queue_db=processing_queue_db,
            ocr_processor=ocr_processor,
            missing_source_grace_seconds=vault_configuration.missing_source_grace_seconds,
        )
    else:
        if not args.hindsight_url.strip() or not args.hindsight_bank_id.strip():
            raise SystemExit("standalone producer requires Hindsight URL and bank id")
        client = HindsightHTTPClient(
            args.hindsight_url.strip(),
            args.hindsight_bank_id.strip(),
            authorization=authorization,
            timeout_seconds=timeout_seconds,
            parser=args.hindsight_parser,
            max_file_bytes=args.hindsight_max_file_mb * 1024 * 1024,
        )
        producer = HindsightProducer(
            roots=roots,
            state_db=state_db,
            client=client,
            max_submits_per_reconcile=args.hindsight_max_submits_per_reconcile,
            settle_observations=args.hindsight_settle_observations,
            source_kind=args.hindsight_source_kind,
            processing_queue_db=processing_queue_db,
            ocr_processor=ocr_processor,
        )
    producer.start_status_poller()
    producer.start_submission_dispatcher()
    index = WorkspaceIndex(
        roots,
        max_depth,
        state_db,
        reconcile_seconds=reconcile_seconds,
        debounce_seconds=watch_debounce_ms / 1000.0,
        enable_watcher=not args.no_watch,
        producer=producer,
        excluded_folder_names=excluded_folder_names,
        required_mounts=required_mounts,
    )

    stop = threading.Event()

    def request_stop(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    try:
        index.start()
        print("multi-vault producer started" if vault_configuration else "workspace producer started", flush=True)
        while not stop.wait(1.0):
            pass
    finally:
        index.stop()
        producer.close()
        if coordinator_lock is not None:
            coordinator_lock.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
