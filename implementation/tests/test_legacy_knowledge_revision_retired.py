"""The historical direct Knowledge PUT must not bypass the signed UPDATE gate."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import knowledge
from mvp_vertical.cockpit_api import create_app


class _Connection:
    def close(self) -> None:
        pass


def test_direct_knowledge_revision_is_gone_even_with_editor_key(monkeypatch) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("direct revise_knowledge must not be called")

    monkeypatch.setattr(knowledge, "revise_knowledge", forbidden)
    client = TestClient(create_app(connect_fn=_Connection, editor_api_key="edit-key"))
    body = {
        "markdown": "# Updated",
        "expected_version": 1,
        "actor": "legacy-client",
        "actor_kind": "human",
        "idempotency_key": "legacy-update-1",
    }
    response = client.put(
        "/knowledge/knowledge.coverage",
        headers={"Authorization": "Bearer edit-key"},
        json=body,
    )

    assert response.status_code == 410
    assert "signed update preview/apply" in response.json()["detail"]
    assert client.put(
        "/v1/knowledge/knowledge.coverage",
        headers={"Authorization": "Bearer edit-key"},
        json=body,
    ).status_code == 404
