"""Tests for the real HTTP PolicyClient against a mock transport (no network)."""

import httpx
import pytest

from mvp_vertical.policy_gate import HttpPolicyClient, enforce_consequential

BASE = "http://pantheon-policy-api:8000"


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def _decision_payload():
    scope = {"scope_type": "project", "scope_id": "P-42"}
    return {
        "decision": {"decision_id": "d1", "decided_by": "marie", "scope": scope},
        "expectation": {"required_scope": scope},
    }


def test_preflight_posts_to_the_pdp_with_bearer_and_returns_json():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"policy_disposition": "eligible_for_candidate_work"})

    client = HttpPolicyClient(BASE, "secret-key", client=_client(handler))
    out = client.preflight({"request": {"intent": "publish"}})
    assert out["policy_disposition"] == "eligible_for_candidate_work"
    assert seen["url"] == BASE + "/policy/preflights:evaluate"
    assert seen["auth"] == "Bearer secret-key"


def test_validate_decision_posts_to_the_decisions_route():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/policy/decisions:validate"
        return httpx.Response(200, json={"verdict": "valid", "findings": []})

    client = HttpPolicyClient(BASE, "k", client=_client(handler))
    assert client.validate_decision(_decision_payload())["verdict"] == "valid"


def test_enforce_consequential_allows_with_a_live_http_pdp_only_when_effect_is_authorized():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("preflights:evaluate"):
            return httpx.Response(
                200,
                json={
                    "policy_disposition": "eligible_for_candidate_work",
                    "external_effect_allowed": True,
                    "canonical_effect_allowed": False,
                },
            )
        return httpx.Response(200, json={"verdict": "valid", "findings": []})

    client = HttpPolicyClient(BASE, "k", client=_client(handler))
    verdict = enforce_consequential(client, candidate={}, decision_payload=_decision_payload())
    assert verdict.allowed is True


def test_live_http_pdp_v0_style_external_denial_blocks_even_with_valid_decision():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("preflights:evaluate"):
            return httpx.Response(
                200,
                json={
                    "policy_disposition": "eligible_for_candidate_work",
                    "external_effect_allowed": False,
                    "canonical_effect_allowed": False,
                },
            )
        return httpx.Response(200, json={"verdict": "valid", "findings": []})

    client = HttpPolicyClient(BASE, "k", client=_client(handler))
    verdict = enforce_consequential(client, candidate={}, decision_payload=_decision_payload())
    assert verdict.allowed is False
    assert verdict.disposition == "blocked_external_effect_not_authorized"


def test_http_error_from_pdp_fails_closed():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    client = HttpPolicyClient(BASE, "k", client=_client(handler))
    verdict = enforce_consequential(client, candidate={}, decision_payload=_decision_payload())
    assert verdict.allowed is False
    assert verdict.disposition == "policy_unavailable"


def test_transport_error_fails_closed():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to PDP")

    client = HttpPolicyClient(BASE, "k", client=_client(handler))
    verdict = enforce_consequential(client, candidate={}, decision_payload=_decision_payload())
    assert verdict.allowed is False
    assert verdict.disposition == "policy_unavailable"
