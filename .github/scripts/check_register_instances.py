#!/usr/bin/env python3
"""Validate register_link / impact_review / register_candidate instances.

Read-only governance check. It validates each instance file under
docs/examples/cascade_register/ against its schema, verifies link_ids
referential integrity, applies the cascade rule, then evaluates bounded Register
Candidate history coherence for rejected-value non-resurrection and explicit
supersession.

Schema/link/cascade validation remains owned by the mcp-server doctor. History
coherence reuses the same candidate corpus and existing fields only; neither
check edits, fixes, approves, rejects or supersedes records.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
from pantheon_mcp.doctor import check_register_instances  # noqa: E402
from pantheon_mcp.register_history import check_register_history  # noqa: E402


def _print_violations(result: dict) -> None:
    for item in result.get("violations", []):
        print(f" - {item['file']}: {item['message']}", file=sys.stderr)


def main() -> int:
    result = check_register_instances(ROOT)

    if not result["ok"]:
        print(
            f"Register instance check {result['status']}: {result['message']}",
            file=sys.stderr,
        )
        _print_violations(result)
        for path in result.get("missing_schemas", []):
            print(f" - missing schema: {path}", file=sys.stderr)
        return 1

    history = check_register_history(ROOT)
    if not history["ok"]:
        print(
            f"Register history check {history['status']}: {history['message']}",
            file=sys.stderr,
        )
        _print_violations(history)
        return 1

    checked = result.get("instances_checked", 0)
    history_checked = history.get("candidates_checked", 0)
    print(
        "OK: "
        f"{checked} register instance(s) valid; link_ids resolve; cascade rule satisfied; "
        f"{history_checked} candidate history record(s) preserve rejection/supersession coherence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
