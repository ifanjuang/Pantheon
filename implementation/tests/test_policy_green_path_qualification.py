from __future__ import annotations

from mvp_vertical.policy_gate import (
    StandInPolicyClient,
    enforce_consequential,
    governed_effect,
)


SCOPE = {"scope_type": "project", "scope_id": "qualification-sandbox"}
TASK_CONTRACT_REF = "tc.qualification.external-effect.v1"
EVIDENCE_REF = "epc.qualification.external-effect.v1"
OBJECT_IDENTITY = (
    "qualification-external-effect:"
    "tc.qualification.external-effect.v1:project:qualification-sandbox"
)
EFFECT_DIGEST = "sha256:8f3b6c453aa7645e3d2f00c3c048fce98e18788c7a187905224e692052bbac85"


def _candidate() -> dict:
    return {
        "request": {
            "intent": "qualification_external_effect",
            "external_effect": True,
            "writes_state": True,
            "transmission_requested": False,
            "memory_promotion_requested": False,
            "professional_position": False,
            "financial_or_contractual_effect": False,
            "scope": SCOPE,
        },
        "gate_signals": {
            "task_contract_ref": TASK_CONTRACT_REF,
            "evidence_pack_candidate_ref": EVIDENCE_REF,
        },
        "decision_expectation": {
            "required_ceiling": "C3",
            "required_scope": SCOPE,
            "object_identity": OBJECT_IDENTITY,
            "expected_digest": EFFECT_DIGEST,
        },
    }


def _decision() -> dict:
    return {
        "decision": {
            "decision_id": "decision-qualification-001",
            "decided_by": "marie.dupont",
            "expires_at": "2099-01-01T00:00:00Z",
            "approval_level": "C3",
            "scope": SCOPE,
            "object_identity": OBJECT_IDENTITY,
            "content_digest": EFFECT_DIGEST,
            "signature": "signature-validated-by-pdp",
        },
        "expectation": {
            "required_ceiling": "C0",
            "required_scope": {"scope_type": "project", "scope_id": "ATTACKER"},
            "object_identity": "caller-controlled",
            "expected_digest": "sha256:caller-controlled",
        },
    }


def _qualification_policy(*, external_effect_allowed: bool = True, gate_validated: bool = True):
    return StandInPolicyClient(
        disposition="eligible_with_gate_validated",
        external_effect_allowed=external_effect_allowed,
        canonical_effect_allowed=False,
        gate_signal_validation_performed=gate_validated,
        replay_guard_required=True,
    )


def test_replay_required_direct_verdict_cannot_allow_without_consumer():
    verdict = enforce_consequential(
        _qualification_policy(),
        candidate=_candidate(),
        decision_payload=_decision(),
    )

    assert verdict.allowed is False
    assert verdict.disposition == "blocked_replay_guard_unavailable"
    assert verdict.decision_id == "decision-qualification-001"


def test_one_signed_decision_runs_exactly_one_bounded_effect():
    policy = _qualification_policy()
    consumed: set[str] = set()
    effects: list[str] = []

    def consume(decision_id: str) -> bool:
        if decision_id in consumed:
            return False
        consumed.add(decision_id)
        return True

    first = governed_effect(
        policy,
        candidate=_candidate(),
        decision_payload=_decision(),
        consume_decision=consume,
        effect=lambda: effects.append("ran") or {"synthetic": True},
    )
    second = governed_effect(
        policy,
        candidate=_candidate(),
        decision_payload=_decision(),
        consume_decision=consume,
        effect=lambda: effects.append("replayed") or {"synthetic": True},
    )

    assert first["status"] == "applied"
    assert first["effect_ran"] is True
    assert first["qualification_trace"] == {
        "decision_consumed_once": True,
        "decision_id": "decision-qualification-001",
        "runtime_success_is_evidence": False,
        "effect_execution_is_approval": False,
    }
    assert second["status"] == "blocked"
    assert second["disposition"] == "blocked_replayed_decision"
    assert second["effect_ran"] is False
    assert effects == ["ran"]
    assert policy.last_preflight["decision_validation"]["expectation"] == _candidate()[
        "decision_expectation"
    ]


def test_pdp_denial_wins_before_decision_consumption():
    policy = _qualification_policy(external_effect_allowed=False)
    consumed: list[str] = []
    effects: list[str] = []

    result = governed_effect(
        policy,
        candidate=_candidate(),
        decision_payload=_decision(),
        consume_decision=lambda decision_id: consumed.append(decision_id) or True,
        effect=lambda: effects.append("must-not-run"),
    )

    assert result["status"] == "blocked"
    assert result["disposition"] == "blocked_external_effect_not_authorized"
    assert consumed == []
    assert effects == []


def test_replay_required_without_validated_gate_fails_closed():
    policy = _qualification_policy(gate_validated=False)
    consumed: list[str] = []

    result = governed_effect(
        policy,
        candidate=_candidate(),
        decision_payload=_decision(),
        consume_decision=lambda decision_id: consumed.append(decision_id) or True,
        effect=lambda: "must-not-run",
    )

    assert result["status"] == "blocked"
    assert result["disposition"] == "blocked_unvalidated_gate_signal"
    assert consumed == []


def test_replay_guard_is_mandatory_for_the_qualified_external_effect():
    result = governed_effect(
        _qualification_policy(),
        candidate=_candidate(),
        decision_payload=_decision(),
        effect=lambda: "must-not-run",
    )

    assert result["status"] == "blocked"
    assert result["disposition"] == "blocked_replay_guard_unavailable"
    assert result["effect_ran"] is False
