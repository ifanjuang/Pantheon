"""Phase orientation: the main subjects of a phase, read from a governed registry.

``registries/architecture_phase_orientation.registry.json`` is a French
projection of the agency domain pack phase map (candidate deliverables, minimum
evidence and gate per phase block) with the gate risk of the index effect
matrix. It orients a reader on what a phase usually involves.

It is not a checklist. Nothing here computes a status, checks completeness or
reports a missing item: a project does not go through every phase, and a listed
deliverable is not required. A code without a block (an agency phase, a scope
marker such as AGENCY_LIBRARY) has no orientation, which is not an error.
"""

from __future__ import annotations

from typing import Any

from . import pantheon_contracts

REGISTRY = "phase_orientation"


class OrientationUnavailable(ValueError):
    """The orientation registry cannot be read."""


def _entries() -> list[dict[str, Any]]:
    try:
        registry = pantheon_contracts.load_registry(REGISTRY)
    except pantheon_contracts.ContractUnavailable as exc:
        raise OrientationUnavailable(str(exc)) from exc
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise OrientationUnavailable("the phase orientation registry has no entries list")
    return entries


def phase_orientation(phase_code: Any) -> dict[str, Any] | None:
    """Orientation of the block covering ``phase_code``, or None when no block covers it."""
    code = str(phase_code or "").strip()
    if not code:
        return None
    for entry in _entries():
        if code in (entry.get("phases") or []):
            orientation = {
                "phase": code,
                "block": entry["id"],
                "block_phases": list(entry["phases"]),
                "label": entry["label"],
                "deliverables": list(entry["deliverables"]),
                "minimum_evidence": list(entry["minimum_evidence"]),
                "gate": entry["gate"],
                "gate_risk": (entry.get("gate_risks") or {}).get(code),
                "advisory": True,
            }
            if entry.get("note"):
                orientation["note"] = entry["note"]
            return orientation
    return None


def safe_phase_orientation(phase_code: Any) -> dict[str, Any] | None:
    """Like ``phase_orientation`` but None when the registry is unavailable: a read must not fail on it."""
    try:
        return phase_orientation(phase_code)
    except OrientationUnavailable:
        return None
