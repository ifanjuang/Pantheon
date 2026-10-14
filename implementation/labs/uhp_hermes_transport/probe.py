#!/usr/bin/env python3
"""Operator-only synthetic UHP transport probe for Pantheon-Next#1141.

This utility is an external qualification client, not a Pantheon runtime path.
Only read-only discovery is allowed without explicit SYNTHETIC_ONLY acknowledgement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from uhp_client import UhpClient, UhpTransportError


RUN_MODES = {"task", "stream", "cancel", "file", "artifact"}


class ProbeError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ProbeError(f"{path} must contain one JSON object")
    return raw


def _case_material(root: Path, case_id: str) -> tuple[dict[str, Any], str]:
    case = root / case_id
    basis = _load_json(case / "basis.json")
    prompt = (case / "prompt.txt").read_text(encoding="utf-8").strip()
    if basis.get("case_id") != case_id:
        raise ProbeError("fixture case_id does not match requested case")
    return basis, prompt


def _find_harness(payload: dict[str, Any], harness_id: str) -> dict[str, Any]:
    harnesses = payload.get("harnesses")
    if not isinstance(harnesses, list):
        raise ProbeError("UHP harness list is malformed")
    matches = [
        item
        for item in harnesses
        if isinstance(item, dict) and item.get("id") == harness_id
    ]
    if len(matches) != 1:
        raise ProbeError(f"harness_id {harness_id!r} was not found exactly once")
    harness = matches[0]
    if harness.get("base") != "hermes":
        raise ProbeError(
            f"harness_id {harness_id!r} is base={harness.get('base')!r}, not hermes"
        )
    return harness


def _receipt_base(
    *,
    mode: str,
    basis: dict[str, Any] | None,
    discovery: dict[str, Any],
    harness: dict[str, Any],
    admission_id: str | None,
    requested_protocol_version: str,
) -> dict[str, Any]:
    return {
        "object_type": "uhp_transport_probe_receipt",
        "synthetic": True,
        "mode": mode,
        "requested_protocol_version": requested_protocol_version,
        "served_default_version": discovery.get("default_version"),
        "served_versions": discovery.get("versions"),
        "conformance_class": discovery.get("conformance_class"),
        "harness": {
            "id": harness.get("id"),
            "base": harness.get("base"),
            "defaultModel": harness.get("defaultModel"),
            "disabledTools": harness.get("disabledTools"),
            "mcpServers": harness.get("mcpServers"),
            "skills": harness.get("skills"),
        },
        "case_id": basis.get("case_id") if basis else None,
        "execution_basis_digest": (
            basis.get("execution_basis_digest") if basis else None
        ),
        "pantheon_admission_probe": admission_id,
        "client_metadata_correlation_only": bool(admission_id),
        "host_level_admission_correlation": "not_measured",
        "effective_tool_surface_proven": False,
        "automatic_retry_performed": False,
        "technical_receipt_is_evidence": False,
        "activation_changed": False,
        "production_authorization": False,
    }


def _task_metadata(case_id: str, admission_id: str | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "pantheon_qualification_case": case_id,
        "pantheon_qualification_issue": "1141",
    }
    if admission_id:
        metadata["pantheon_admission_probe"] = admission_id
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one synthetic UHP transport probe for Pantheon-Next#1141"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("UHP_BASE_URL", ""),
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("UHP_API_KEY", ""),
        help="Prefer UHP_API_KEY environment variable.",
    )
    parser.add_argument("--harness-id", required=True)
    parser.add_argument(
        "--protocol-version",
        default="2026-09-28",
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=Path("/tmp/pantheon-uhp-1141"),
    )
    parser.add_argument(
        "--mode",
        choices=["observe", *sorted(RUN_MODES)],
        default="observe",
    )
    parser.add_argument("--case-id")
    parser.add_argument("--admission-id")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--ack", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if not args.base_url or not args.api_key:
            raise ProbeError("UHP_BASE_URL and UHP_API_KEY are required")
        if args.mode in RUN_MODES:
            if args.ack != "SYNTHETIC_ONLY":
                raise ProbeError(
                    "execution modes require --ack SYNTHETIC_ONLY"
                )
            if not args.case_id:
                raise ProbeError("execution modes require --case-id")
            if not args.idempotency_key:
                raise ProbeError("execution modes require --idempotency-key")

        client = UhpClient(
            args.base_url,
            args.api_key,
            protocol_version=args.protocol_version,
        )
        discovery = client.discovery()
        harnesses = client.list_harnesses()
        harness = _find_harness(harnesses, args.harness_id)

        basis = None
        prompt = None
        if args.case_id:
            basis, prompt = _case_material(
                args.fixture_root,
                args.case_id,
            )

        receipt = _receipt_base(
            mode=args.mode,
            basis=basis,
            discovery=discovery,
            harness=harness,
            admission_id=args.admission_id,
            requested_protocol_version=args.protocol_version,
        )

        if args.mode == "observe":
            print(
                json.dumps(
                    receipt,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        assert basis is not None
        assert prompt is not None
        metadata = _task_metadata(
            basis["case_id"],
            args.admission_id,
        )
        started = time.monotonic()

        if args.mode == "task":
            response = client.submit_task(
                input_value=prompt,
                harness_id=args.harness_id,
                idempotency_key=args.idempotency_key,
                metadata=metadata,
            )
            receipt["response"] = response

        elif args.mode == "stream":
            events = client.stream_task(
                input_value=prompt,
                harness_id=args.harness_id,
                idempotency_key=args.idempotency_key,
                metadata=metadata,
            )
            receipt["event_count"] = len(events)
            receipt["stream_sequence_valid"] = (
                client.stream_sequence_valid(events)
            )
            receipt["events"] = events

        elif args.mode == "cancel":
            response = client.submit_task(
                input_value=prompt,
                harness_id=args.harness_id,
                idempotency_key=args.idempotency_key,
                background=True,
                metadata=metadata,
            )
            response_id = response.get("id")
            if not isinstance(response_id, str) or not response_id:
                raise ProbeError(
                    "background UHP response did not return an id"
                )
            cancelled = client.cancel_response(response_id)
            reread = client.get_response(response_id)
            receipt["initial_response"] = response
            receipt["cancel_response"] = cancelled
            receipt["reread_response"] = reread

        elif args.mode == "file":
            source = (
                args.fixture_root
                / basis["case_id"]
                / "synthetic.eml"
            )
            if not source.is_file():
                raise ProbeError(
                    f"transient source fixture is missing: {source}"
                )
            source_bytes = source.read_bytes()
            uploaded = client.upload_file(
                source,
                media_type="message/rfc822",
            )
            file_id = uploaded.get("id")
            if not isinstance(file_id, str) or not file_id:
                raise ProbeError("UHP upload did not return a file id")
            input_value = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        {
                            "type": "input_file",
                            "filename": source.name,
                            "file_id": file_id,
                        },
                    ],
                }
            ]
            response = client.submit_task(
                input_value=input_value,
                harness_id=args.harness_id,
                idempotency_key=args.idempotency_key,
                metadata=metadata,
            )
            receipt["source_sha256"] = hashlib.sha256(
                source_bytes
            ).hexdigest()
            receipt["upload"] = uploaded
            receipt["response"] = response
            receipt["uhp_file_transport_observed"] = True
            receipt["ephemeral_lease_semantics_proven"] = False
            receipt["affaires_hindsight_source_persistence"] = "not_measured"

        elif args.mode == "artifact":
            response = client.submit_task(
                input_value=prompt,
                harness_id=args.harness_id,
                idempotency_key=args.idempotency_key,
                metadata=metadata,
            )
            response_metadata = response.get("metadata")
            session_id = (
                response_metadata.get("session_id")
                if isinstance(response_metadata, dict)
                else None
            )
            if not isinstance(session_id, str) or not session_id:
                raise ProbeError(
                    "artifact task response has no session_id"
                )
            listed = client.list_session_files(session_id)
            hashes = []
            for item in listed.get("files", []):
                if not isinstance(item, dict):
                    continue
                container_id = item.get("container_id")
                file_id = item.get("id")
                if (
                    isinstance(container_id, str)
                    and isinstance(file_id, str)
                ):
                    payload = client.download_file(
                        container_id,
                        file_id,
                    )
                    hashes.append(
                        {
                            "container_id": container_id,
                            "file_id": file_id,
                            "filename": item.get("filename"),
                            "bytes": len(payload),
                            "sha256": hashlib.sha256(
                                payload
                            ).hexdigest(),
                        }
                    )
            receipt["response"] = response
            receipt["session_files"] = listed
            receipt["downloaded_artifacts"] = hashes
            receipt["governance_promotion_status"] = "not_measured"

        receipt["elapsed_seconds"] = time.monotonic() - started
        print(
            json.dumps(
                receipt,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0
    except (ProbeError, UhpTransportError, OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "object_type": "uhp_transport_probe_error",
                    "error": str(exc),
                    "technical_receipt_is_evidence": False,
                    "activation_changed": False,
                    "production_authorization": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
