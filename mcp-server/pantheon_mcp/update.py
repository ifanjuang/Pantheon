"""Read-only update-availability verification.

Where the family asks installed / observable / recoverable / exposed, this asks
whether a component is **current**: given a provided current version and the
latest available version, is an update available. It reports availability as data
— it goes nowhere to fetch the latest version and installs nothing (Pantheon is
not an updater). The comparison is provided-evidence-in, verdict-out.

It classifies *provided* evidence only: it performs no probe, no network fetch,
no NAS access and decides nothing. Insufficient evidence is reported as a
capability gap rather than improvised. The gate and the human decide.
"""

from __future__ import annotations

import re

from .evidence_validation import (
    invalid_evidence_report,
    validate_evidence,
    verdict_report,
)

_SCHEMA_PATH = "schemas/update_evidence.schema.yaml"

_READ_ONLY_NOTE = (
    "Classifies provided evidence only; performs no probe, no network fetch, no "
    "NAS access, no update, and decides nothing. The gate and the human decide."
)


def _parse_version(value):
    """Tolerant version parse for caller-provided version strings."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    text = text.lstrip("vV")
    text = re.split(r"[-+ ]", text, maxsplit=1)[0]
    parts = text.split(".")
    out = []
    saw_number = False
    for part in parts:
        match = re.match(r"\d+", part)
        if match:
            out.append(int(match.group()))
            saw_number = True
        else:
            out.append(0)
    return out if saw_number else None


def _compare_version(a, b):
    """Return -1 / 0 / 1 comparing a to b, or None when either is unparseable."""
    pa, pb = _parse_version(a), _parse_version(b)
    if pa is None or pb is None:
        return None
    n = max(len(pa), len(pb))
    pa = pa + [0] * (n - len(pa))
    pb = pb + [0] * (n - len(pb))
    for x, y in zip(pa, pb):
        if x < y:
            return -1
        if x > y:
            return 1
    return 0


def verify_update(evidence: dict) -> dict:
    """Classify update availability from provided evidence and return data only."""
    problems = validate_evidence(evidence, _SCHEMA_PATH)
    if problems:
        return invalid_evidence_report(problems)

    gaps: list[str] = []
    current = evidence.get("current_version")
    available = evidence.get("available_version")
    if not (isinstance(current, str) and current.strip()):
        gaps.append("no current version evidence ('current_version')")
    elif _parse_version(current) is None:
        gaps.append("current version not comparable ('current_version')")
    if not (isinstance(available, str) and available.strip()):
        gaps.append("no available version evidence ('available_version')")
    elif _parse_version(available) is None:
        gaps.append("available version not comparable ('available_version')")

    comparison = _compare_version(current, available)
    if comparison is None:
        verdict = "unknown"
    elif comparison == 0:
        verdict = "current"
    elif comparison < 0:
        verdict = "update_available"
    else:
        verdict = "ahead"

    return verdict_report(
        evidence,
        axes={
            "current_version": current if isinstance(current, str) else None,
            "available_version": available if isinstance(available, str) else None,
        },
        verdict=verdict,
        gaps=gaps,
        note=_READ_ONLY_NOTE,
    )
