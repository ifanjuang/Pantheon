#!/usr/bin/env python3
"""Validate the architecture_devis_reprise governed vertical slice.

Read-only governance check. It validates each instance under
docs/examples/vertical_devis_reprise/ against its spine schema and checks the
end-to-end coherence invariants (evidence log scoped to a project; a required
evidence gate carries V and E; the answer status references the dossier evidence
pack and register candidate).

The whole check is imported from the mcp-server doctor so there is a single
source of truth. The script never edits, fixes or decides.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
from pantheon_mcp.doctor import check_vertical_slice  # noqa: E402


def main() -> int:
    result = check_vertical_slice(ROOT)
    violations = result.get("violations", [])
    if not result["ok"]:
        print(
            f"Vertical slice check {result['status']}: {result['message']}",
            file=sys.stderr,
        )
        for item in violations:
            print(f" - {item['file']}: {item['message']}", file=sys.stderr)
        for path in result.get("missing_schemas", []):
            print(f" - missing schema: {path}", file=sys.stderr)
        return 1
    checked = result.get("instances_checked", 0)
    print(f"OK: {checked} vertical-slice instance(s) valid; project-scoped; gate V/E present; references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
