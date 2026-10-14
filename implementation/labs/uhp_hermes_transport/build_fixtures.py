from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from qualification import canonical_digest


TASK_CONTRACT_REF = "task-contract://synthetic/uhp-1141/v1"
CONTEXT_PACK_REF = "context-pack://synthetic/uhp-1141/v1"


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _basis(
    case_id: str,
    question: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    basis = {
        "case_id": case_id,
        "task_contract_ref": TASK_CONTRACT_REF,
        "context_pack_ref": CONTEXT_PACK_REF,
        "question": question,
        "context": context,
        "requested_effect": "read_only",
    }
    basis["execution_basis_digest"] = canonical_digest(basis)
    return basis


def build_all(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)

    core_context = {
        "fact_alpha": "ALPHA-1141",
        "fact_beta": "BETA-2026",
        "contradiction": {
            "source_a": "DELAY_DAYS=14",
            "source_b": "DELAY_DAYS=21",
        },
        "instruction": (
            "Preserve both contradictory values; do not resolve them."
        ),
    }
    core_question = (
        "Return one JSON object with fact_alpha, fact_beta, source_a and "
        "source_b. Copy exact values from the admitted synthetic context."
    )
    core_basis = _basis(
        "T1-core-read-only",
        core_question,
        core_context,
    )
    _write(
        root / "T1-core-read-only" / "basis.json",
        json.dumps(core_basis, indent=2) + "\n",
    )
    _write(
        root / "T1-core-read-only" / "prompt.txt",
        core_question + "\n",
    )

    stream_question = (
        "Produce a deterministic numbered sequence from 0001 to 0200, "
        "one item per line, then end with STREAM-END-1141. "
        "This fixture exists only to exercise transport streaming."
    )
    stream_basis = _basis(
        "T4-stream-cancel",
        stream_question,
        {"marker": "STREAM-END-1141", "synthetic": True},
    )
    _write(
        root / "T4-stream-cancel" / "basis.json",
        json.dumps(stream_basis, indent=2) + "\n",
    )
    _write(
        root / "T4-stream-cancel" / "prompt.txt",
        stream_question + "\n",
    )

    eml = (
        b"From: sender@example.invalid\r\n"
        b"To: recipient@example.invalid\r\n"
        b"Subject: PANTHEON-UHP-1141\r\n"
        b"Message-ID: <synthetic-1141@example.invalid>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"TRANSIENT_MARKER=EMAIL-1141-EXACT\r\n"
        b"This message is synthetic and contains no professional data.\r\n"
    )
    eml_sha = _sha256_bytes(eml)
    file_question = (
        "Read the supplied synthetic RFC822 message and return exactly the "
        "value after TRANSIENT_MARKER plus the Subject header."
    )
    file_context = {
        "expected_source_sha256": eml_sha,
        "expected_marker": "EMAIL-1141-EXACT",
        "expected_subject": "PANTHEON-UHP-1141",
        "persistence_policy": (
            "ask_only_no_affaires_no_hindsight_no_source"
        ),
    }
    file_basis = _basis(
        "T6-transient-file",
        file_question,
        file_context,
    )
    _write(
        root / "T6-transient-file" / "basis.json",
        json.dumps(file_basis, indent=2) + "\n",
    )
    _write(
        root / "T6-transient-file" / "prompt.txt",
        file_question + "\n",
    )
    _write(
        root / "T6-transient-file" / "synthetic.eml",
        eml,
    )

    artifact_bytes = b"PANTHEON-UHP-ARTIFACT-1141\n"
    artifact_sha = _sha256_bytes(artifact_bytes)
    artifact_question = (
        "Create a file named result-1141.txt containing exactly "
        "PANTHEON-UHP-ARTIFACT-1141 followed by one newline. "
        "Return a short statement after writing it."
    )
    artifact_context = {
        "expected_filename": "result-1141.txt",
        "expected_sha256": artifact_sha,
        "promotion_policy": "candidate_only",
    }
    artifact_basis = _basis(
        "T7-artifact",
        artifact_question,
        artifact_context,
    )
    _write(
        root / "T7-artifact" / "basis.json",
        json.dumps(artifact_basis, indent=2) + "\n",
    )
    _write(
        root / "T7-artifact" / "prompt.txt",
        artifact_question + "\n",
    )
    _write(
        root / "T7-artifact" / "expected-artifact.bin",
        artifact_bytes,
    )

    manifest = {
        "schema": "pantheon/uhp-hermes-transport-fixtures/v1",
        "synthetic": True,
        "task_contract_ref": TASK_CONTRACT_REF,
        "context_pack_ref": CONTEXT_PACK_REF,
        "cases": {
            "T1-core-read-only": {
                "basis_digest": core_basis["execution_basis_digest"],
            },
            "T4-stream-cancel": {
                "basis_digest": stream_basis["execution_basis_digest"],
            },
            "T6-transient-file": {
                "basis_digest": file_basis["execution_basis_digest"],
                "source_sha256": eml_sha,
            },
            "T7-artifact": {
                "basis_digest": artifact_basis["execution_basis_digest"],
                "artifact_sha256": artifact_sha,
            },
        },
        "non_equivalences": [
            "fixture != professional source",
            "fixture digest != Evidence",
            "paired basis != shared admission",
        ],
    }
    _write(
        root / "manifest.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic non-sensitive fixtures "
            "for Pantheon-Next#1141"
        )
    )
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_all(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
