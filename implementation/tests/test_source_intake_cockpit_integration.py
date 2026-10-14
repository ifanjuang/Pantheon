"""Integration checks for Source intake installation in the main Cockpit app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import source_intake
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def _source() -> dict:
    return {
        "source_id": "source-1",
        "source_kind": "email",
        "origin_system": "gmail",
        "origin_external_ref": "message-1",
        "origin_producer": None,
        "received_by": None,
        "raw_source_ref": "gmail://message-1",
        "received_at": "2026-08-05T17:00:00Z",
        "project_link_status": "unassigned",
        "project_id": None,
        "declared_project_name": None,
        "candidate_project_refs": [],
        "source_date": None,
        "mime_type": "message/rfc822",
        "checksum": None,
        "confidentiality": None,
        "metadata": {},
        "revision": 1,
    }


def test_source_routes_are_installed_in_main_cockpit_app(monkeypatch) -> None:
    monkeypatch.setattr(
        source_intake,
        "list_sources",
        lambda _conn, **_values: [_source()],
    )
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            initialize_fn=None,
            api_key="read-key",
            editor_api_key="editor-key",
            hermes_api_key="hermes-key",
        )
    )

    response = client.get(
        "/agency/sources",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 200
    assert response.json()["sources"][0]["source_id"] == "source-1"
    assert response.json()["source_projections"][0]["origin"]["system"] == "gmail"


def test_main_cockpit_refuses_hermes_global_source_write(monkeypatch) -> None:
    called = False

    def create_source(_conn, **_values):
        nonlocal called
        called = True
        raise AssertionError("Hermes must be rejected before Source adapter execution")

    monkeypatch.setattr(source_intake, "create_source", create_source)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            initialize_fn=None,
            editor_api_key="editor-key",
            hermes_api_key="hermes-key",
        )
    )

    response = client.post(
        "/agency/sources",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Actor": "hermes",
        },
        json={
            "source_id": "source-hermes-1",
            "source_kind": "text",
            "origin": {"system": "hermes", "external_ref": "result-1"},
            "raw_source_ref": "native://candidate",
            "received_at": "2026-08-05T17:00:00Z",
            "idempotency_key": "source-hermes-0001",
        },
    )
    assert response.status_code == 403
    assert called is False
