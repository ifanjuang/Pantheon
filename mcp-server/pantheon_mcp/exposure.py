"""Read-only exposure-surface verification.

Where the other verifications ask whether a component is installed, observable or
recoverable, this asks whether its **exposure surface is safe**: how far it is
reachable (local / VPN / public), whether authentication is enforced and whether
access scope is limited. The doctrine is explicit that internal runtimes must not
be reachable publicly without protection, and that a public surface must stay
authenticated and least-privilege. A publicly reachable surface with no auth is
the unsafe extreme this surfaces as a distinct read-only verdict.

It classifies *provided* evidence only: it performs no probe, makes no NAS
access, opens no port, sends nothing and decides nothing. Insufficient evidence
is reported as a capability gap rather than improvised. The gate and the human
decide.

Evidence shape (every field optional; all values are *provided*, never fetched)::

    component: runtime_client
    reach: public              # local | vpn | public
    auth: { enforced: true }
    scope: { limited: true }   # read-only / least-privilege

The component identifier is deliberately client-agnostic. A Hermes Web/dashboard
instance or another compatible replaceable client may be described here without
making that client a Pantheon authority or architecture dependency.
"""

from __future__ import annotations

from .evidence_validation import (
    invalid_evidence_report,
    validate_evidence,
    verdict_report,
)

_SCHEMA_PATH = "schemas/exposure_evidence.schema.yaml"

_READ_ONLY_NOTE = (
    "Classifies provided evidence only; performs no probe, no NAS access, opens "
    "no port, sends nothing, and decides nothing. The gate and the human decide."
)

_CONTAINED = {"local", "vpn"}
_OPEN = {"public"}


def _reach_state(evidence: dict, gaps: list[str]):
    """Return (reach, reach_contained). reach_contained is None when reach is not
    provided, True when local/vpn, False when public."""
    reach = evidence.get("reach")
    if reach in _CONTAINED:
        return reach, True
    if reach in _OPEN:
        return reach, False
    gaps.append("no reach evidence ('reach': local | vpn | public)")
    return None, None


def _flag_state(evidence: dict, key: str, field: str, gaps: list[str], gap_msg: str):
    block = evidence.get(key)
    if isinstance(block, dict) and field in block:
        return block[field]
    gaps.append(gap_msg)
    return None


def verify_exposure(evidence: dict) -> dict:
    """Classify a component's exposure-surface safety from provided evidence and
    return the verdict as data. Read-only: it opens nothing and decides nothing."""
    problems = validate_evidence(evidence, _SCHEMA_PATH)
    if problems:
        return invalid_evidence_report(problems)

    gaps: list[str] = []
    reach, reach_contained = _reach_state(evidence, gaps)
    authenticated = _flag_state(evidence, "auth", "enforced", gaps, "no auth evidence ('auth.enforced')")
    scoped = _flag_state(evidence, "scope", "limited", gaps, "no scope evidence ('scope.limited')")

    if reach_contained is False and authenticated is False:
        verdict = "exposed"
        gaps.append("publicly reachable without authentication")
    elif authenticated and scoped and reach_contained:
        verdict = "guarded"
    elif authenticated is False or scoped is False or reach_contained is False:
        verdict = "degraded"
    else:
        verdict = "unknown"

    return verdict_report(
        evidence,
        axes={
            "reach": reach,
            "reach_contained": reach_contained,
            "authenticated": authenticated,
            "scoped": scoped,
        },
        verdict=verdict,
        gaps=gaps,
        note=_READ_ONLY_NOTE,
    )