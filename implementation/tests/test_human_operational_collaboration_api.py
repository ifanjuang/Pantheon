"""PostgreSQL/API acceptance for B4 operational scoped collaboration."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from mvp_vertical import (
    agency_data,
    document_revision_discussion,
    human_access,
    human_revision_upload,
    project_document_currentness,
    project_documents,
    storage_retention,
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


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _persist_structure(
    conn,
    *,
    source_document_id: str,
    source_digest: str,
    body: str,
) -> None:
    extraction_id = _id("extraction")
    compilation_id = _id("compilation")
    output_digest = _sha_text(body)
    conn.execute(
        """
        INSERT INTO extraction_runs (
            extraction_id, document_id, contract_id, contract_digest,
            source_digest, converter, converter_version, config_digest,
            status, markdown_content, chunk_count, quality_flags
        ) VALUES (%s, %s, 'contract-b4', %s, %s, 'fixture', '1', %s,
                  'ready', %s, 0, '[]'::jsonb)
        """,
        (extraction_id, source_document_id, "c" * 64, source_digest, "f" * 64, body),
    )
    conn.execute(
        """
        INSERT INTO structured_compilations (
            compilation_id, extraction_id, compiler, compiler_version,
            config_digest, output_digest, status, quality_flags, diagnostics,
            unit_count, chunk_count, page_count, table_count, anomaly_count
        ) VALUES (%s, %s, 'pantheon_structured_extraction', '2', %s, %s,
                  'ready', '[]'::jsonb, '[]'::jsonb, 1, 0, 1, 0, 0)
        """,
        (compilation_id, extraction_id, "f" * 64, output_digest),
    )
    conn.execute(
        """
        INSERT INTO extraction_units (
            unit_id, compilation_id, extraction_id, ordinal, content_type,
            body, text_digest, page_start, page_end, structural_locator,
            parent_heading, section_path, quality_flags, table_data
        ) VALUES (%s, %s, %s, 0, 'paragraph', %s, %s, 1, 1,
                  'section:test/p:1', NULL, '[]'::jsonb, '[]'::jsonb, NULL)
        """,
        (_id("unit"), compilation_id, extraction_id, body, _sha_text(body)),
    )
    conn.commit()


def _technical_revision(
    conn,
    *,
    document: dict,
    label: str,
    content: bytes,
    source_path: Path,
    retention_root: Path,
    provider_ref: str,
    supersedes_version_id: str | None = None,
    structure_body: str | None = None,
) -> dict:
    source_document_id = _id("source-document")
    digest = _sha_bytes(content)
    source_ref = f"tests/{source_document_id}.txt"
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'text/plain', %s, 'ready')
        """,
        (
            source_document_id,
            document["parent_project_id"],
            document["parent_project_id"],
            source_ref,
            digest,
            len(content),
        ),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'text/plain', %s)
        """,
        (source_document_id, source_ref, digest, len(content)),
    )
    conn.commit()

    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(content)
    storage_retention.retain_document_version(
        conn,
        document_id=source_document_id,
        version=1,
        source_path=source_path,
        retention_root=retention_root,
        storage_provider_ref=provider_ref,
    )
    conn.commit()

    if structure_body is not None:
        _persist_structure(
            conn,
            source_document_id=source_document_id,
            source_digest=digest,
            body=structure_body,
        )

    revision = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_document_id,
        source_version=1,
        revision_label=label,
        supersedes_version_id=supersedes_version_id,
        actor="architect",
        actor_kind="human",
        idempotency_key=_id("revision"),
    )
    conn.commit()
    return revision


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def prepared(tmp_path: Path):
    try:
        conn = store.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    project_documents.ensure_schema(conn)
    conn.execute(project_document_currentness.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(storage_retention.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(human_access.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(human_access.ACTION_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(human_access.MANAGEMENT_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(document_revision_discussion.MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    conn.execute(
        "TRUNCATE doc_document_revision_comments, human_resource_grants, "
        "human_oidc_bindings, human_principals, doc_document_version_effect_events, "
        "document_version_storage_bindings, storage_object_locations, storage_objects, "
        "doc_document_version_reference_observations, doc_document_version_sources, "
        "doc_document_events, doc_document_versions, doc_documents, extraction_units, "
        "structured_compilations, extraction_runs, document_versions, source_documents, "
        "agency_source_events, agency_sources, agency_project_events, agency_projects "
        "RESTART IDENTITY CASCADE"
    )
    conn.commit()

    for project_id in ("project-a", "project-b"):
        agency_data.create_project(
            conn,
            project_id=project_id,
            code=project_id.upper(),
            display_name=f"Project {project_id}",
            actor="architect",
            actor_kind="human",
            idempotency_key=_id("project"),
        )

    document = project_documents.create_document(
        conn,
        document_id="document-study",
        parent_project_id="project-a",
        document_type="ETUDE",
        title="Étude structure",
        actor="architect",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    hidden_document = project_documents.create_document(
        conn,
        document_id="document-internal",
        parent_project_id="project-a",
        document_type="DEVIS",
        title="Document interne",
        actor="architect",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    other_document = project_documents.create_document(
        conn,
        document_id="document-other-project",
        parent_project_id="project-b",
        document_type="ETUDE",
        title="Autre projet",
        actor="architect",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    conn.commit()

    retention_root = tmp_path / "retained"
    provider_ref = "test-local-retention"
    revision_b = _technical_revision(
        conn,
        document=document,
        label="B",
        content=b"Structure B\nUw = 1.4\n",
        source_path=tmp_path / "sources" / "b.txt",
        retention_root=retention_root,
        provider_ref=provider_ref,
        structure_body="Uw = 1.4",
    )
    revision_c = _technical_revision(
        conn,
        document=document,
        label="C",
        content=b"Structure C\nUw = 1.3\n",
        source_path=tmp_path / "sources" / "c.txt",
        retention_root=retention_root,
        provider_ref=provider_ref,
        supersedes_version_id=revision_b["version_id"],
        structure_body="Uw = 1.3",
    )
    other_revision = _technical_revision(
        conn,
        document=other_document,
        label="A",
        content=b"Other project\n",
        source_path=tmp_path / "sources" / "other.txt",
        retention_root=retention_root,
        provider_ref=provider_ref,
        structure_body="Other",
    )

    project_document_currentness.record_version_event(
        conn,
        document_version_id=revision_b["version_id"],
        event_type="issued",
        new_status="issued",
        new_effect_class="coordination_update",
        new_authority_status="internal_review_authority",
        actor="architect",
        actor_kind="human",
        idempotency_key=_id("currentness"),
        reason="coordination issue",
        basis_refs=["review:b4"],
    )
    conn.commit()

    for principal_ref, subject in (
        ("principal-manager", "manager-sub"),
        ("principal-bet", "bet-sub"),
        ("principal-outsider", "outsider-sub"),
    ):
        human_access.create_principal(
            conn,
            principal_ref=principal_ref,
            created_by="bootstrap",
        )
        human_access.bind_oidc_identity(
            conn,
            principal_ref=principal_ref,
            issuer="https://id.example.test/",
            subject=subject,
            bound_by="bootstrap",
        )

    manager_read = human_access.grant_access(
        conn,
        principal_ref="principal-manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="bootstrap",
    )
    manager_manage = human_access.grant_access(
        conn,
        principal_ref="principal-manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.access.manage",
        granted_by="bootstrap",
    )
    bet_project = human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="bootstrap",
    )
    bet_read = human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=document["document_id"],
        action="document.read",
        granted_by="bootstrap",
    )
    bet_submit = human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=document["document_id"],
        action="document.revision.submit",
        granted_by="bootstrap",
    )
    conn.commit()
    conn.close()

    verifier = FakeVerifier(
        {
            "manager-token": {
                "iss": "https://id.example.test/",
                "sub": "manager-sub",
                "name": "Agency Manager",
                "exp": 9999999999,
            },
            "bet-token": {
                "iss": "https://id.example.test/",
                "sub": "bet-sub",
                "name": "BET User",
                "exp": 9999999999,
            },
            "outsider-token": {
                "iss": "https://id.example.test/",
                "sub": "outsider-sub",
                "name": "Outsider",
                "exp": 9999999999,
            },
        }
    )
    upload_config = human_revision_upload.RevisionUploadConfig(
        source_root=tmp_path / "human-uploads",
        retention_root=retention_root,
        retention_provider_ref=provider_ref,
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
        oidc_verifier=verifier,
        revision_upload_config=upload_config,
    )
    return {
        "client": TestClient(app),
        "document": document,
        "hidden_document": hidden_document,
        "revision_b": revision_b,
        "revision_c": revision_c,
        "other_revision": other_revision,
        "retention_root": retention_root,
        "provider_ref": provider_ref,
        "manager_read": manager_read,
        "manager_manage": manager_manage,
        "bet_project": bet_project,
        "bet_read": bet_read,
        "bet_submit": bet_submit,
    }


def test_exact_revision_content_is_scoped_verified_and_does_not_expose_storage_path(prepared) -> None:
    client = prepared["client"]
    document_id = prepared["document"]["document_id"]
    version_id = prepared["revision_c"]["version_id"]
    response = client.get(
        f"/me/projects/project-a/documents/{document_id}/revisions/{version_id}/content",
        headers=_auth("bet-token"),
    )
    assert response.status_code == 200, response.text
    assert response.content == b"Structure C\nUw = 1.3\n"
    assert response.headers["content-type"].startswith("text/plain")
    assert "inline" in response.headers["content-disposition"]
    assert str(prepared["retention_root"]) not in str(response.headers)

    download = client.get(
        f"/me/projects/project-a/documents/{document_id}/revisions/{version_id}/content?download=true",
        headers=_auth("bet-token"),
    )
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]

    outsider = client.get(
        f"/me/projects/project-a/documents/{document_id}/revisions/{version_id}/content",
        headers=_auth("outsider-token"),
    )
    assert outsider.status_code == 403

    wrong_scope = client.get(
        f"/me/projects/project-a/documents/{document_id}/revisions/{prepared['other_revision']['version_id']}/content",
        headers=_auth("bet-token"),
    )
    assert wrong_scope.status_code == 404


def test_project_access_manager_can_manage_only_ordinary_grants_inside_project(prepared) -> None:
    client = prepared["client"]
    listing = client.get(
        "/me/projects/project-a/access/grants",
        headers=_auth("manager-token"),
    )
    assert listing.status_code == 200, listing.text
    assert any(item["action"] == "project.access.manage" for item in listing.json()["grants"])
    assert "project.access.manage" not in listing.json()["remote_manageable_actions"]

    granted = client.post(
        "/me/projects/project-a/access/grants",
        headers=_auth("manager-token"),
        json={
            "principal_ref": "principal-bet",
            "resource_type": "project_document",
            "resource_id": prepared["document"]["document_id"],
            "action": "document.comment",
            "reason": "coordination discussion",
        },
    )
    assert granted.status_code == 201, granted.text
    comment_grant = granted.json()["grant"]
    assert comment_grant["granted_by"] == "principal-manager"

    forbidden_delegate = client.post(
        "/me/projects/project-a/access/grants",
        headers=_auth("manager-token"),
        json={
            "principal_ref": "principal-bet",
            "resource_type": "project",
            "resource_id": "project-a",
            "action": "project.access.manage",
        },
    )
    assert forbidden_delegate.status_code == 422

    forbidden_revoke_manager = client.post(
        f"/me/projects/project-a/access/grants/{prepared['manager_manage']['grant_id']}/revoke",
        headers=_auth("manager-token"),
    )
    assert forbidden_revoke_manager.status_code == 422

    other_project = client.get(
        "/me/projects/project-b/access/grants",
        headers=_auth("manager-token"),
    )
    assert other_project.status_code == 403

    revoked = client.post(
        f"/me/projects/project-a/access/grants/{comment_grant['grant_id']}/revoke",
        headers=_auth("manager-token"),
    )
    assert revoked.status_code == 200
    assert revoked.json()["grant"]["revoked_at"] is not None

    post_after_revoke = client.post(
        f"/me/projects/project-a/documents/{prepared['document']['document_id']}"
        f"/revisions/{prepared['revision_c']['version_id']}/comments",
        headers={**_auth("bet-token"), "Idempotency-Key": "comment-after-revoke"},
        json={"body": "Should be denied"},
    )
    assert post_after_revoke.status_code == 403


def test_currentness_and_portal_projection_preserve_authority_boundaries(prepared) -> None:
    client = prepared["client"]
    document_id = prepared["document"]["document_id"]

    latest = client.get(
        f"/me/projects/project-a/documents/{document_id}/currentness/latest_received",
        headers=_auth("bet-token"),
    )
    assert latest.status_code == 200
    assert latest.json()["document_version_id"] == prepared["revision_c"]["version_id"]

    coordination = client.get(
        f"/me/projects/project-a/documents/{document_id}/currentness/current_for_coordination",
        headers=_auth("bet-token"),
    )
    assert coordination.status_code == 200
    assert coordination.json()["document_version_id"] == prepared["revision_b"]["version_id"]

    contractual = client.get(
        f"/me/projects/project-a/documents/{document_id}/currentness/current_contractual",
        headers=_auth("bet-token"),
    )
    assert contractual.status_code == 200
    assert contractual.json()["resolution_status"] == "unresolved"
    assert contractual.json()["document_version_id"] is None

    portal = client.get(
        "/me/projects/project-a/portal",
        headers=_auth("bet-token"),
    )
    assert portal.status_code == 200, portal.text
    payload = portal.json()
    assert [item["document"]["document_id"] for item in payload["documents"]] == [document_id]
    assert payload["project_capabilities"] == {"read": True, "manage_access": False}
    assert payload["documents"][0]["capabilities"] == {
        "read": True,
        "submit_revision": True,
        "comment": False,
    }
    assert payload["documents"][0]["currentness"]["latest_received"]["document_version_id"] == prepared["revision_c"]["version_id"]
    assert payload["documents"][0]["currentness"]["current_for_coordination"]["document_version_id"] == prepared["revision_b"]["version_id"]
    assert payload["authority"]["is_authorization"] is False
    assert payload["authority"]["changes_project_truth"] is False


def test_exact_revision_comparison_is_read_only_and_project_scoped(prepared) -> None:
    client = prepared["client"]
    document_id = prepared["document"]["document_id"]
    conn = psycopg.connect(store.dsn_from_env())
    try:
        before_counts = {
            "events": conn.execute("SELECT count(*) FROM doc_document_events").fetchone()[0],
            "version_effects": conn.execute(
                "SELECT count(*) FROM doc_document_version_effect_events"
            ).fetchone()[0],
        }
    finally:
        conn.close()

    response = client.get(
        f"/me/projects/project-a/documents/{document_id}/comparison",
        params={
            "before_version_id": prepared["revision_b"]["version_id"],
            "after_version_id": prepared["revision_c"]["version_id"],
        },
        headers=_auth("bet-token"),
    )
    assert response.status_code == 200, response.text
    assert response.json()["summary"]["modified"] == 1
    assert response.json()["summary"]["has_changes"] is True
    assert response.json()["authority"]["establishes_downstream_impact"] is False

    wrong_revision = client.get(
        f"/me/projects/project-a/documents/{document_id}/comparison",
        params={
            "before_version_id": prepared["revision_b"]["version_id"],
            "after_version_id": prepared["other_revision"]["version_id"],
        },
        headers=_auth("bet-token"),
    )
    assert wrong_revision.status_code == 404

    conn = psycopg.connect(store.dsn_from_env())
    try:
        after_counts = {
            "events": conn.execute("SELECT count(*) FROM doc_document_events").fetchone()[0],
            "version_effects": conn.execute(
                "SELECT count(*) FROM doc_document_version_effect_events"
            ).fetchone()[0],
        }
    finally:
        conn.close()
    assert after_counts == before_counts
