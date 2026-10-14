"""End-to-end acceptance for B2 contextual revision upload composition."""

from __future__ import annotations

import io
import json
import uuid
from pathlib import Path

import psycopg
import pytest

from mvp_vertical import (
    agency_data,
    human_access,
    human_revision_upload,
    project_documents,
    source_intake,
    storage_retention,
    store,
)
from mvp_vertical.embedder import embed, to_pgvector


@pytest.fixture
def conn():
    try:
        connection = store.connect()
        human_revision_upload.ensure_schema(connection)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
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
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _setup(conn) -> dict:
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
    document = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="ETUDE",
        title="Étude BET structure",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    other_document = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="DEVIS",
        title="Offre privée",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    human_access.create_principal(conn, principal_ref="principal-bet", created_by="admin")
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
    return {"document": document, "other_document": other_document}


def _config(tmp_path: Path, *, max_bytes: int = 1024 * 1024) -> human_revision_upload.RevisionUploadConfig:
    return human_revision_upload.RevisionUploadConfig(
        source_root=tmp_path / "sources",
        retention_root=tmp_path / "retention",
        retention_provider_ref="agency-retention-test",
        max_bytes=max_bytes,
    )


def _upload(conn, tmp_path: Path, document_id: str, *, data: bytes, filename: str, key: str, label: str = "C"):
    return human_revision_upload.upload_revision(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        document_id=document_id,
        stream=io.BytesIO(data),
        original_filename=filename,
        idempotency_key=key,
        config=_config(tmp_path),
        revision_label=label,
    )


def test_markdown_upload_composes_source_ingest_retention_and_professional_revision(conn, tmp_path) -> None:
    setup = _setup(conn)
    # Existing unrelated retrieval material in the same Project must survive the
    # one-source ingestion performed by B2.
    conn.execute(
        """
        INSERT INTO chunks (
            dossier, source_ref, chunk_no, body, embedding,
            contract_id, contract_digest, ingestion_id, source_digest
        ) VALUES ('project-a', 'existing/other.md', 0, 'existing project context',
                  %s::vector, 'existing-contract', %s, 'existing-run', %s)
        """,
        (to_pgvector(embed("existing project context")), "a" * 64, "b" * 64),
    )
    conn.commit()

    result = _upload(
        conn,
        tmp_path,
        setup["document"]["document_id"],
        data=b"# BET structure\n\nNouvel indice C.\n",
        filename="../../BET structure indice C.md",
        key="bet-index-c-0001",
    )

    assert result["source"]["project_id"] == "project-a"
    assert result["technical_capture"]["analysis_status"] == "ready"
    assert result["technical_capture"]["analysis_error"] is None
    assert result["retention"]["verified"] is True
    assert result["revision"]["revision_label"] == "C"
    assert result["authority"]["is_professional_validation"] is False
    assert conn.execute(
        "SELECT count(*) FROM chunks WHERE dossier = 'project-a' AND source_ref = 'existing/other.md'"
    ).fetchone()[0] == 1

    source = source_intake.get_source(conn, result["source"]["source_id"])
    assert source["created_by"] == "principal-bet"
    assert source["project_link_status"] == "linked"
    assert source["raw_source_ref"].startswith("human_uploads/sha256/")
    assert ".." not in source["raw_source_ref"]
    assert "BET structure indice C.md" not in source["raw_source_ref"]
    assert source["metadata"]["original_filename"] == "../../BET structure indice C.md"

    retained = storage_retention.resolve_retained_version_path(
        conn,
        document_id=result["technical_capture"]["document_id"],
        version=result["technical_capture"]["version"],
        retention_root=_config(tmp_path).retention_root,
        storage_provider_ref="agency-retention-test",
    )
    assert retained.read_bytes() == b"# BET structure\n\nNouvel indice C.\n"
    serialized = json.dumps(result, ensure_ascii=False)
    assert str(_config(tmp_path).source_root.resolve()) not in serialized
    assert str(_config(tmp_path).retention_root.resolve()) not in serialized
    # `source_ref` is a server-relative provenance identifier, not a directly
    # accessible NAS path. The physical storage roots remain undisclosed.
    assert result["revision"]["source_ref"].startswith("human_uploads/sha256/")


def test_same_idempotency_key_replays_and_different_payload_fails_closed(conn, tmp_path) -> None:
    setup = _setup(conn)
    document_id = setup["document"]["document_id"]
    first = _upload(
        conn,
        tmp_path,
        document_id,
        data=b"same index C bytes\n",
        filename="index-c.md",
        key="retry-index-c-0001",
    )
    replay = _upload(
        conn,
        tmp_path,
        document_id,
        data=b"same index C bytes\n",
        filename="index-c.md",
        key="retry-index-c-0001",
    )
    assert replay["source"]["source_id"] == first["source"]["source_id"]
    assert replay["revision"]["version_id"] == first["revision"]["version_id"]
    assert conn.execute(
        "SELECT count(*) FROM doc_document_versions WHERE document_id = %s",
        (document_id,),
    ).fetchone()[0] == 1

    with pytest.raises(source_intake.SourceIdempotencyConflict):
        _upload(
            conn,
            tmp_path,
            document_id,
            data=b"different bytes under same request identity\n",
            filename="index-c.md",
            key="retry-index-c-0001",
        )
    conn.rollback()
    assert conn.execute(
        "SELECT count(*) FROM doc_document_versions WHERE document_id = %s",
        (document_id,),
    ).fetchone()[0] == 1


def test_empty_and_oversize_uploads_are_refused_before_source_creation(conn, tmp_path) -> None:
    setup = _setup(conn)
    document_id = setup["document"]["document_id"]
    config = _config(tmp_path, max_bytes=4)
    for data, key in ((b"", "empty-upload-001"), (b"12345", "large-upload-001")):
        with pytest.raises(human_revision_upload.RevisionUploadRejected):
            human_revision_upload.upload_revision(
                conn,
                principal_ref="principal-bet",
                project_id="project-a",
                document_id=document_id,
                stream=io.BytesIO(data),
                original_filename="unsafe/../../input.md",
                idempotency_key=key,
                config=config,
                revision_label="C",
            )
        conn.rollback()
    assert conn.execute("SELECT count(*) FROM agency_sources").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM doc_document_versions").fetchone()[0] == 0


def test_ungranted_document_and_other_project_are_denied_before_file_publication(conn, tmp_path) -> None:
    setup = _setup(conn)
    config = _config(tmp_path)
    with pytest.raises(human_access.AccessDenied):
        human_revision_upload.upload_revision(
            conn,
            principal_ref="principal-bet",
            project_id="project-a",
            document_id=setup["other_document"]["document_id"],
            stream=io.BytesIO(b"secret\n"),
            original_filename="secret.md",
            idempotency_key="no-document-access-001",
            config=config,
        )
    conn.rollback()
    assert not config.source_root.exists()

    with pytest.raises(human_access.AccessDenied):
        human_revision_upload.upload_revision(
            conn,
            principal_ref="principal-bet",
            project_id="project-b",
            document_id=setup["document"]["document_id"],
            stream=io.BytesIO(b"wrong project\n"),
            original_filename="wrong.md",
            idempotency_key="wrong-project-0001",
            config=config,
        )
    conn.rollback()
    assert not config.source_root.exists()


def test_binary_analysis_failure_does_not_erase_received_revision(conn, tmp_path) -> None:
    setup = _setup(conn)
    result = _upload(
        conn,
        tmp_path,
        setup["document"]["document_id"],
        data=b"synthetic opaque binary bytes",
        filename="BET-structure-D.pdf",
        key="bet-index-d-0001",
        label="D",
    )
    assert result["technical_capture"]["analysis_status"] == "failed"
    assert "requires the bounded Docling Serve adapter" in result["technical_capture"]["analysis_error"]
    assert result["retention"]["verified"] is True
    assert result["revision"]["revision_label"] == "D"
    assert conn.execute(
        "SELECT count(*) FROM agency_sources WHERE source_id = %s",
        (result["source"]["source_id"],),
    ).fetchone()[0] == 1
    assert conn.execute(
        "SELECT count(*) FROM doc_document_versions WHERE version_id = %s",
        (result["revision"]["version_id"],),
    ).fetchone()[0] == 1
