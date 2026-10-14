"""Cockpit API boundaries for the first owner-specific Knowledge UPDATE."""

from __future__ import annotations

from contextlib import nullcontext

from fastapi.testclient import TestClient

from mvp_vertical import knowledge_update
from mvp_vertical.cockpit_shell import create_cockpit_app
from mvp_vertical.policy_gate import StandInPolicyClient


class _Connection:
    def transaction(self):
        return nullcontext()

    def close(self) -> None:
        pass


GATE_REFS = {
    "task_contract_ref": "task-contract:reviewed-001",
    "evidence_pack_candidate_ref": "evidence-pack-candidate:001",
    "human_decision_ref": "human-decision:001",
}


def test_update_preview_requires_editor_key_signing_authority_and_declared_human(monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_update,
        "preview_knowledge_update",
        lambda _conn, **values: {
            "status": "confirmation_required",
            "actor": values["actor"],
            "signing_secret": values["signing_secret"],
        },
    )
    path = "/projects/project-a/knowledge/knowledge.coverage/updates/preview"
    body = {"proposed_markdown": "# Updated", "expected_version": 2}

    unsigned = TestClient(
        create_cockpit_app(connect_fn=_Connection, editor_api_key="edit-key")
    )
    assert unsigned.post(
        path,
        json=body,
        headers={
            "Authorization": "Bearer edit-key",
            "X-Pantheon-Human-Actor": "ifan.juang",
        },
    ).status_code == 503

    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            editor_api_key="edit-key",
            update_signing_secret="server-signing-secret",
        )
    )
    assert client.post(path, json=body).status_code == 401
    assert client.post(
        path,
        json=body,
        headers={"Authorization": "Bearer read-key", "X-Pantheon-Human-Actor": "ifan"},
    ).status_code == 401
    assert client.post(
        path,
        json=body,
        headers={"Authorization": "Bearer edit-key"},
    ).status_code == 422
    response = client.post(
        path,
        json=body,
        headers={
            "Authorization": "Bearer edit-key",
            "X-Pantheon-Human-Actor": "ifan.juang",
        },
    )
    assert response.status_code == 200
    assert response.json()["actor"] == "ifan.juang"
    assert response.json()["signing_secret"] == "server-signing-secret"

    assert client.post(
        "/v1/projects/project-a/knowledge/knowledge.coverage/updates/preview",
        json=body,
        headers={
            "Authorization": "Bearer edit-key",
            "X-Pantheon-Human-Actor": "ifan.juang",
        },
    ).status_code == 404


def test_update_apply_passes_exact_effect_and_policy_gate_references(monkeypatch) -> None:
    observed = {}

    def apply(_conn, **values):
        observed.update(values)
        return {"status": "applied", "knowledge": {"version": 3}}

    monkeypatch.setattr(knowledge_update, "apply_knowledge_update", apply)
    policy_client = StandInPolicyClient()
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            editor_api_key="edit-key",
            update_signing_secret="server-signing-secret",
            policy_client=policy_client,
        )
    )
    response = client.post(
        "/projects/project-a/knowledge/knowledge.coverage/updates/apply",
        headers={
            "Authorization": "Bearer edit-key",
            "X-Pantheon-Human-Actor": "ifan.juang",
        },
        json={
            "proposed_markdown": "# Updated",
            "expected_version": 2,
            "review_status": "needs_review",
            "base_markdown_digest": "sha256:base",
            "confirmation_token": "a" * 64,
            "confirmation_expires_at": 2_000_000_000,
            "confirmation_phrase": "CONFIRMER UPDATE",
            "idempotency_key": "knowledge-update-0001",
            **GATE_REFS,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "applied"
    assert observed == {
        "parent_project_id": "project-a",
        "knowledge_id": "knowledge.coverage",
        "actor": "ifan.juang",
        "signing_secret": "server-signing-secret",
        "policy_client": policy_client,
        "proposed_markdown": "# Updated",
        "expected_version": 2,
        "review_status": "needs_review",
        "base_markdown_digest": "sha256:base",
        "confirmation_token": "a" * 64,
        "confirmation_expires_at": 2_000_000_000,
        "confirmation_phrase": "CONFIRMER UPDATE",
        "idempotency_key": "knowledge-update-0001",
        **GATE_REFS,
    }


def test_policy_unavailable_maps_to_service_unavailable(monkeypatch) -> None:
    def unavailable(_conn, **_values):
        raise knowledge_update.KnowledgeUpdatePolicyUnavailable("policy unavailable")

    monkeypatch.setattr(knowledge_update, "apply_knowledge_update", unavailable)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            editor_api_key="edit-key",
            update_signing_secret="server-signing-secret",
            policy_client=StandInPolicyClient(),
        )
    )
    response = client.post(
        "/projects/project-a/knowledge/knowledge.coverage/updates/apply",
        headers={
            "Authorization": "Bearer edit-key",
            "X-Pantheon-Human-Actor": "ifan.juang",
        },
        json={
            "proposed_markdown": "# Updated",
            "expected_version": 2,
            "base_markdown_digest": "sha256:base",
            "confirmation_token": "a" * 64,
            "confirmation_expires_at": 2_000_000_000,
            "confirmation_phrase": "CONFIRMER UPDATE",
            "idempotency_key": "knowledge-update-0003",
            **GATE_REFS,
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "policy unavailable"


def test_expired_confirmation_maps_to_gone(monkeypatch) -> None:
    def expired(_conn, **_values):
        raise knowledge_update.KnowledgeUpdateExpired("expired")

    monkeypatch.setattr(knowledge_update, "apply_knowledge_update", expired)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            editor_api_key="edit-key",
            update_signing_secret="server-signing-secret",
            policy_enforcement="disabled",
        )
    )
    response = client.post(
        "/projects/project-a/knowledge/knowledge.coverage/updates/apply",
        headers={
            "Authorization": "Bearer edit-key",
            "X-Pantheon-Human-Actor": "ifan.juang",
        },
        json={
            "proposed_markdown": "# Updated",
            "expected_version": 2,
            "base_markdown_digest": "sha256:base",
            "confirmation_token": "a" * 64,
            "confirmation_expires_at": 1,
            "confirmation_phrase": "CONFIRMER UPDATE",
            "idempotency_key": "knowledge-update-0002",
        },
    )
    assert response.status_code == 410
