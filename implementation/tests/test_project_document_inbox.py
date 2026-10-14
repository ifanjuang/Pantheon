"""PostgreSQL acceptance for A5 deterministic Source reconciliation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from mvp_vertical import (
    agency_data,
    project_document_admission,
    project_document_inbox,
    project_documents,
    source_intake,
)


@pytest.fixture
def conn():
    try:
        connection = project_document_inbox.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_version_effect_events, doc_document_version_sources, "
        "doc_document_events, doc_document_versions, doc_documents, "
        "agency_source_events, agency_source_relations, agency_sources, "
        "document_versions, source_documents, agency_project_events, "
        "agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _source_id() -> str:
    return f"source-{uuid.uuid4().hex}"


def _project(conn, label: str = "A") -> str:
    project_id = _id(f"project-{label.lower()}")
    agency_data.create_project(
        conn,
        project_id=project_id,
        code=f"P-{uuid.uuid4().hex[:10]}",
        display_name=f"Project {label}",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    conn.commit()
    return project_id


def _source(
    conn,
    *,
    project_id: str | None,
    raw_ref: str,
    checksum: str | None,
    origin_ref: str | None = None,
) -> dict:
    source_id = _source_id()
    created = source_intake.create_source(
        conn,
        source_id=source_id,
        source_kind="document",
        origin_system="inbox-test",
        origin_external_ref=origin_ref or raw_ref,
        raw_source_ref=raw_ref,
        received_at=datetime(2026, 8, 8, 13, 0, tzinfo=timezone.utc),
        checksum=checksum,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("source-create"),
    )
    if project_id is None:
        conn.commit()
        return created
    linked = source_intake.link_project(
        conn,
        source_id=source_id,
        project_id=project_id,
        expected_revision=created["revision"],
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("source-link"),
    )
    conn.commit()
    return linked


def _technical(
    conn,
    *,
    project_id: str,
    source_ref: str,
    versions: list[tuple[int, str]],
    document_id: str | None = None,
) -> str:
    document_id = document_id or _id("source-document")
    latest_digest = versions[-1][1]
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 1234, 'ready')
        """,
        (document_id, project_id, project_id, source_ref, latest_digest),
    )
    for version, digest in versions:
        conn.execute(
            """
            INSERT INTO document_versions (
                document_id, version, source_ref, source_digest, media_type, byte_size
            ) VALUES (%s, %s, %s, %s, 'application/pdf', 1234)
            """,
            (document_id, version, source_ref, digest),
        )
    conn.commit()
    return document_id


def _logical(conn, *, project_id: str, title: str = "Étude thermique") -> dict:
    document = project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id=project_id,
        document_type="ETUDE",
        title=title,
        discipline_code="THERMIQUE",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("logical-create"),
    )
    conn.commit()
    return document


def _link_professional(
    conn,
    *,
    document: dict,
    technical_id: str,
    source_version: int,
    label: str,
) -> dict:
    revision = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=technical_id,
        source_version=source_version,
        revision_label=label,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("revision-link"),
    )
    conn.commit()
    return revision


def test_unlinked_and_suggested_sources_reuse_existing_source_intake_project_posture(conn) -> None:
    project_id = _project(conn)
    unlinked = _source(conn, project_id=None, raw_ref="upload/u.pdf", checksum="1" * 64)
    result = project_document_inbox.reconcile_source(conn, source_id=unlinked["source_id"])
    assert result["status"] == "needs_project_link"
    assert result["project_candidates"] == []

    suggested = source_intake.suggest_projects(
        conn,
        source_id=unlinked["source_id"],
        candidates=[
            {
                "project_ref": project_id,
                "score": 0.8,
                "basis": ["declared project name"],
                "producer": "test",
                "created_at": "2026-08-08T13:00:00+00:00",
            }
        ],
        expected_revision=unlinked["revision"],
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("suggest"),
    )
    conn.commit()
    result = project_document_inbox.reconcile_source(conn, source_id=suggested["source_id"])
    assert result["status"] == "needs_project_link"
    assert result["project_candidates"][0]["project_ref"] == project_id
    assert result["authority"]["project_link_confirmed"] is False


def test_missing_and_ambiguous_technical_capture_fail_closed(conn) -> None:
    project_id = _project(conn)
    missing = _source(conn, project_id=project_id, raw_ref="upload/missing.pdf", checksum="2" * 64)
    result = project_document_inbox.reconcile_source(conn, source_id=missing["source_id"])
    assert result["status"] == "needs_technical_capture"

    digest = "3" * 64
    _technical(conn, project_id=project_id, source_ref="one.pdf", versions=[(1, digest)])
    _technical(conn, project_id=project_id, source_ref="two.pdf", versions=[(1, digest)])
    ambiguous = _source(conn, project_id=project_id, raw_ref="upload/ambiguous", checksum=digest)
    result = project_document_inbox.reconcile_source(conn, source_id=ambiguous["source_id"])
    assert result["status"] == "technical_capture_ambiguous"
    assert result["reconciliation_basis"] == "checksum"
    assert len(result["technical_candidates"]) == 2


def test_checksumless_source_uses_only_exact_reference_fallback(conn) -> None:
    project_id = _project(conn)
    technical = _technical(
        conn,
        project_id=project_id,
        source_ref="NAS/BET/thermal_B.pdf",
        versions=[(1, "4" * 64)],
    )
    source = _source(
        conn,
        project_id=project_id,
        raw_ref="NAS/BET/thermal_B.pdf",
        checksum=None,
    )
    result = project_document_inbox.reconcile_source(conn, source_id=source["source_id"])
    assert result["status"] == "needs_document_identity"
    assert result["technical_capture"]["source_document_id"] == technical
    assert result["technical_capture"]["basis"] == "exact_reference"


def test_exact_professional_digest_projects_duplicate_receipt_candidate(conn) -> None:
    project_id = _project(conn)
    digest = "5" * 64
    technical = _technical(
        conn, project_id=project_id, source_ref="BET/thermal_C.pdf", versions=[(1, digest)]
    )
    logical = _logical(conn, project_id=project_id)
    revision = _link_professional(
        conn, document=logical, technical_id=technical, source_version=1, label="C"
    )
    source = _source(conn, project_id=project_id, raw_ref="upload/resend", checksum=digest)

    before = conn.execute("SELECT count(*) FROM doc_document_versions").fetchone()[0]
    result = project_document_inbox.reconcile_source(conn, source_id=source["source_id"])
    assert result["status"] == "probable_duplicate_receipt"
    assert result["professional_candidate"]["version_id"] == revision["version_id"]
    assert result["candidate_basis"] == "exact_professional_content_digest"
    assert result["authority"]["revision_admitted"] is False
    assert conn.execute("SELECT count(*) FROM doc_document_versions").fetchone()[0] == before


def test_same_digest_in_multiple_logical_documents_is_identity_ambiguous(conn) -> None:
    project_id = _project(conn)
    digest = "6" * 64
    technical = _technical(
        conn, project_id=project_id, source_ref="shared.pdf", versions=[(1, digest)]
    )
    first = _logical(conn, project_id=project_id, title="Document A")
    second = _logical(conn, project_id=project_id, title="Document B")
    _link_professional(conn, document=first, technical_id=technical, source_version=1, label="A")
    _link_professional(conn, document=second, technical_id=technical, source_version=1, label="A")
    source = _source(conn, project_id=project_id, raw_ref="upload/shared", checksum=digest)

    result = project_document_inbox.reconcile_source(conn, source_id=source["source_id"])
    assert result["status"] == "document_identity_ambiguous"
    assert result["candidate_basis"] == "exact_digest_used_by_multiple_logical_documents"
    assert {item["document_id"] for item in result["professional_candidates"]} == {
        first["document_id"],
        second["document_id"],
    }


def test_same_technical_source_identity_with_new_bytes_projects_probable_new_revision(conn) -> None:
    project_id = _project(conn)
    technical = _technical(
        conn,
        project_id=project_id,
        source_ref="NAS/BET/thermal.pdf",
        versions=[(1, "7" * 64), (2, "8" * 64)],
    )
    logical = _logical(conn, project_id=project_id)
    previous = _link_professional(
        conn, document=logical, technical_id=technical, source_version=1, label="B"
    )
    source = _source(
        conn,
        project_id=project_id,
        raw_ref="upload/new-version",
        checksum="8" * 64,
    )

    result = project_document_inbox.reconcile_source(conn, source_id=source["source_id"])
    assert result["status"] == "probable_new_revision"
    assert result["professional_candidate"]["document_id"] == logical["document_id"]
    assert result["professional_candidate"]["suggested_predecessor_version_id"] == previous["version_id"]
    assert result["candidate_basis"] == "same_technical_source_identity_existing_professional_lineage"


def test_renamed_similar_file_with_new_technical_identity_is_not_guessed_as_revision(conn) -> None:
    project_id = _project(conn)
    old_technical = _technical(
        conn,
        project_id=project_id,
        source_ref="BET/thermal_B.pdf",
        versions=[(1, "9" * 64)],
    )
    logical = _logical(conn, project_id=project_id)
    _link_professional(
        conn, document=logical, technical_id=old_technical, source_version=1, label="B"
    )
    _technical(
        conn,
        project_id=project_id,
        source_ref="BET/thermal_C.pdf",
        versions=[(1, "a" * 64)],
    )
    source = _source(
        conn,
        project_id=project_id,
        raw_ref="upload/thermal_C.pdf",
        checksum="a" * 64,
    )

    result = project_document_inbox.reconcile_source(conn, source_id=source["source_id"])
    assert result["status"] == "needs_document_identity"
    assert result["candidate_basis"] == "no_deterministic_professional_lineage"
    assert "semantic candidate" in result["reason"]


def test_already_admitted_source_returns_exact_a2_binding(conn) -> None:
    project_id = _project(conn)
    digest = "b" * 64
    technical = _technical(
        conn, project_id=project_id, source_ref="BET/study_A.pdf", versions=[(1, digest)]
    )
    logical = _logical(conn, project_id=project_id)
    source = _source(conn, project_id=project_id, raw_ref="upload/study", checksum=digest)
    admitted = project_document_admission.admit_source_as_revision(
        conn,
        source_id=source["source_id"],
        document_id=logical["document_id"],
        source_document_id=technical,
        source_version=1,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("admit"),
    )
    conn.commit()

    result = project_document_inbox.reconcile_source(conn, source_id=source["source_id"])
    assert result["status"] == "already_admitted"
    assert result["admitted"]["document_version_id"] == admitted["document_version_id"]
    assert result["authority"]["professional_identity_confirmed"] is True
    assert result["authority"]["revision_admitted"] is True
