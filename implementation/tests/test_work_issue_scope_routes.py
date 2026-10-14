"""Route and authority tests for aggregate-owned WorkIssue scopes."""

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical import work_issue_scopes
from mvp_vertical.work_issue_scope_api import install_work_issue_scope_routes


def _headers(token: str, *, actor: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if actor is not None:
        headers["X-Pantheon-Human-Actor"] = actor
    return headers


def _app(monkeypatch) -> FastAPI:
    app = FastAPI()

    def with_connection(operation):
        return operation(None)

    def bearer(authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            return ""
        return authorization.removeprefix("Bearer ").strip()

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
        if bearer(authorization) not in {"read-secret", "editor-secret"}:
            raise HTTPException(status_code=401, detail="invalid read key")

    def require_editor_key(authorization: str | None = Header(default=None)) -> None:
        if bearer(authorization) != "editor-secret":
            raise HTTPException(status_code=401, detail="invalid editor key")

    def require_human_actor(
        x_pantheon_human_actor: str | None = Header(
            default=None,
            alias="X-Pantheon-Human-Actor",
        ),
    ) -> str:
        if not x_pantheon_human_actor or not x_pantheon_human_actor.strip():
            raise HTTPException(status_code=422, detail="human actor required")
        return x_pantheon_human_actor.strip()

    monkeypatch.setattr(
        work_issue_scopes,
        "create_scoped_issue",
        lambda _conn, **kwargs: {
            "work_issue": {"issue_id": kwargs["issue_id"], "version": 2},
            "scope_links": [
                {
                    "scope_link_id": kwargs["scopes"][0]["scope_link_id"],
                    "issue_ref": kwargs["issue_id"],
                    "scope_ref": {
                        "entity_type": kwargs["scopes"][0]["entity_type"],
                        "entity_id": kwargs["scopes"][0]["entity_id"],
                    },
                    "scope_role": kwargs["scopes"][0]["scope_role"],
                }
            ],
            "scope_is_not_authorization": True,
        },
    )
    monkeypatch.setattr(
        work_issue_scopes,
        "list_scoped_issue_projections",
        lambda _conn, **_kwargs: [
            {
                "work_issue": {"issue_id": "issue-one", "status": "open"},
                "scope_links": [],
                "scope_is_not_authorization": True,
            }
        ],
    )

    install_work_issue_scope_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
    )
    return app


def _create_payload() -> dict:
    return {
        "issue_id": "issue-one",
        "case_ref": "project-alpha",
        "title": "Vérifier le devis",
        "description": "Comparer le devis aux pièces du projet.",
        "idempotency_key": "create-issue-one",
        "scopes": [
            {
                "scope_link_id": "scope-one",
                "entity_type": "project",
                "entity_id": "project-alpha",
                "scope_role": "primary",
            }
        ],
    }


def test_scope_routes_are_installed_once(monkeypatch) -> None:
    app = _app(monkeypatch)
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        path = getattr(route, "path", "")
        if path.startswith("/work/"):
            methods_by_path.setdefault(path, set()).update(route.methods or set())
    assert methods_by_path["/work/issues"] == {"POST"}
    assert methods_by_path["/work/issues/{issue_id}/scopes"] == {"GET", "POST"}
    assert methods_by_path["/work/scopes/{entity_type}/{entity_id}/issues"] == {"GET"}
    assert methods_by_path[
        "/work/issues/{issue_id}/scopes/{scope_link_id}/retire"
    ] == {"POST"}
    assert methods_by_path[
        "/work/issues/{issue_id}/scopes/{scope_link_id}/replace-primary"
    ] == {"POST"}


def test_hermes_key_cannot_create_a_scoped_work_issue(monkeypatch) -> None:
    client = TestClient(_app(monkeypatch))
    response = client.post(
        "/work/issues",
        json=_create_payload(),
        headers=_headers("hermes-secret", actor="hermes-runtime"),
    )
    assert response.status_code == 401


def test_editor_key_still_requires_a_human_actor(monkeypatch) -> None:
    client = TestClient(_app(monkeypatch))
    response = client.post(
        "/work/issues",
        json=_create_payload(),
        headers=_headers("editor-secret"),
    )
    assert response.status_code == 422


def test_human_can_create_scope_without_authorization_inference(monkeypatch) -> None:
    client = TestClient(_app(monkeypatch))
    response = client.post(
        "/work/issues",
        json=_create_payload(),
        headers=_headers("editor-secret", actor="human-reviewer"),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["effect"] == "work_issue_created"
    assert payload["scope_is_not_authorization"] is True
    assert payload["work_issue"]["scope_is_not_authorization"] is True


def test_read_key_can_project_exact_entity_scope(monkeypatch) -> None:
    client = TestClient(_app(monkeypatch))
    response = client.get(
        "/work/scopes/project/project-alpha/issues",
        headers=_headers("read-secret"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scope_ref"] == {
        "entity_type": "project",
        "entity_id": "project-alpha",
    }
    assert payload["scope_match"] == "exact_entity_ref"
    assert payload["scope_is_not_authorization"] is True
    assert payload["work_issues"][0]["work_issue"]["issue_id"] == "issue-one"
