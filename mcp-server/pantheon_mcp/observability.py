"""Read-only observability verification.

Where `verify_install` asks "is the component installed and does it answer",
this asks the prior question: **can we even see it** — are its observability
signals present, is the data fresh, are errors within threshold. A component can
be installed and answering yet effectively blind (no logs, stale metrics), and a
verdict built on absent signals would be a false comfort; this surfaces that as a
distinct read-only verdict the dashboard displays.

It classifies *provided* evidence only: it performs no probe, makes no NAS
access, queries no metrics backend and decides nothing. Insufficient evidence is
reported as a capability gap rather than improvised. The gate and the human
decide.

Evidence shape (every field optional; all values are *provided*, never fetched)::

    component: hermes
    signals:                                  # provided signal inventory
      - { name: logs, present: true }
      - { name: metrics, present: true }
    expected_signals: [logs, metrics]         # which must be present
    freshness: { last_event_age_s: 12, max_age_s: 60 }
    errors: { count: 0, threshold: 5 }
"""

from __future__ import annotations

from .evidence_validation import (
    invalid_evidence_report,
    validate_evidence,
    verdict_report,
)

_SCHEMA_PATH = "schemas/observability_evidence.schema.yaml"

_READ_ONLY_NOTE = (
    "Classifies provided evidence only; performs no probe, no NAS access, no "
    "metrics query, and decides nothing. The gate and the human decide."
)


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _signals_state(evidence: dict, gaps: list[str]):
    """Return (has_any, signals_present). has_any is None when no inventory is
    provided, False when an inventory is provided but nothing is present."""
    signals = evidence.get("signals")
    if not isinstance(signals, list) or not signals:
        gaps.append("no observability signals provided ('signals': [{name, present}])")
        return None, None
    present = sorted({str(s.get("name")) for s in signals if s["present"] is True})
    has_any = bool(present)
    expected = [str(e) for e in (evidence.get("expected_signals") or [])]
    if not expected:
        expected = sorted({str(s.get("name")) for s in signals if isinstance(s, dict)})
    missing = [e for e in expected if e not in present]
    for m in missing:
        gaps.append(f"expected signal '{m}' absent")
    return has_any, (not missing)


def _fresh_state(evidence: dict, gaps: list[str]):
    fr = evidence.get("freshness")
    if isinstance(fr, dict):
        last = _num(fr.get("last_event_age_s"))
        ceiling = _num(fr.get("max_age_s"))
        if last is not None and ceiling is not None:
            fresh = last <= ceiling
            if not fresh:
                gaps.append("data stale (last event older than max age)")
            return fresh
    gaps.append("no freshness evidence ('freshness.last_event_age_s' / 'max_age_s')")
    return None


def _errors_state(evidence: dict, gaps: list[str]):
    er = evidence.get("errors")
    if isinstance(er, dict):
        count = _num(er.get("count"))
        threshold = _num(er.get("threshold"))
        if count is not None and threshold is not None:
            ok = count <= threshold
            if not ok:
                gaps.append("error count over threshold")
            return ok
    gaps.append("no error evidence ('errors.count' / 'errors.threshold')")
    return None


def verify_observability(evidence: dict) -> dict:
    """Classify a component's observability posture from provided evidence and
    return the verdict as data. Read-only: it queries nothing and decides nothing."""
    problems = validate_evidence(evidence, _SCHEMA_PATH)
    if problems:
        return invalid_evidence_report(problems)

    gaps: list[str] = []
    has_any, signals_present = _signals_state(evidence, gaps)
    fresh = _fresh_state(evidence, gaps)
    errors_ok = _errors_state(evidence, gaps)

    if has_any is False:
        verdict = "blind"
    elif signals_present and fresh and errors_ok:
        verdict = "observable"
    elif signals_present is False or fresh is False or errors_ok is False:
        verdict = "degraded"
    else:
        verdict = "unknown"

    return verdict_report(
        evidence,
        axes={
            "has_signal": has_any,
            "signals_present": signals_present,
            "fresh": fresh,
            "errors_ok": errors_ok,
        },
        verdict=verdict,
        gaps=gaps,
        note=_READ_ONLY_NOTE,
    )
