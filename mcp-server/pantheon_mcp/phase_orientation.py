"""Read-only phase orientation: the main subjects of a phase, for a governed reader.

Reads ``registries/architecture_phase_orientation.registry.json``, a French
projection of the agency domain pack phase map (candidate deliverables, minimum
evidence and gate per phase block) with the gate risk of the index effect
matrix. The answer orients; it is not a checklist. It computes no status,
checks no completeness and reports no missing item. A code without a block (an
agency phase, a scope marker) returns ``found: false``, which is not an error.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .repo import read_repo_text

ORIENTATION_PATH = "registries/architecture_phase_orientation.registry.json"


def load_orientation(root: Path | None = None) -> list[dict[str, Any]]:
    registry = json.loads(read_repo_text(ORIENTATION_PATH, root))
    entries = registry.get("entries") if isinstance(registry, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"{ORIENTATION_PATH} has no entries list")
    return entries


def phase_orientation(phase: str, root: Path | None = None) -> dict[str, Any]:
    code = str(phase or "").strip().upper()
    result: dict[str, Any] = {
        "phase": code,
        "found": False,
        "advisory": True,
        "boundary": "orientation only: no status, no completeness check, no required deliverable",
        "source": ORIENTATION_PATH,
    }
    for entry in load_orientation(root):
        if code and code in (entry.get("phases") or []):
            result.update(
                found=True,
                block=entry["id"],
                block_phases=list(entry["phases"]),
                label=entry["label"],
                deliverables=list(entry["deliverables"]),
                minimum_evidence=list(entry["minimum_evidence"]),
                gate=entry["gate"],
                gate_risk=(entry.get("gate_risks") or {}).get(code),
            )
            if entry.get("note"):
                result["note"] = entry["note"]
            break
    return result
