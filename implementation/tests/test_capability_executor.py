"""Tests for the governed external capability-operation transport seam."""

import httpx
import pytest

from mvp_vertical.capability_manager import (
    CapabilityRecord,
    HermesCapabilityExecutor,
    governed_execute,
)
from mvp_vertical.policy_gate import StandInPolicyClient

BASE = "http://hermes:8642"
VERIFIED_TEST_PATH = "/test/native-capability-operation"


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


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_executor_requires_an_explicit_verified_native_operation_path():
    with pytest.raises(ValueError, match="explicitly verified native capability endpoint"):
        HermesCapabilityExecutor(BASE, "hermes-key")


def test_executor_posts_one_bounded_operation_to_explicit_path_and_returns_receipt():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"receipt_id": "rcpt-1", "status": "done"})

    executor = HermesCapabilityExecutor(
        BASE,
        "hermes-key",
        operations_path=VERIFIED_TEST_PATH,
        client=_client(handler),
    )
    receipt = executor("install", _record(installation_status="proposed"))
    assert receipt["receipt_id"] == "rcpt-1"
    assert receipt["runtime"] == "hermes"
    assert seen["path"] == VERIFIED_TEST_PATH
    assert seen["auth"] == "Bearer hermes-key"
    assert seen["body"]["action"] == "install"
    assert seen["body"]["capability_id"] == "mcp.pantheon-policy"


def test_governed_execute_runs_explicit_transport_only_behind_allow():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"receipt_id": "rcpt-install"})

    executor = HermesCapabilityExecutor(
        BASE,
        "k",
        operations_path=VERIFIED_TEST_PATH,
        client=_client(handler),
    )
    out = governed_execute(
        _record(installation_status="proposed"),
        "install",
        policy_client=StandInPolicyClient(),
        executor=executor,
        decision_payload=_decision(),
    )
    assert out["status"] == "applied"
    assert out["receipt"]["receipt_id"] == "rcpt-install"
    assert out["observation"].installation_status == "installed"
    assert calls["n"] == 1


def test_blocked_policy_never_calls_explicit_transport():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        calls["n"] += 1
        return httpx.Response(200, json={"receipt_id": "should-not-happen"})

    executor = HermesCapabilityExecutor(
        BASE,
        "k",
        operations_path=VERIFIED_TEST_PATH,
        client=_client(handler),
    )
    out = governed_execute(
        _record(installation_status="proposed"),
        "install",
        policy_client=StandInPolicyClient(disposition="blocked_pending_human_decision"),
        executor=executor,
        decision_payload=_decision(),
    )
    assert out["status"] == "blocked"
    assert calls["n"] == 0
