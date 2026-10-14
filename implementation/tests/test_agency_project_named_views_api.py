from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def test_project_schema_http_surface_resolves_cockpit_back_by_default() -> None:
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))

    response = client.get(
        "/agency/schema/project",
        headers={"Authorization": "Bearer read-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    schema = payload["schema"]
    assert payload["authorization_inferred"] is False
    assert schema["resolved_view"]["name"] == "cockpit_back"
    assert schema["resolved_view"]["authorization_inferred"] is False
    assert [field["key"] for field in schema["fields"]] == schema["views"]["cockpit_back"]["fields"]
    assert "revision" not in [field["key"] for field in schema["fields"]]


def test_project_schema_http_surface_can_select_notion_view() -> None:
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))

    response = client.get(
        "/agency/schema/project",
        params={"view": "notion"},
        headers={"Authorization": "Bearer read-key"},
    )

    assert response.status_code == 200
    schema = response.json()["schema"]
    assert schema["resolved_view"]["name"] == "notion"
    assert [field["key"] for field in schema["fields"]] == schema["views"]["notion"]["fields"]
    assert "revision" in [field["key"] for field in schema["fields"]]
    assert "created_by" not in [field["key"] for field in schema["fields"]]


def test_project_schema_http_surface_rejects_unknown_view() -> None:
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))

    response = client.get(
        "/agency/schema/project",
        params={"view": "invented"},
        headers={"Authorization": "Bearer read-key"},
    )

    assert response.status_code == 422
    assert "unknown Project schema view" in response.json()["detail"]


def test_project_schema_http_surface_does_not_grant_hermes_global_read() -> None:
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            hermes_api_key="hermes-key",
        )
    )

    response = client.get(
        "/agency/schema/project",
        params={"view": "hermes_context"},
        headers={"Authorization": "Bearer hermes-key"},
    )

    assert response.status_code == 403
    assert "admitted scoped execution envelope" in response.json()["detail"]