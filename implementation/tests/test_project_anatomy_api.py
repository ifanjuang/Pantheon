from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical import apu_owner, project_anatomy_projection
from mvp_vertical.project_anatomy_api import install_project_anatomy_routes


def _app() -> FastAPI:
    app = FastAPI()

    def with_connection(operation):
        return operation(object())

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer read-key":
            raise HTTPException(status_code=401, detail="invalid read API key")

    install_project_anatomy_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )
    return app


def test_project_anatomy_route_is_read_only_and_protected(monkeypatch) -> None:
    monkeypatch.setattr(
        project_anatomy_projection,
        "get_project_anatomy_projection",
        lambda conn, *, project_id: {
            "project_ref": project_id,
            "model_version": 2,
            "coverage": {"status": "not_persisted", "absence_inference_allowed": False},
            "authority": {
                "cockpit_projection_only": True,
                "authorization_inferred": False,
                "permits_runtime_writes": False,
            },
        },
    )
    client = TestClient(_app())

    assert client.get("/agency/projects/project-1/project-anatomy").status_code == 401

    response = client.get(
        "/agency/projects/project-1/project-anatomy",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["system_of_record"] == "postgres"
    assert payload["authorization_inferred"] is False
    assert payload["project_anatomy"]["authority"]["permits_runtime_writes"] is False
    assert payload["project_anatomy"]["coverage"]["absence_inference_allowed"] is False


def test_project_anatomy_route_preserves_owner_conflict_semantics(monkeypatch) -> None:
    def conflict(conn, *, project_id):
        raise apu_owner.ApuOwnerConflict("Project Anatomy owner revision is inconsistent")

    monkeypatch.setattr(
        project_anatomy_projection,
        "get_project_anatomy_projection",
        conflict,
    )
    response = TestClient(_app()).get(
        "/agency/projects/project-1/project-anatomy",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 409
    assert "revision is inconsistent" in response.json()["detail"]
