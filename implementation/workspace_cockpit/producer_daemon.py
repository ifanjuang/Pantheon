#!/usr/bin/env python3
"""Standalone AFFAIRES filesystem -> Hindsight producer daemon.

This process owns filesystem scan/watch/reconcile and producer writes. It exposes no UI.
The optional Cockpit reads the persisted SQLite projection independently.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import threading

from hindsight_producer import HindsightHTTPClient, HindsightProducer
from server import DEFAULT_EXCLUDED_FOLDERS, WorkspaceIndex, _path_is_within, _root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=_root, required=True)
    parser.add_argument("--max-depth", type=int, default=8, choices=range(1, 17))
    parser.add_argument("--exclude-folder", action="append", default=[])
    parser.add_argument(
        "--state-db",
        default=os.getenv("WORKSPACE_INDEX_DB", "/state/index.sqlite3"),
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
    state_db = Path(args.state_db)
    if not state_db.is_absolute():
        raise SystemExit("--state-db must be an absolute path")
    if any(_path_is_within(state_db, root) for _, root in args.root):
        raise SystemExit("--state-db must remain outside every watched workspace root")
    if args.reconcile_seconds < 0.1:
        raise SystemExit("--reconcile-seconds must be >= 0.1")
    if args.watch_debounce_ms < 0:
        raise SystemExit("--watch-debounce-ms must be >= 0")
    if args.hindsight_max_submits_per_reconcile < 1:
        raise SystemExit("--hindsight-max-submits-per-reconcile must be >= 1")
    if args.hindsight_max_file_mb < 1:
        raise SystemExit("--hindsight-max-file-mb must be >= 1")
    if args.hindsight_settle_observations < 1:
        raise SystemExit("--hindsight-settle-observations must be >= 1")
    if not args.hindsight_url.strip() or not args.hindsight_bank_id.strip():
        raise SystemExit("standalone producer requires Hindsight URL and bank id")

    configured_exclusions = [
        value.strip()
        for value in os.getenv("WORKSPACE_EXCLUDED_FOLDERS", "").split(",")
        if value.strip()
    ]
    excluded_folder_names = tuple(
        dict.fromkeys((*DEFAULT_EXCLUDED_FOLDERS, *configured_exclusions, *args.exclude_folder))
    )

    client = HindsightHTTPClient(
        args.hindsight_url.strip(),
        args.hindsight_bank_id.strip(),
        authorization=os.getenv("WORKSPACE_HINDSIGHT_AUTHORIZATION", "").strip(),
        timeout_seconds=float(os.getenv("WORKSPACE_HINDSIGHT_TIMEOUT_SECONDS", "30")),
        parser=args.hindsight_parser,
        max_file_bytes=args.hindsight_max_file_mb * 1024 * 1024,
    )
    producer = HindsightProducer(
        roots=args.root,
        state_db=state_db,
        client=client,
        max_submits_per_reconcile=args.hindsight_max_submits_per_reconcile,
        settle_observations=args.hindsight_settle_observations,
        source_kind=args.hindsight_source_kind,
    )
    index = WorkspaceIndex(
        args.root,
        args.max_depth,
        state_db,
        reconcile_seconds=args.reconcile_seconds,
        debounce_seconds=args.watch_debounce_ms / 1000.0,
        enable_watcher=not args.no_watch,
        producer=producer,
        excluded_folder_names=excluded_folder_names,
    )

    stop = threading.Event()

    def request_stop(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    index.start()
    print("affaires-producer started", flush=True)
    try:
        while not stop.wait(1.0):
            pass
    finally:
        index.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
