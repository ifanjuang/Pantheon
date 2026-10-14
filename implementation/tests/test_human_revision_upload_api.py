"""API acceptance for B2 multipart contextual revision upload."""

from __future__ import annotations

import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from mvp_vertical import agency_data, human_access, human_revision_upload, project_documents, store
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


class FakeVerifier:
    def verify(self, token: str) -> dict:
        if token != "bet-token":
            raise human_access.AuthenticationFailed("OIDC access token verification failed")
        return {
            "iss": "https://id.example.test/",
            "sub": "bet-user-42",
            "name": "BET User",
            "exp": 9999999999,
        }


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def prepared(tmp_path):
    try:
        conn = store.connect()
        human_revision_upload.ensure_schema(conn)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    conn.execute(
        "TRUNCATE human_resource_grants, human_oidc_bindings, human_principals, "
        "document_version_storage_bindings, storage_object_locations, storage_objects, "
        "doc_document_version_sources, doc_document_version_reference_observations, "
        "doc_document_events, doc_document_versions, doc_documents, "
        "agency_source_events, agency_source_relations, agency_sources, "
        "agency_project_events, agency_projects, chunks, document_compilation_bindings, "
        "extraction_units, structured_compilations, document_extraction_bindings, "
        "extraction_observations, extraction_runs, document_versions, source_documents "
        "RESTART IDENTITY CASCADE"
    )
    conn.commit()
    agency_data.create_project(
        conn,
        project_id="project-a",
        code="PROJECT-A",
        display_name="Project A",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("project"),
    )
    document = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="ETUDE",
        title="Étude BET",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    human_access.create_principal(conn, principal_ref="principal-bet", created_by="admin")
    human_access.bind_oidc_identity(
        conn,
        principal_ref="principal-bet",
        issuer="https://id.example.test/",
        subject="bet-user-42",
        bound_by="admin",
    )
    for resource_type, resource_id, action in (
        ("project", "project-a", "project.read"),
        ("project_document", document["document_id"], "document.read"),
        ("project_document", document["document_id"], "document.revision.submit"),
    ):
        human_access.grant_access(
            conn,
            principal_ref="principal-bet",
            project_id="project-a",
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            granted_by="admin",
        )
    conn.commit()
    conn.close()

    config = human_revision_upload.RevisionUploadConfig(
        source_root=tmp_path / "sources",
        retention_root=tmp_path / "retention",
        retention_provider_ref="test-retention",
        max_bytes=1024 * 1024,
    )

    def connect_fn():
        return psycopg.connect(store.dsn_from_env())

    app = create_composed_cockpit_app(
        connect_fn=connect_fn,
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
        oidc_verifier=FakeVerifier(),
        revision_upload_config=config,
    )
    return TestClient(app), document, config


def test_multipart_upload_uses_verified_principal_and_returns_no_physical_path(prepared) -> None:
    client, document, config = prepared
    response = client.post(
        f"/me/projects/project-a/documents/{document['document_id']}/revision-uploads",
        headers={"Authorization": "Bearer bet-token", "Idempotency-Key": "api-bet-index-c-0001"},
        data={"revision_label": "C"},
        files={
            "file": (
                "../../BET-structure-C.md",
                b"# Structure\n\nIndice C depuis le BET.\n",
                "text/markdown",
            )
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["principal_ref"] == "principal-bet"
    assert payload["result"]["revision"]["revision_label"] == "C"
    assert payload["result"]["retention"]["verified"] is True
    assert str(config.source_root) not in response.text
    assert str(config.retention_root) not in response.text

    conn = psycopg.connect(store.dsn_from_env())
    try:
        actor = conn.execute(
            """
            SELECT actor FROM doc_document_events
             WHERE document_id = %s AND event_type = 'revision_linked'
             ORDER BY occurred_at DESC LIMIT 1
            """,
            (document["document_id"],),
        ).fetchone()[0]
    finally:
        conn.close()
    assert actor == "principal-bet"


def test_missing_idempotency_key_and_missing_upload_config_fail_explicitly(prepared) -> None:
    client, document, _config = prepared
    no_key = client.post(
        f"/me/projects/project-a/documents/{document['document_id']}/revision-uploads",
        headers={"Authorization": "Bearer bet-token"},
        files={"file": ("index.md", b"content", "text/markdown")},
    )
    assert no_key.status_code == 422

    def connect_fn():
        return psycopg.connect(store.dsn_from_env())

    app = create_composed_cockpit_app(
        connect_fn=connect_fn,
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
        oidc_verifier=FakeVerifier(),
        revision_upload_config=None,
    )
    # Clear env-driven defaults so this test exercises the explicit disabled posture.
    app.state.revision_upload_config = None
    disabled = TestClient(app).post(
        f"/me/projects/project-a/documents/{document['document_id']}/revision-uploads",
        headers={"Authorization": "Bearer bet-token", "Idempotency-Key": "disabled-upload-001"},
        files={"file": ("index.md", b"content", "text/markdown")},
    )
    assert disabled.status_code == 503
