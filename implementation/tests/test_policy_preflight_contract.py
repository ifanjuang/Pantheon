from __future__ import annotations

import json

import httpx

from mvp_vertical.policy_gate import HttpPolicyClient, StandInPolicyClient, governed_effect
from mvp_vertical.policy_request import bind_decision_payload, build_preflight_payload


def _decision_payload():
    scope = {"scope_type": "project", "scope_id": "P-42"}
    return {
        "decision": {
            "decision_id": "decision-42",
            "decided_by": "marie.dupont",
            "expires_at": "2026-07-24T12:00:00Z",
            "approval_level": "C1",
            "scope": scope,
            "object_identity": "paperless:42:7",
            "content_digest": "sha256:abc",
        },
        "expectation": {
            "required_ceiling": "C1",
            "required_scope": scope,
            "object_identity": "paperless:42:7",
            "expected_digest": "sha256:abc",
        },
    }


def test_flat_runtime_candidate_is_translated_to_policy_http_contract():
    payload = build_preflight_payload(
        {
            "effect_kind": "external_document_metadata_update",
            "resource": "paperless_ngx",
            "document_id": 42,
            "changed_fields": ["tags"],
        },
        _decision_payload(),
    )
    assert set(payload) == {"request", "gate_signals"}
    assert payload["request"] == {
        "intent": "external_document_metadata_update",
        "external_effect": True,
        "writes_state": True,
        "delegated_execution": True,
        "transmission_requested": False,
        "memory_promotion_requested": False,
        "professional_position": False,
        "financial_or_contractual_effect": False,
        "scope": {"scope_type": "project", "scope_id": "P-42"},
    }
    assert payload["gate_signals"] == {
        "human_decision_ref": "decision-42",
        "human_decision_level": "C1",
    }
    assert "effect_kind" not in payload
    assert "document_id" not in payload


def test_explicit_task_contract_signal_is_preserved():
    payload = build_preflight_payload(
        {
            "request": {
                "intent": "project_document_intake",
                "external_effect": False,
                "writes_state": True,
                "scope": {"scope_type": "project", "scope_id": "P-42"},
            },
            "gate_signals": {"task_contract_ref": "tc.project-42"},
        },
        _decision_payload(),
    )
    assert payload["request"]["external_effect"] is False
    assert payload["request"]["delegated_execution"] is True
    assert payload["gate_signals"] == {
        "task_contract_ref": "tc.project-42",
        "human_decision_ref": "decision-42",
        "human_decision_level": "C1",
    }


def test_reviewed_direct_human_intent_is_not_mislabeled_as_delegated_work():
    payload = build_preflight_payload(
        {
            "request": {
                "intent": "act_working_information",
                "external_effect": False,
                "writes_state": True,
                "scope": {"scope_type": "project", "scope_id": "P-42"},
            }
        },
        _decision_payload(),
    )
    assert payload["request"]["delegated_execution"] is False
    assert payload["gate_signals"] == {
        "human_decision_ref": "decision-42",
        "human_decision_level": "C1",
    }


def test_unknown_runtime_candidate_cannot_self_exempt_from_task_contract_boundary():
    payload = build_preflight_payload(
        {
            "request": {
                "intent": "custom_local_state_write",
                "external_effect": False,
                "writes_state": True,
                "delegated_execution": False,
                "scope": {"scope_type": "project", "scope_id": "P-42"},
            }
        },
        _decision_payload(),
    )
    assert payload["request"]["delegated_execution"] is True


def test_runtime_expectation_overrides_caller_supplied_expectation():
    caller = _decision_payload()
    caller["expectation"] = {
        "required_ceiling": "C0",
        "required_scope": {"scope_type": "project", "scope_id": "ATTACKER"},
        "object_identity": "fake-object",
        "expected_digest": "sha256:fake",
    }
    candidate = {
        "decision_expectation": {
            "required_ceiling": "C1",
            "required_scope": {"scope_type": "project", "scope_id": "P-42"},
            "object_identity": "paperless:42:7",
            "expected_digest": "sha256:abc",
        }
    }
    bound = bind_decision_payload(candidate, caller)
    assert bound["expectation"] == candidate["decision_expectation"]
    assert bound["decision"] == caller["decision"]


def test_forged_matching_caller_expectation_cannot_authorize_wrong_effect():
    caller = _decision_payload()
    caller["decision"]["object_identity"] = "fake-object"
    caller["decision"]["content_digest"] = "sha256:fake"
    caller["expectation"] = {
        "required_ceiling": "C1",
        "required_scope": {"scope_type": "project", "scope_id": "P-42"},
        "object_identity": "fake-object",
        "expected_digest": "sha256:fake",
    }
    candidate = {
        "request": {
            "intent": "project_document_intake",
            "external_effect": False,
            "writes_state": True,
            "scope": {"scope_type": "project", "scope_id": "P-42"},
        },
        "decision_expectation": {
            "required_ceiling": "C1",
            "required_scope": {"scope_type": "project", "scope_id": "P-42"},
            "object_identity": "paperless:42:7",
            "expected_digest": "sha256:abc",
        },
    }
    ran = []
    result = governed_effect(
        StandInPolicyClient(),
        candidate=candidate,
        decision_payload=caller,
        effect=lambda: ran.append("should-not-run"),
    )
    assert result["status"] == "blocked"
    assert result["effect_ran"] is False
    assert ran == []
    assert any(
        "object_identity" in reason or "content_digest" in reason
        for reason in result["reasons"]
    )


def test_http_policy_client_receives_only_contract_fields_and_bound_decision():
    observed = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        observed.append((request.url.path, body, request.headers.get("authorization")))
        if request.url.path.endswith("preflights:evaluate"):
            assert set(body) == {"request", "gate_signals"}
            return httpx.Response(
                200,
                json={
                    "policy_disposition": "eligible_with_gate_signals_unverified",
                    "missing_requirements": [],
                    "external_effect_allowed": True,
                    "canonical_effect_allowed": False,
                },
            )
        if request.url.path.endswith("decisions:validate"):
            assert body["expectation"] == {
                "required_ceiling": "C1",
                "required_scope": {"scope_type": "project", "scope_id": "P-42"},
                "object_identity": "paperless:42:7",
                "expected_digest": "sha256:abc",
            }
            return httpx.Response(200, json={"verdict": "valid", "findings": []})
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    policy = HttpPolicyClient("http://pantheon-policy-api:8000", "policy-key", client=http)
    ran = []
    result = governed_effect(
        policy,
        candidate={
            "effect_kind": "external_document_metadata_update",
            "resource": "paperless_ngx",
            "decision_expectation": {
                "required_ceiling": "C1",
                "required_scope": {"scope_type": "project", "scope_id": "P-42"},
                "object_identity": "paperless:42:7",
                "expected_digest": "sha256:abc",
            },
        },
        decision_payload=_decision_payload(),
        effect=lambda: ran.append("applied") or {"ok": True},
    )
    assert result["status"] == "applied"
    assert result["effect_ran"] is True
    assert ran == ["applied"]
    assert observed[0][0] == "/policy/preflights:evaluate"
    assert observed[0][2] == "Bearer policy-key"
    assert observed[1][0] == "/policy/decisions:validate"
