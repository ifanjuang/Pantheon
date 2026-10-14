"""The application must not be able to lose its policy chokepoint silently.

These tests cover the Cockpit assembly boundary rather than only the owner module:
a gate that exists but is never supplied to a real write path is not enforcement.
"""

from __future__ import annotations

from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from mvp_vertical import knowledge_update
from mvp_vertical.cockpit_shell import create_cockpit_app
from mvp_vertical.policy_gate import HttpPolicyClient, StandInPolicyClient

APPLY_ROUTE = "/projects/{project}/knowledge/{kid}/updates/apply"
PROJECT = "project-a"
KID = "knowledge.coverage"


class _Connection:
    def transaction(self):
        return nullcontext()

    def close(self):
        return None


def _body() -> dict:
    return {
        "proposed_markdown": "# Updated",
        "expected_version": 2,
        "review_status": "needs_review",
        "base_markdown_digest": "sha256:base",
        "confirmation_token": "a" * 64,
        "confirmation_expires_at": 2_000_000_000,
        "confirmation_phrase": "CONFIRMER UPDATE",
        "idempotency_key": "knowledge-update-0001",
        "task_contract_ref": "task-contract:reviewed-001",
        "evidence_pack_candidate_ref": "evidence-pack-candidate:001",
        "human_decision_ref": "human-decision:001",
    }


def _headers() -> dict:
    return {
        "Authorization": "Bearer edit-key",
        "X-Pantheon-Human-Actor": "ifan.juang",
    }


def _app(**kwargs):
    kwargs.setdefault("connect_fn", _Connection)
    kwargs.setdefault("editor_api_key", "edit-key")
    kwargs.setdefault("update_signing_secret", "server-signing-secret")
    return create_cockpit_app(**kwargs)


def _post(client: TestClient):
    return client.post(
        APPLY_ROUTE.format(project=PROJECT, kid=KID),
        headers=_headers(),
        json=_body(),
    )


def test_enforcement_is_required_unless_a_deployment_says_otherwise(monkeypatch) -> None:
    monkeypatch.delenv("MVP_POLICY_ENFORCEMENT", raising=False)
    assert _app().state.policy_enforcement == "required"


def test_an_unconfigured_decision_point_refuses_the_consequential_write(monkeypatch) -> None:
    monkeypatch.delenv("MVP_POLICY_ENFORCEMENT", raising=False)
    monkeypatch.delenv("MVP_POLICY_API_URL", raising=False)
    monkeypatch.delenv("MVP_POLICY_API_KEY", raising=False)

    response = _post(TestClient(_app()))

    assert response.status_code == 503
    assert "policy decision point is not configured" in response.json()["detail"]


def test_read_only_surface_still_assembles_without_a_decision_point(monkeypatch) -> None:
    monkeypatch.delenv("MVP_POLICY_API_URL", raising=False)
    monkeypatch.delenv("MVP_POLICY_API_KEY", raising=False)
    app = _app(api_key="read-key")

    assert app.state.policy_client is None
    assert any(getattr(route, "path", "") == "/work/issues" for route in app.routes)


def test_a_configured_client_is_handed_to_the_application(monkeypatch) -> None:
    monkeypatch.delenv("MVP_POLICY_ENFORCEMENT", raising=False)
    client = StandInPolicyClient()
    assert _app(policy_client=client).state.policy_client is client


def test_environment_configuration_builds_a_real_http_client(monkeypatch) -> None:
    monkeypatch.setenv("MVP_POLICY_API_URL", "https://policy.internal")
    monkeypatch.setenv("MVP_POLICY_API_KEY", "policy-key")
    assert isinstance(_app().state.policy_client, HttpPolicyClient)


def test_a_partial_environment_does_not_half_configure_a_client(monkeypatch) -> None:
    monkeypatch.setenv("MVP_POLICY_API_URL", "https://policy.internal")
    monkeypatch.delenv("MVP_POLICY_API_KEY", raising=False)

    app = _app()
    assert app.state.policy_client is None
    assert _post(TestClient(app)).status_code == 503


def test_disabling_enforcement_must_be_stated_by_name(monkeypatch) -> None:
    monkeypatch.delenv("MVP_POLICY_API_URL", raising=False)
    monkeypatch.delenv("MVP_POLICY_API_KEY", raising=False)
    observed = {}

    def apply(_conn, **values):
        observed.update(values)
        return {"status": "applied", "knowledge": {"version": 3}}

    monkeypatch.setattr(knowledge_update, "apply_knowledge_update", apply)
    app = _app(policy_enforcement="disabled")

    assert app.state.policy_enforcement == "disabled"
    response = _post(TestClient(app))
    assert response.status_code == 200
    assert observed["policy_client"] is None


def test_an_unknown_enforcement_posture_fails_closed_at_assembly() -> None:
    with pytest.raises(ValueError, match="MVP_POLICY_ENFORCEMENT"):
        _app(policy_enforcement="maybe")


def test_the_environment_can_only_select_a_declared_posture(monkeypatch) -> None:
    monkeypatch.setenv("MVP_POLICY_ENFORCEMENT", "off")
    with pytest.raises(ValueError, match="MVP_POLICY_ENFORCEMENT"):
        _app()


def test_posture_is_read_case_and_whitespace_insensitively(monkeypatch) -> None:
    monkeypatch.setenv("MVP_POLICY_ENFORCEMENT", "  Disabled ")
    assert _app().state.policy_enforcement == "disabled"


def test_the_composed_application_carries_the_same_policy_assembly(monkeypatch) -> None:
    from mvp_vertical.cockpit_composed import create_composed_cockpit_app

    monkeypatch.delenv("MVP_POLICY_ENFORCEMENT", raising=False)
    client = StandInPolicyClient()
    app = create_composed_cockpit_app(
        connect_fn=_Connection,
        initialize_fn=None,
        editor_api_key="edit-key",
        update_signing_secret="server-signing-secret",
        policy_client=client,
    )

    assert app.state.policy_client is client
    assert app.state.policy_enforcement == "required"
