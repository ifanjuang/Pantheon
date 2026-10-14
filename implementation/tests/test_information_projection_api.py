"""HTTP boundary tests for Information-family projection routes."""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical import information_projection
from mvp_vertical.information_projection_api import install_information_projection_routes


class _Connection:
    def close(self) -> None:
        pass


def _client() -> TestClient:
    app = FastAPI()

    def with_connection(operation):
        conn = _Connection()
        try:
            return operation(conn)
        finally:
            conn.close()

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer read-key":
            raise HTTPException(status_code=401, detail="invalid read API key")

    def require_writer_kind(authorization: str | None = Header(default=None)) -> str:
        if authorization == "Bearer editor-key":
            return "human"
        if authorization == "Bearer hermes-key":
            return "hermes"
        raise HTTPException(status_code=401, detail="invalid writer API key")

    def require_actor(
        x_pantheon_actor: str | None = Header(default=None, alias="X-Pantheon-Actor"),
    ) -> str:
        if not x_pantheon_actor:
            raise HTTPException(status_code=422, detail="actor required")
        return x_pantheon_actor

    install_information_projection_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_writer_kind=require_writer_kind,
        require_actor=require_actor,
    )
    return TestClient(app)


def _projection(information_id: str = "info-1") -> dict:
    return {
        "information": {
            "information_id": information_id,
            "project_id": "project-1",
            "series_id": "series-1",
            "title": "CCTP structure",
            "category": "CCTP",
            "summary": "Prescription structurelle",
            "details": "Détails techniques",
            "author": "architecte",
            "source_ref": "source-cctp",
            "source_note": None,
            "index_label": "B",
            "information_date": "2026-08-05",
            "status": "draft",
            "limits": [],
            "type_tags": ["document-technique"],
            "subject_tags": ["structure"],
            "updated_at": "2026-08-05T11:00:00Z",
        },
        "projection": {
            "information_id": information_id,
            "source_date": "2026-08-04",
            "received_at": "2026-08-05T08:00:00Z",
            "issued_at": "2026-08-05T10:00:00Z",
            "updated_at": "2026-08-05T11:00:00Z",
            "backing_mode": "native",
            "media_types": ["text"],
            "contact_refs": [],
            "document_refs": [],
            "revision": 0,
        },
        "business_kind": "CCTP",
        "professional_index": "B",
        "business_date": "2026-08-05",
        "lifecycle_status": "draft",
        "document_authority_transferred": False,
        "authorization_inferred": False,
    }


def test_projection_read_preserves_document_authority(monkeypatch) -> None:
    monkeypatch.setattr(
        information_projection,
        "get_projection",
        lambda _conn, information_id: _projection(information_id),
    )
    response = _client().get(
        "/agency/information/info-1/projection",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_authority_transferred"] is False
    assert body["business_kind"] == "CCTP"
    assert body["information_projection"]["title"] == "CCTP structure"
    assert body["information_projection"]["revision"] == 0


def test_metadata_update_is_explicit_and_revision_checked(monkeypatch) -> None:
    observed = {}

    def update_projection_metadata(_conn, **values):
        observed.update(values)
        result = _projection(values["information_id"])
        result["projection"]["revision"] = values["expected_revision"] + 1
        result["projection"]["media_types"] = values["media_types"]
        return result

    monkeypatch.setattr(
        information_projection,
        "update_projection_metadata",
        update_projection_metadata,
    )
    response = _client().put(
        "/agency/information/info-1/projection-metadata",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Actor": "ifan",
        },
        json={
            "expected_revision": 0,
            "idempotency_key": "info-projection-metadata-0001",
            "source_date": "2026-08-01",
            "received_at": "2026-08-02T09:00:00Z",
            "issued_at": "2026-08-03T10:00:00Z",
            "media_types": ["pdf", "text", "table"],
            "contact_refs": [{"label": "BET Structure", "role": "auteur"}],
        },
    )
    assert response.status_code == 200
    assert observed["actor_kind"] == "human"
    assert observed["expected_revision"] == 0
    assert response.json()["document_authority_transferred"] is False
    assert response.json()["information_projection"]["revision"] == 1


def test_document_link_does_not_copy_document_authority(monkeypatch) -> None:
    observed = {}

    def add_document_link(_conn, **values):
        observed.update(values)
        result = _projection(values["information_id"])
        result["projection"]["backing_mode"] = "single_document"
        result["projection"]["document_refs"] = [
            {"document_id": values["document_id"], "role": values["role"]}
        ]
        result["document_link_operation"] = "created"
        return result

    monkeypatch.setattr(information_projection, "add_document_link", add_document_link)
    response = _client().post(
        "/agency/information/info-1/documents",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Actor": "ifan",
        },
        json={
            "document_id": "document-1",
            "role": "primary",
            "observed_version": 2,
            "observed_digest": "abc",
            "expected_revision": 0,
            "idempotency_key": "info-document-link-0001",
        },
    )
    assert response.status_code == 201
    assert observed["document_id"] == "document-1"
    body = response.json()
    assert body["document_authority_transferred"] is False
    assert body["information_projection"]["backing_mode"] == "single_document"


def test_hermes_global_projection_write_is_refused_before_adapter(monkeypatch) -> None:
    called = False

    def update_projection_metadata(_conn, **_values):
        nonlocal called
        called = True
        raise AssertionError("Hermes write must not reach projection adapter")

    monkeypatch.setattr(
        information_projection,
        "update_projection_metadata",
        update_projection_metadata,
    )
    response = _client().put(
        "/agency/information/info-1/projection-metadata",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Actor": "hermes",
        },
        json={
            "expected_revision": 0,
            "idempotency_key": "info-hermes-write-0001",
            "media_types": ["text"],
        },
    )
    assert response.status_code == 403
    assert called is False
