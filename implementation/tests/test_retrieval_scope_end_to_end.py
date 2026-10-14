"""Database acceptance for access + currentness + exact retrieval composition."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from mvp_vertical import (
    agency_data,
    human_access,
    project_document_currentness,
    project_documents,
    retrieval_scope,
    store,
)
from mvp_vertical.contract import TaskContract
from mvp_vertical.documents import file_digest


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _connect_or_skip():
    try:
        conn = human_access.connect()
        project_document_currentness.ensure_schema(conn)
        return conn
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL/pgvector unreachable: {exc}")


def _contract(project_id: str, source_ref: str) -> TaskContract:
    contract_id = _id("task")
    return TaskContract(
        raw={
            "object_id": contract_id,
            "contract_id": contract_id,
            "scope": {
                "parent_project_id": project_id,
                "declared_sources": [source_ref],
            },
        },
        path=Path("task.yaml"),
        dossier=project_id,
        sources=(source_ref,),
        forbidden=(),
    )


def test_authorized_resolved_historical_revision_is_the_only_ranked_digest(tmp_path) -> None:
    conn = _connect_or_skip()
    project_id = _id("project")
    source_ref = "sources/reference.md"
    contract = _contract(project_id, source_ref)
    source = tmp_path / source_ref
    source.parent.mkdir(parents=True)

    try:
        agency_data.create_project(
            conn,
            project_id=project_id,
            code=project_id.upper(),
            display_name="Retrieval scope integration",
            contacts=[],
            actor="admin",
            actor_kind="human",
            idempotency_key=_id("project-create"),
        )
        conn.commit()

        source.write_text(
            "# Reference\n\nlegacytoken belongs only to the applicable older revision.",
            encoding="utf-8",
        )
        old_digest = file_digest(source)
        store.ingest(conn, contract, tmp_path, ingestion_id=_id("old-ingestion"))

        source.write_text(
            "# Reference\n\ncurrenttoken belongs only to the newer technical revision.",
            encoding="utf-8",
        )
        new_digest = file_digest(source)
        assert new_digest != old_digest
        store.ingest(conn, contract, tmp_path, ingestion_id=_id("new-ingestion"))

        technical = conn.execute(
            "SELECT document_id, source_digest FROM source_documents "
            "WHERE dossier = %s AND source_ref = %s",
            (project_id, source_ref),
        ).fetchone()
        assert technical is not None
        source_document_id, current_digest = technical
        assert current_digest == new_digest

        logical = project_documents.create_document(
            conn,
            parent_project_id=project_id,
            document_type="REFERENCE",
            title="Applicable reference",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("document-create"),
        )
        conn.commit()
        old_revision = project_documents.link_revision(
            conn,
            document_id=logical["document_id"],
            source_document_id=source_document_id,
            source_version=1,
            revision_label="A",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("link-old"),
        )
        conn.commit()
        project_documents.link_revision(
            conn,
            document_id=logical["document_id"],
            source_document_id=source_document_id,
            source_version=2,
            revision_label="B",
            supersedes_version_id=old_revision["version_id"],
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("link-new"),
        )
        conn.commit()

        project_document_currentness.record_version_event(
            conn,
            document_version_id=old_revision["version_id"],
            event_type="issued",
            new_status="issued",
            new_effect_class="working_revision",
            new_authority_status="internal_working_authority",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("old-working"),
            reason="older revision remains the bounded working posture",
            basis_refs=["review:integration"],
        )
        conn.commit()

        principal_ref = _id("principal")
        human_access.create_principal(conn, principal_ref=principal_ref, created_by="admin")
        human_access.grant_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project",
            resource_id=project_id,
            action="project.read",
            granted_by="admin",
        )
        human_access.grant_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=logical["document_id"],
            action="document.read",
            granted_by="admin",
        )
        conn.commit()
        principal = human_access.PrincipalContext(
            principal_ref=principal_ref,
            issuer="test",
            subject="test-subject",
        )

        resolution, hits = retrieval_scope.retrieve_accessible_applicable_hybrid(
            conn,
            principal,
            contract=contract,
            project_id=project_id,
            requested_documents=((logical["document_id"], "current_working"),),
            query="legacytoken",
            top_k=4,
            candidate_k=8,
        )

        assert len(resolution.sources) == 1
        resolved = resolution.sources[0]
        assert resolved.document_version_id == old_revision["version_id"]
        assert resolved.source_version == 1
        assert resolved.source_digest == old_digest
        assert hits
        assert {hit.chunk.source_digest for hit in hits} == {old_digest}
        assert all("currenttoken" not in hit.chunk.body for hit in hits)

        current_hits = store.retrieve_scoped(conn, contract, "legacytoken", top_k=8)
        assert current_hits
        assert {hit.source_digest for hit in current_hits} == {new_digest}
    finally:
        conn.close()
