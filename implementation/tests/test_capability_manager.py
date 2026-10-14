"""Tests for the capability management slice (Phase D)."""

import pytest

from mvp_vertical.capability_manager import (
    CapabilityRecord,
    governed_execute,
    plan_action,
)
from mvp_vertical.policy_gate import StandInPolicyClient


def _record(**kw):
    base = dict(capability_id="mcp.pantheon-policy", capability_type="mcp_binding")
    base.update(kw)
    return CapabilityRecord(**base)


def _decision():
    scope = {"scope_type": "workspace", "scope_id": "W-1"}
    return {
        "decision": {"decision_id": "d1", "decided_by": "marie", "scope": scope},
        "expectation": {"required_scope": scope},
    }


def _executor_calls():
    calls = []

    def executor(action, record):
        calls.append(action)
        return {"receipt_id": f"r-{action}", "runtime": "external"}

    return executor, calls


def _external_policy():
    return StandInPolicyClient(external_effect_allowed=True)


def test_plan_rejects_unknown_capability_type():
    plan = plan_action(_record(capability_type="wat"), "install")
    assert plan["legal"] is False
    assert "capability_type" in plan["reason"]


def test_propose_install_is_non_consequential_and_advances_state():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(), "propose_install",
        policy_client=StandInPolicyClient(), executor=executor,
    )
    assert out["status"] == "applied"
    assert out["observation"].installation_status == "proposed"
    assert calls == ["propose_install"]


def test_install_requires_a_human_decision():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(installation_status="proposed"), "install",
        policy_client=StandInPolicyClient(), executor=executor,
        decision_payload=None,
    )
    assert out["status"] == "blocked"
    assert calls == []
    assert out["observation"].installation_status == "proposed"


def test_current_v0_style_external_denial_blocks_install_even_with_decision():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(installation_status="proposed"), "install",
        policy_client=StandInPolicyClient(external_effect_allowed=False), executor=executor,
        decision_payload=_decision(),
    )
    assert out["status"] == "blocked"
    assert out["disposition"] == "blocked_external_effect_not_authorized"
    assert calls == []


def test_replay_required_policy_cannot_bypass_consumer_through_capability_manager():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(installation_status="proposed"),
        "install",
        policy_client=StandInPolicyClient(
            disposition="eligible_with_gate_validated",
            external_effect_allowed=True,
            gate_signal_validation_performed=True,
            replay_guard_required=True,
        ),
        executor=executor,
        decision_payload=_decision(),
    )
    assert out["status"] == "blocked"
    assert out["disposition"] == "blocked_replay_guard_unavailable"
    assert calls == []


def test_install_with_explicit_external_authorization_runs_native_op():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(installation_status="proposed"), "install",
        policy_client=_external_policy(), executor=executor,
        decision_payload=_decision(),
    )
    assert out["status"] == "applied"
    assert calls == ["install"]
    assert out["observation"].installation_status == "installed"
    assert out["receipt"]["receipt_id"] == "r-install"


def test_consequential_action_is_blocked_when_pdp_blocks_and_executor_never_runs():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(installation_status="proposed"), "install",
        policy_client=StandInPolicyClient(
            disposition="blocked_pending_scope", external_effect_allowed=True
        ),
        executor=executor, decision_payload=_decision(),
    )
    assert out["status"] == "blocked"
    assert calls == []
    assert out["observation"].installation_status == "proposed"


def test_illegal_transition_is_refused():
    executor, calls = _executor_calls()
    out = governed_execute(
        _record(installation_status="absent"), "enable",
        policy_client=_external_policy(), executor=executor, decision_payload=_decision(),
    )
    assert out["status"] == "refused"
    assert calls == []


def test_update_requires_update_available():
    executor, _ = _executor_calls()
    legal = governed_execute(
        _record(installation_status="installed", update_status="update_available"),
        "update", policy_client=_external_policy(), executor=executor, decision_payload=_decision(),
    )
    assert legal["status"] == "applied"
    assert legal["observation"].update_status == "up_to_date"

    blocked = plan_action(
        _record(installation_status="installed", update_status="up_to_date"), "update"
    )
    assert blocked["legal"] is False


def test_enable_then_retire_flow_with_explicit_external_authorization():
    executor, calls = _executor_calls()
    rec = _record(installation_status="installed")
    enabled = governed_execute(
        rec, "enable", policy_client=_external_policy(), executor=executor,
        decision_payload=_decision(),
    )
    assert enabled["observation"].enablement_status == "enabled"
    retired = governed_execute(
        enabled["observation"], "retire", policy_client=_external_policy(),
        executor=executor, decision_payload=_decision(),
    )
    assert retired["observation"].installation_status == "absent"
    assert calls == ["enable", "retire"]
