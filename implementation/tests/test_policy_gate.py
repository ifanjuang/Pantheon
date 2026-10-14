"""Tests for the policy chokepoint seam (Phase C)."""

from mvp_vertical.policy_gate import (
    GateVerdict,
    StandInPolicyClient,
    enforce_consequential,
    governed_effect,
)


def _decision_payload(decided_by="marie.dupont", scope=None):
    scope = scope or {"scope_type": "project", "scope_id": "P-42"}
    return {
        "decision": {"decision_id": "d1", "decided_by": decided_by, "scope": scope},
        "expectation": {"required_scope": {"scope_type": "project", "scope_id": "P-42"}},
    }


class _RaisingClient:
    def preflight(self, candidate):
        raise ConnectionError("PDP down")

    def validate_decision(self, payload):  # pragma: no cover - never reached
        raise AssertionError("must not be called after preflight failure")


def test_external_effect_needs_explicit_pdp_effect_authorization():
    ran = []
    out = governed_effect(
        StandInPolicyClient(external_effect_allowed=False),
        candidate={"effect_kind": "external_write"},
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("written"),
    )
    assert out["status"] == "blocked"
    assert out["disposition"] == "blocked_external_effect_not_authorized"
    assert out["effect_ran"] is False
    assert ran == []


def test_explicit_external_authorization_and_valid_decision_allow_the_effect():
    client = StandInPolicyClient(external_effect_allowed=True)
    ran = []
    out = governed_effect(
        client,
        candidate={"effect_kind": "external_write"},
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("written") or "ok",
    )
    assert out["status"] == "applied"
    assert out["effect_ran"] is True
    assert out["result"] == "ok"
    assert ran == ["written"]


def test_candidate_internal_write_can_continue_without_external_effect_flag():
    ran = []
    out = governed_effect(
        StandInPolicyClient(),
        candidate={
            "request": {
                "intent": "project_document_candidate",
                "external_effect": False,
                "writes_state": True,
                "scope": {"scope_type": "project", "scope_id": "P-42"},
            }
        },
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("candidate") or "ok",
    )
    assert out["status"] == "applied"
    assert ran == ["candidate"]


def test_non_eligible_preflight_blocks_and_effect_never_runs():
    client = StandInPolicyClient(
        disposition="blocked_pending_human_decision", external_effect_allowed=True
    )
    ran = []
    out = governed_effect(
        client,
        candidate={},
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("written"),
    )
    assert out["status"] == "blocked"
    assert out["effect_ran"] is False
    assert ran == []
    assert "blocked_pending_human_decision" in out["disposition"]


def test_invalid_decision_blocks_even_when_preflight_and_external_effect_are_eligible():
    client = StandInPolicyClient(external_effect_allowed=True)
    ran = []
    out = governed_effect(
        client,
        candidate={},
        decision_payload=_decision_payload(decided_by="hermes"),
        effect=lambda: ran.append("written"),
    )
    assert out["status"] == "blocked"
    assert out["effect_ran"] is False
    assert ran == []
    assert any("non-human" in r for r in out["reasons"])


def test_scope_mismatch_blocks():
    client = StandInPolicyClient(external_effect_allowed=True)
    out = governed_effect(
        client,
        candidate={},
        decision_payload=_decision_payload(scope={"scope_type": "project", "scope_id": "OTHER"}),
        effect=lambda: "written",
    )
    assert out["status"] == "blocked"
    assert any("scope" in r for r in out["reasons"])


def test_memory_promotion_needs_explicit_canonical_authorization():
    ran = []
    out = governed_effect(
        StandInPolicyClient(),
        candidate={
            "request": {
                "intent": "memory_promotion",
                "external_effect": False,
                "writes_state": True,
                "memory_promotion_requested": True,
                "scope": {"scope_type": "project", "scope_id": "P-42"},
            }
        },
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("promoted"),
    )
    assert out["status"] == "blocked"
    assert out["disposition"] == "blocked_canonical_effect_not_authorized"
    assert ran == []


def test_pdp_unavailable_fails_closed():
    ran = []
    out = governed_effect(
        _RaisingClient(),
        candidate={},
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("written"),
    )
    assert out["status"] == "blocked"
    assert out["disposition"] == "policy_unavailable"
    assert out["effect_ran"] is False
    assert ran == []


def test_enforce_consequential_returns_a_verdict():
    verdict = enforce_consequential(
        StandInPolicyClient(external_effect_allowed=True),
        candidate={},
        decision_payload=_decision_payload(),
    )
    assert isinstance(verdict, GateVerdict)
    assert verdict.allowed is True
