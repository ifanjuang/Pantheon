"""Read-only install / liveness verification.

Given evidence already gathered about a component install — a log excerpt, a
health probe result and check results — this classifies the install state and
returns the verdict as data: is it installed, does it answer, are its checks
green. It performs **no probe**, makes **no NAS access**, installs nothing and
decides nothing. The gate and the human decide.

This is the read-only verification brain the dashboard surface displays: the
dashboard "verifies installs from their logs and liveness", and this turns the
provided evidence into a structured verdict. When evidence is insufficient it
reports a capability gap rather than improvising a conclusion.

Evidence shape (every field optional; all values are *provided*, never fetched)::

    component: langfuse-hermes
    installed: true                 # or omit and supply the markers below
    installed_markers: [".../VERSION"]      # presence taken as installed
    install_success_markers: ["bootstrap complete"]   # matched in logs
    logs: "...log excerpt..."
    health: { reachable: true, status_code: 200, latency_ms: 42 }
    checks:
      - { name: health, status: green }
      - { name: ready, status: green }
    expected_checks: [health, ready]        # must all be present and green
"""

from __future__ import annotations

from .evidence_validation import (
    invalid_evidence_report,
    validate_evidence,
    verdict_report,
)

_SCHEMA_PATH = "schemas/install_verification_evidence.schema.yaml"

_READ_ONLY_NOTE = (
    "Classifies provided evidence only; performs no probe, no NAS access, no "
    "install, and decides nothing. The gate and the human decide."
)


def _installed_state(evidence: dict, gaps: list[str]):
    if "installed" in evidence:
        return evidence["installed"]
    if evidence.get("installed_markers"):
        return True
    markers = evidence.get("install_success_markers") or []
    logs = evidence.get("logs")
    if markers and isinstance(logs, str):
        return any(str(m) in logs for m in markers)
    gaps.append(
        "no installation evidence ('installed', 'installed_markers', or "
        "'install_success_markers' + 'logs')"
    )
    return None


def _answers_state(evidence: dict, gaps: list[str]):
    health = evidence.get("health")
    if not isinstance(health, dict):
        gaps.append("no health probe provided ('health.reachable' / 'health.status_code')")
        return None
    if "reachable" not in health:
        gaps.append("health reachability missing ('health.reachable')")
        return None
    reachable = health["reachable"]
    code = health.get("status_code")
    if code is None:
        return reachable
    code_ok = isinstance(code, int) and 200 <= code < 300
    return reachable and code_ok


def _checks_state(evidence: dict, gaps: list[str]):
    checks = evidence.get("checks")
    if not isinstance(checks, list) or not checks:
        gaps.append("no check results provided ('checks': [{name, status}])")
        return None
    statuses = {
        str(c.get("name")): str(c.get("status", "unknown"))
        for c in checks
        if isinstance(c, dict)
    }
    not_green = sorted(n for n, s in statuses.items() if s != "green")
    expected = [str(e) for e in (evidence.get("expected_checks") or [])]
    missing = [e for e in expected if e not in statuses]
    for n in not_green:
        gaps.append(f"check '{n}' not green (status: {statuses[n]})")
    for m in missing:
        gaps.append(f"expected check '{m}' absent")
    return (not not_green) and (not missing)


def verify_install(evidence: dict) -> dict:
    """Classify a component install from provided evidence and return the
    verdict as data. Read-only: it probes nothing and decides nothing."""
    problems = validate_evidence(evidence, _SCHEMA_PATH)
    if problems:
        return invalid_evidence_report(problems)

    gaps: list[str] = []
    installed = _installed_state(evidence, gaps)
    answers = _answers_state(evidence, gaps)
    checks_green = _checks_state(evidence, gaps)

    if installed is False:
        verdict = "absent"
    elif installed and answers and checks_green:
        verdict = "green"
    elif installed and (answers is False or checks_green is False):
        verdict = "degraded"
    else:
        verdict = "unknown"

    return verdict_report(
        evidence,
        axes={
            "installed": installed,
            "answers": answers,
            "checks_green": checks_green,
        },
        verdict=verdict,
        gaps=gaps,
        note=_READ_ONLY_NOTE,
    )
