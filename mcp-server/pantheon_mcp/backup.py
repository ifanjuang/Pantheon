"""Read-only backup / recoverability verification.

Where `verify_install` asks "is it installed and answering" and
`verify_observability` asks "can we even see it", this asks the recovery
question: **if it dies, can we get it back** — does a backup exist, is it recent,
and has a restore actually been demonstrated. A backup that exists but is stale,
or has never been restored, is not recoverability; and "we have backups" with no
restore test is the classic false comfort. This is the baseline the bootstrap
chain blocks on before any substrate or runtime.

It classifies *provided* evidence only: it performs no probe, makes no NAS
access, runs no backup or restore and decides nothing. Insufficient evidence is
reported as a capability gap rather than improvised. The gate and the human
decide.

Evidence shape (every field optional; all values are *provided*, never fetched)::

    component: registre-probatoire
    present: true                       # or omit and supply backup_markers
    backup_markers: [".../snapshot-2026-06-22"]
    freshness: { last_backup_age_s: 3600, max_age_s: 86400 }
    restore: { verified: true }
"""

from __future__ import annotations

from .evidence_validation import (
    invalid_evidence_report,
    validate_evidence,
    verdict_report,
)

_SCHEMA_PATH = "schemas/backup_evidence.schema.yaml"

_READ_ONLY_NOTE = (
    "Classifies provided evidence only; performs no probe, no NAS access, no "
    "backup or restore, and decides nothing. The gate and the human decide."
)


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _present_state(evidence: dict, gaps: list[str]):
    if "present" in evidence:
        return evidence["present"]
    if evidence.get("backup_markers"):
        return True
    gaps.append("no backup evidence ('present' or 'backup_markers')")
    return None


def _recent_state(evidence: dict, gaps: list[str]):
    fr = evidence.get("freshness")
    if isinstance(fr, dict):
        last = _num(fr.get("last_backup_age_s"))
        ceiling = _num(fr.get("max_age_s"))
        if last is not None and ceiling is not None:
            recent = last <= ceiling
            if not recent:
                gaps.append("backup stale (last backup older than max age)")
            return recent
    gaps.append("no freshness evidence ('freshness.last_backup_age_s' / 'max_age_s')")
    return None


def _restore_state(evidence: dict, gaps: list[str]):
    restore = evidence.get("restore")
    if isinstance(restore, dict) and "verified" in restore:
        verified = restore["verified"]
        if not verified:
            gaps.append("restore not demonstrated ('restore.verified' is false)")
        return verified
    gaps.append("no restore evidence ('restore.verified')")
    return None


def verify_backup(evidence: dict) -> dict:
    """Classify a component's backup / recoverability posture from provided
    evidence and return the verdict as data. Read-only: it runs nothing and
    decides nothing."""
    problems = validate_evidence(evidence, _SCHEMA_PATH)
    if problems:
        return invalid_evidence_report(problems)

    gaps: list[str] = []
    present = _present_state(evidence, gaps)
    recent = _recent_state(evidence, gaps)
    restore_verified = _restore_state(evidence, gaps)

    if present is False:
        verdict = "unprotected"
    elif present and recent and restore_verified:
        verdict = "protected"
    elif present and (recent is False or restore_verified is False):
        verdict = "degraded"
    else:
        verdict = "unknown"

    return verdict_report(
        evidence,
        axes={
            "present": present,
            "recent": recent,
            "restore_verified": restore_verified,
        },
        verdict=verdict,
        gaps=gaps,
        note=_READ_ONLY_NOTE,
    )
