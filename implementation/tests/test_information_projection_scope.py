"""Project-scope boundaries for Information-to-Document links."""

from __future__ import annotations

import uuid
from datetime import date

import psycopg
import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical import agency_data, agency_information, information_projection
from mvp_vertical.information_projection_api import install_information_projection_routes


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        information_projection.initialize(connection)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE agency_information_projection_events, "
        "agency_information_document_links, agency_information_projection_metadata, "
        "agency_information_cards, source_documents, agency_project_events, "
        "agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn, code: str) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=code,
        display_name=f"Projet {code}",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )


def test_document_link_cannot_cross_project_boundary(conn) -> None:
    information_project = _project(conn, "TILLEUL")
    document_project = _project(conn, "DURAND")
    information = agency_information.create_information(
        conn,
        project_id=information_project["project_id"],
        title="CCTP couverture",
        category="CCTP",
        source_type="native",
        source_note="Brouillon natif",
        index_label="B",
        information_date=date(2026, 8, 5),
        actor_kind="human",
    )
    document_id = _id("document")
    source_ref = f"upload://{document_id}"
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref,
            source_digest, media_type, byte_size, analysis_status
        ) VALUES (%s,%s,%s,%s,%s,'application/pdf',1,'ready')
        """,
        (
            document_id,
            document_project["project_id"],
            document_project["project_id"],
            source_ref,
            _id("digest"),
        ),
    )
    conn.commit()

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="Information and Document must belong to the same project",
    ):
        information_projection.add_document_link(
            conn,
            information_id=information["information_id"],
            document_id=document_id,
            role="primary",
            observed_version=1,
            observed_digest=None,
            expected_revision=0,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("link"),
        )

    count = conn.execute(
        "SELECT COUNT(*) FROM agency_information_document_links"
    ).fetchone()[0]
    assert count == 0


class _Connection:
    def close(self) -> None:
        pass


def _api_client() -> TestClient:
    app = FastAPI()

    def with_connection(operation):
        connection = _Connection()
        try:
            return operation(connection)
        finally:
            connection.close()

    def require_read_key() -> None:
        return None

    def require_writer_kind(
        authorization: str | None = Header(default=None),
    ) -> str:
        if authorization == "Bearer editor-key":
            return "human"
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


def test_cross_project_database_guard_is_exposed_as_bounded_api_error(monkeypatch) -> None:
    def reject_cross_project_link(_conn, **_values):
        raise psycopg.errors.RaiseException(
            "Information and Document must belong to the same project"
        )

    monkeypatch.setattr(
        information_projection,
        "add_document_link",
        reject_cross_project_link,
    )
    response = _api_client().post(
        "/agency/information/info-1/documents",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Actor": "ifan",
        },
        json={
            "document_id": "document-other-project",
            "role": "primary",
            "observed_version": 1,
            "expected_revision": 0,
            "idempotency_key": "cross-project-link-0001",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Information and Document must belong to the same project"
    )
