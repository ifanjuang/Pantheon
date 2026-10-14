"""API acceptance for B1 OIDC-scoped `/me` collaboration routes."""

from __future__ import annotations

import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from mvp_vertical import (
    agency_data,
    human_access,
    project_document_admission,
    project_documents,
    source_intake,
    store,
)
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


class FakeVerifier:
    def __init__(self, tokens: dict[str, dict]):
        self.tokens = tokens

    def verify(self, token: str) -> dict:
        if token not in self.tokens:
            raise human_access.AuthenticationFailed("OIDC access token verification failed")
        return self.tokens[token]


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def prepared():
    try:
        conn = store.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    project_document_admission.ensure_schema(conn)
    human_access.ensure_schema(conn)
    conn.execute(
        "TRUNCATE human_resource_grants, human_oidc_bindings, human_principals, "
        "doc_document_version_sources, doc_document_version_reference_observations, "
        "doc_document_events, doc_document_versions, doc_documents, "
        "agency_source_events, agency_sources, agency_project_events, agency_projects, "
        "document_versions, source_documents RESTART IDENTITY CASCADE"
    )
    conn.commit()

    for project_id in ("project-a", "project-b"):
        agency_data.create_project(
            conn,
            project_id=project_id,
            code=project_id.upper(),
            display_name=f"Project {project_id}",
            actor="admin",
            actor_kind="human",
            idempotency_key=_id("project"),
        )
    doc_a1 = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="ETUDE",
        title="BET structure",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("doc"),
    )
    doc_a2 = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="DEVIS",
        title="Offer internal",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("doc"),
    )
    project_documents.create_document(
        conn,
        parent_project_id="project-b",
        document_type="ETUDE",
        title="Other project study",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("doc"),
    )

    human_access.create_principal(conn, principal_ref="principal-bet", created_by="admin")
    human_access.bind_oidc_identity(
        conn,
        principal_ref="principal-bet",
        issuer="https://id.example.test/",
        subject="bet-user-42",
        bound_by="admin",
    )
    project_grant = human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
    )
    human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=doc_a1["document_id"],
        action="document.read",
        granted_by="admin",
    )
    human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=doc_a1["document_id"],
        action="document.revision.submit",
        granted_by="admin",
    )

    source_document_id = _id("source-document")
    source_ref = "incoming/BET_structure_C.pdf"
    digest = "c" * 64
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, 'project-a', 'project-a', %s, %s,
                  'application/pdf', 1234, 'ready')
        """,
        (source_document_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (source_document_id, source_ref, digest),
    )
    source = source_intake.create_source(
        conn,
        source_id=_id("source"),
        source_kind="document",
        origin_system="external-bet",
        origin_external_ref=source_ref,
        raw_source_ref=source_ref,
        received_at="2026-08-08T18:00:00Z",
        checksum=digest,
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("source-create"),
    )
    source = source_intake.link_project(
        conn,
        source_id=source["source_id"],
        project_id="project-a",
        expected_revision=source["revision"],
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("source-link"),
    )
    conn.commit()
    conn.close()

    verifier = FakeVerifier(
        {
            "bet-token": {
                "iss": "https://id.example.test/",
                "sub": "bet-user-42",
                "name": "BET User",
                "email": "bet@example.test",
                "iat": 100,
                "exp": 9999999999,
            }
        }
    )

    def connect_fn():
        return psycopg.connect(store.dsn_from_env())

    app = create_composed_cockpit_app(
        connect_fn=connect_fn,
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
        oidc_verifier=verifier,
    )
    return {
        "client": TestClient(app),
        "doc_a1": doc_a1,
        "doc_a2": doc_a2,
        "source": source,
        "source_document_id": source_document_id,
        "project_grant": project_grant,
    }


def _auth(token: str = "bet-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_and_project_list_use_verified_principal_and_direct_scope(prepared) -> None:
    client = prepared["client"]
    me = client.get("/me", headers=_auth())
    assert me.status_code == 200
    assert me.json()["principal"]["principal_ref"] == "principal-bet"
    assert me.json()["principal"]["email"] == "bet@example.test"
    assert me.json()["authority"]["is_approval"] is False

    projects = client.get("/me/projects", headers=_auth())
    assert projects.status_code == 200
    assert [item["project_id"] for item in projects.json()["projects"]] == ["project-a"]

    other = client.get("/me/projects/project-b", headers=_auth())
    assert other.status_code == 403


def test_document_list_and_get_do_not_leak_ungranted_project_resources(prepared) -> None:
    client = prepared["client"]
    documents = client.get("/me/projects/project-a/documents", headers=_auth())
    assert documents.status_code == 200
    assert [item["document_id"] for item in documents.json()["documents"]] == [
        prepared["doc_a1"]["document_id"]
    ]

    allowed = client.get(
        f"/me/projects/project-a/documents/{prepared['doc_a1']['document_id']}",
        headers=_auth(),
    )
    assert allowed.status_code == 200

    hidden = client.get(
        f"/me/projects/project-a/documents/{prepared['doc_a2']['document_id']}",
        headers=_auth(),
    )
    assert hidden.status_code == 403


def test_shared_service_keys_are_not_human_identity_and_human_token_is_not_hermes(prepared) -> None:
    client = prepared["client"]
    assert client.get("/me", headers=_auth("editor-key")).status_code == 401
    assert client.get("/me", headers=_auth("hermes-key")).status_code == 401
    assert client.get("/edit-requests", headers=_auth()).status_code == 401


def test_revision_submission_uses_verified_principal_as_actor(prepared) -> None:
    client = prepared["client"]
    response = client.post(
        f"/me/projects/project-a/documents/{prepared['doc_a1']['document_id']}/revisions",
        headers=_auth(),
        json={
            "source_id": prepared["source"]["source_id"],
            "source_document_id": prepared["source_document_id"],
            "source_version": 1,
            "revision_label": "C",
            "idempotency_key": "bet-submit-index-c-0001",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["principal_ref"] == "principal-bet"
    assert payload["result"]["authority"]["is_approval"] is False
    assert payload["result"]["revision"]["revision_label"] == "C"

    conn = psycopg.connect(store.dsn_from_env())
    try:
        actor = conn.execute(
            """
            SELECT actor
              FROM doc_document_events
             WHERE document_id = %s AND event_type = 'revision_linked'
             ORDER BY occurred_at DESC
             LIMIT 1
            """,
            (prepared["doc_a1"]["document_id"],),
        ).fetchone()[0]
        admitted_by = conn.execute(
            "SELECT admitted_by FROM doc_document_version_sources WHERE source_id = %s",
            (prepared["source"]["source_id"],),
        ).fetchone()[0]
    finally:
        conn.close()
    assert actor == "principal-bet"
    assert admitted_by == "principal-bet"


def test_revoked_project_grant_blocks_routes_but_keeps_professional_history(prepared) -> None:
    conn = psycopg.connect(store.dsn_from_env())
    try:
        human_access.revoke_grant(conn, grant_id=prepared["project_grant"]["grant_id"])
        conn.commit()
    finally:
        conn.close()

    client = prepared["client"]
    assert client.get("/me/projects/project-a", headers=_auth()).status_code == 403
    assert client.get("/me/projects/project-a/documents", headers=_auth()).status_code == 403

    conn = psycopg.connect(store.dsn_from_env())
    try:
        assert conn.execute(
            "SELECT count(*) FROM doc_documents WHERE document_id = %s",
            (prepared["doc_a1"]["document_id"],),
        ).fetchone()[0] == 1
    finally:
        conn.close()
