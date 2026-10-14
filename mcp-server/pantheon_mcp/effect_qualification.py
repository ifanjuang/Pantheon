"""Fixture-only composition for issue Pantheon-Next#664 consequential-path qualification.

This module does not create a general authorization mechanism. It recognizes one
repository-backed synthetic Task Contract / Evidence Pack pair, validates the
already-bound human decision with ``gate_validation``, and reports whether the
PDP may emit the one qualification-only external-effect permission.

Replay consumption is intentionally not implemented here: Pantheon is a
read-only PDP projection and does not own operational effect state. When this
fixture is eligible it requires the operational PEP to consume the decision once
before invoking the synthetic effect.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from . import gate_validation

QUALIFICATION_INTENT = "qualification_external_effect"
TASK_CONTRACT_REF = "tc.qualification.external-effect.v1"
EVIDENCE_PACK_CANDIDATE_REF = "epc.qualification.external-effect.v1"
TASK_CONTRACT_FIXTURE = Path(
    "mcp-server/fixtures/qualification_external_effect.task_contract.yaml"
)
EVIDENCE_PACK_FIXTURE = Path(
    "mcp-server/fixtures/qualification_external_effect.evidence_pack.yaml"
)


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _scope(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    scope_type = value.get("scope_type")
    scope_id = value.get("scope_id")
    if not isinstance(scope_type, str) or not scope_type:
        return None
    if not isinstance(scope_id, str) or not scope_id:
        return None
    return {"scope_type": scope_type, "scope_id": scope_id}


def _load_fixture(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def expected_object_identity(scope: dict[str, str]) -> str:
    return (
        f"qualification-external-effect:{TASK_CONTRACT_REF}:"
        f"{scope['scope_type']}:{scope['scope_id']}"
    )


def expected_effect_digest(scope: dict[str, str]) -> str:
    return _canonical_digest(
        {
            "intent": QUALIFICATION_INTENT,
            "scope": scope,
            "task_contract_ref": TASK_CONTRACT_REF,
            "evidence_pack_candidate_ref": EVIDENCE_PACK_CANDIDATE_REF,
            "writes_state": True,
            "external_effect": True,
        }
    )


def evaluate(
    *,
    root: Path,
    request: dict[str, Any],
    gate_signals: dict[str, Any],
    classification: dict[str, Any],
    decision_validation: Any,
    issuer_keys: dict[str, str] | None,
) -> dict[str, Any] | None:
    """Evaluate only the repository-backed Pantheon-Next#664 qualification fixture.

    ``None`` means this is not the fixture and the normal fail-closed preflight
    remains authoritative. A mapping means the fixture was attempted; it may be
    eligible only when every repository, classification and cryptographic check
    below succeeds.
    """

    if request.get("intent") != QUALIFICATION_INTENT:
        return None

    findings: list[str] = []
    contract = _load_fixture(root / TASK_CONTRACT_FIXTURE)
    evidence = _load_fixture(root / EVIDENCE_PACK_FIXTURE)
    if contract is None:
        findings.append("qualification Task Contract fixture is unavailable")
    if evidence is None:
        findings.append("qualification Evidence Pack fixture is unavailable")

    fixture_scope = _scope((contract or {}).get("scope"))
    request_scope = _scope(request.get("scope"))
    if fixture_scope is None:
        findings.append("qualification Task Contract fixture has no valid scope")
    elif request_scope != fixture_scope:
        findings.append("request scope does not match the qualification Task Contract")

    if (contract or {}).get("contract_id") != TASK_CONTRACT_REF:
        findings.append("qualification Task Contract reference is unavailable or incoherent")
    if (evidence or {}).get("evidence_pack_id") != EVIDENCE_PACK_CANDIDATE_REF:
        findings.append("qualification Evidence Pack reference is unavailable or incoherent")
    if (evidence or {}).get("task_contract_id") != TASK_CONTRACT_REF:
        findings.append("qualification Evidence Pack is not bound to the Task Contract")
    if _scope((evidence or {}).get("scope")) != fixture_scope:
        findings.append("qualification Evidence Pack scope does not match the Task Contract")

    exact_flags = {
        "external_effect": True,
        "writes_state": True,
        "transmission_requested": False,
        "memory_promotion_requested": False,
        "professional_position": False,
        "financial_or_contractual_effect": False,
    }
    for key, expected in exact_flags.items():
        if bool(request.get(key, False)) is not expected:
            findings.append(f"qualification request requires {key}={expected!r}")

    expected_level = (contract or {}).get("approval_level")
    if classification.get("consequence_level") != "K4":
        findings.append("qualification external effect must remain classified K4")
    if classification.get("required_approval_ceiling") != expected_level:
        findings.append("classification ceiling does not match the fixture Task Contract")
    if classification.get("task_contract_required") is not True:
        findings.append("qualification classification must require a Task Contract")
    if classification.get("evidence_required") is not True:
        findings.append("qualification classification must require Evidence")
    if classification.get("blocked_until_gate") is not True:
        findings.append("qualification classification must require a human gate")

    if gate_signals.get("task_contract_ref") != TASK_CONTRACT_REF:
        findings.append("task_contract_ref does not name the repository qualification fixture")
    if gate_signals.get("evidence_pack_candidate_ref") != EVIDENCE_PACK_CANDIDATE_REF:
        findings.append(
            "evidence_pack_candidate_ref does not name the repository qualification fixture"
        )

    validation_performed = False
    validation: dict[str, Any] | None = None
    if not isinstance(decision_validation, dict):
        findings.append("bound decision_validation payload is required")
    else:
        expectation = decision_validation.get("expectation")
        decision = decision_validation.get("decision")
        expectation = expectation if isinstance(expectation, dict) else {}
        decision = decision if isinstance(decision, dict) else {}

        if request_scope is not None:
            expected_identity = expected_object_identity(request_scope)
            expected_digest = expected_effect_digest(request_scope)
            exact_expectation = {
                "required_ceiling": expected_level,
                "required_scope": request_scope,
                "object_identity": expected_identity,
                "expected_digest": expected_digest,
            }
            for key, expected in exact_expectation.items():
                if expectation.get(key) != expected:
                    findings.append(f"decision expectation {key} is not fixture-derived")

        if decision.get("decision_id") != gate_signals.get("human_decision_ref"):
            findings.append("human_decision_ref does not match the bound decision_id")
        if decision.get("approval_level") != gate_signals.get("human_decision_level"):
            findings.append("human_decision_level does not match the bound decision")

        validation = gate_validation.validate_decision(
            decision_validation,
            issuer_keys=issuer_keys,
        )
        validation_performed = True
        if validation.get("verdict") != "valid":
            findings.extend(validation.get("findings", []))
        strict_checks = (
            "structural",
            "signer",
            "expiry",
            "scope",
            "level",
            "object_identity",
            "digest",
            "issuer",
        )
        checks = validation.get("checks") or {}
        for key in strict_checks:
            if checks.get(key) != "ok":
                findings.append(f"strict qualification gate requires {key}=ok")
        if validation.get("issuer_authenticated") is not True:
            findings.append("strict qualification gate requires an authenticated human issuer")

    allowed = not findings
    return {
        "fixture_id": "external-effect-v1",
        "external_effect_allowed": allowed,
        "gate_signal_validation_performed": validation_performed,
        "replay_guard_required": allowed,
        "findings": findings,
        "gate_validation": validation,
        "limits": [
            "This is a synthetic qualification fixture, not a production capability.",
            "PDP validation does not consume the decision; the operational PEP must do so once.",
            "Runtime success is not Pantheon Evidence, truth or professional approval.",
        ],
    }
