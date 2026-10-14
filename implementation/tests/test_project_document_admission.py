"""PostgreSQL acceptance tests for A2 Source-to-revision admission."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from mvp_vertical import agency_data, project_document_admission, project_documents, source_intake


@pytest.fixture
def conn():
    try:
        connection = project_document_admission.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_version_sources, doc_document_events, "
        "doc_document_versions, doc_documents, agency_source_events, "
        "agency_source_relations, agency_sources, source_documents, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _source_id() -> str:
    return f"source-{uuid.uuid4().hex}"


def _project(conn, project_id: str) -> dict:
    return agency_data.create_project(
        conn,
        project_id=project_id,
        code=f"P-{uuid.uuid4().hex[:10]}",
        display_name=project_id,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project"),
    )


def _logical_document(conn, project_id: str, title: str = "Étude thermique") -> dict:
    return project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id=project_id,
        document_type="ETUDE",
        title=title,
        discipline_code="THERMIQUE",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("document"),
    )


def _technical(
    conn,
    *,
    project_id: str,
    source_ref: str,
    digest: str | None = None,
) -> tuple[str, int, str]:
    document_id = _id("source-document")
    digest = digest or uuid.uuid4().hex * 2
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 1234, 'ready')
        """,
        (document_id, project_id, project_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (document_id, source_ref, digest),
    )
    conn.commit()
    return document_id, 1, digest


def _preserved_source(
    conn,
    *,
    project_id: str,
    raw_source_ref: str,
    checksum: str | None,
    origin_external_ref: str | None = None,
) -> dict:
    source_id = _source_id()
    created = source_intake.create_source(
        conn,
        source_id=source_id,
        source_kind="document",
        origin_system="portal-test",
        origin_external_ref=origin_external_ref or raw_source_ref,
        raw_source_ref=raw_source_ref,
        received_at=datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc),
        checksum=checksum,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("source-create"),
    )
    return source_intake.link_project(
        conn,
        source_id=source_id,
        project_id=project_id,
        expected_revision=created["revision"],
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("source-link"),
    )


def test_contextual_bet_sources_admit_b_then_c_into_one_logical_document(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    tech_b, version_b, digest_b = _technical(
        conn, project_id=project_id, source_ref="BET/thermal_B.pdf"
    )
    tech_c, version_c, digest_c = _technical(
        conn, project_id=project_id, source_ref="BET/thermal_C.pdf"
    )
    source_b = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/b", checksum=digest_b
    )
    source_c = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/c", checksum=digest_c
    )

    admitted_b = project_document_admission.admit_source_as_revision(
        conn,
        source_id=source_b["source_id"],
        document_id=document["document_id"],
        source_document_id=tech_b,
        source_version=version_b,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("admit-b"),
    )
    admitted_c = project_document_admission.admit_source_as_revision(
        conn,
        source_id=source_c["source_id"],
        document_id=document["document_id"],
        source_document_id=tech_c,
        source_version=version_c,
        revision_label="C",
        supersedes_version_id=admitted_b["document_version_id"],
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("admit-c"),
    )

    assert admitted_b["revision"]["version_seq"] == 1
    assert admitted_c["revision"]["version_seq"] == 2
    assert admitted_c["revision"]["supersedes_version_id"] == admitted_b["document_version_id"]
    assert admitted_c["authority"]["is_professional_validation"] is False
    assert [row["source_id"] for row in project_document_admission.list_revision_sources(conn, admitted_c["document_version_id"])] == [source_c["source_id"]]


def test_duplicate_resend_records_second_source_without_false_revision(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    digest = "a" * 64
    tech_1, version_1, _ = _technical(
        conn, project_id=project_id, source_ref="BET/thermal_C.pdf", digest=digest
    )
    tech_2, version_2, _ = _technical(
        conn, project_id=project_id, source_ref="BET/resend_thermal_C.pdf", digest=digest
    )
    first_source = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/first", checksum=digest
    )
    resend_source = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/resend", checksum=digest
    )
    first = project_document_admission.admit_source_as_revision(
        conn,
        source_id=first_source["source_id"],
        document_id=document["document_id"],
        source_document_id=tech_1,
        source_version=version_1,
        revision_label="C",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("first"),
    )
    resend = project_document_admission.admit_source_as_revision(
        conn,
        source_id=resend_source["source_id"],
        document_id=document["document_id"],
        source_document_id=tech_2,
        source_version=version_2,
        revision_label="C",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("resend"),
    )

    assert resend["document_version_id"] == first["document_version_id"]
    assert resend["duplicate_content_reused"] is True
    assert len(project_documents.list_revisions(conn, document["document_id"])) == 1
    bindings = project_document_admission.list_revision_sources(conn, first["document_version_id"])
    assert {row["source_id"] for row in bindings} == {first_source["source_id"], resend_source["source_id"]}


def test_wrong_project_source_is_refused(conn) -> None:
    project_a = _id("project-a")
    project_b = _id("project-b")
    _project(conn, project_a)
    _project(conn, project_b)
    document = _logical_document(conn, project_a)
    tech, version, digest = _technical(conn, project_id=project_a, source_ref="study.pdf")
    source = _preserved_source(
        conn, project_id=project_b, raw_source_ref="upload/study", checksum=digest
    )

    with pytest.raises(project_document_admission.SourceNotAdmissible, match="different Project"):
        project_document_admission.admit_source_as_revision(
            conn,
            source_id=source["source_id"],
            document_id=document["document_id"],
            source_document_id=tech,
            source_version=version,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("wrong-project"),
        )


def test_checksum_mismatch_fails_closed(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    tech, version, _ = _technical(
        conn, project_id=project_id, source_ref="study.pdf", digest="b" * 64
    )
    source = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/study", checksum="c" * 64
    )
    with pytest.raises(project_document_admission.CaptureMismatch, match="checksum"):
        project_document_admission.admit_source_as_revision(
            conn,
            source_id=source["source_id"],
            document_id=document["document_id"],
            source_document_id=tech,
            source_version=version,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("mismatch"),
        )
    assert project_documents.list_revisions(conn, document["document_id"]) == []


def test_checksumless_source_requires_exact_reference(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    source_ref = "NAS/30_DCE/study_B.pdf"
    tech, version, _ = _technical(conn, project_id=project_id, source_ref=source_ref)
    source = _preserved_source(
        conn, project_id=project_id, raw_source_ref=source_ref, checksum=None
    )
    admitted = project_document_admission.admit_source_as_revision(
        conn,
        source_id=source["source_id"],
        document_id=document["document_id"],
        source_document_id=tech,
        source_version=version,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("exact-ref"),
    )
    assert admitted["reconciliation_basis"] == "exact_reference"


def test_checksumless_nonmatching_reference_is_refused(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    tech, version, _ = _technical(conn, project_id=project_id, source_ref="NAS/study.pdf")
    source = _preserved_source(
        conn,
        project_id=project_id,
        raw_source_ref="portal/upload/123",
        origin_external_ref="portal:123",
        checksum=None,
    )
    with pytest.raises(project_document_admission.CaptureMismatch, match="exactly matches"):
        project_document_admission.admit_source_as_revision(
            conn,
            source_id=source["source_id"],
            document_id=document["document_id"],
            source_document_id=tech,
            source_version=version,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("no-proof"),
        )


def test_unlinked_or_excluded_source_is_not_admissible(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    tech, version, digest = _technical(conn, project_id=project_id, source_ref="study.pdf")
    source_id = _source_id()
    source_intake.create_source(
        conn,
        source_id=source_id,
        source_kind="document",
        origin_system="portal-test",
        origin_external_ref="upload:1",
        raw_source_ref="upload/1",
        received_at=datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc),
        checksum=digest,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("create"),
    )
    with pytest.raises(project_document_admission.SourceNotAdmissible, match="explicitly linked"):
        project_document_admission.admit_source_as_revision(
            conn,
            source_id=source_id,
            document_id=document["document_id"],
            source_document_id=tech,
            source_version=version,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("unlinked"),
        )


def test_same_source_cannot_be_reused_for_another_admission(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    first_document = _logical_document(conn, project_id, "Étude A")
    second_document = _logical_document(conn, project_id, "Étude B")
    tech, version, digest = _technical(conn, project_id=project_id, source_ref="study.pdf")
    source = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/study", checksum=digest
    )
    project_document_admission.admit_source_as_revision(
        conn,
        source_id=source["source_id"],
        document_id=first_document["document_id"],
        source_document_id=tech,
        source_version=version,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("first"),
    )
    with pytest.raises(project_document_admission.SourceAlreadyAdmitted):
        project_document_admission.admit_source_as_revision(
            conn,
            source_id=source["source_id"],
            document_id=second_document["document_id"],
            source_document_id=tech,
            source_version=version,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("second"),
        )


def test_admission_is_idempotent_and_conflicting_key_reuse_is_refused(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    tech, version, digest = _technical(conn, project_id=project_id, source_ref="study.pdf")
    source = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/study", checksum=digest
    )
    key = _id("admit")
    kwargs = dict(
        source_id=source["source_id"],
        document_id=document["document_id"],
        source_document_id=tech,
        source_version=version,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=key,
    )
    first = project_document_admission.admit_source_as_revision(conn, **kwargs)
    replay = project_document_admission.admit_source_as_revision(conn, **kwargs)
    assert replay == first

    with pytest.raises(project_document_admission.AdmissionIdempotencyConflict):
        project_document_admission.admit_source_as_revision(
            conn,
            **{**kwargs, "revision_label": "B"},
        )


def test_binding_history_is_append_only(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    document = _logical_document(conn, project_id)
    tech, version, digest = _technical(conn, project_id=project_id, source_ref="study.pdf")
    source = _preserved_source(
        conn, project_id=project_id, raw_source_ref="upload/study", checksum=digest
    )
    result = project_document_admission.admit_source_as_revision(
        conn,
        source_id=source["source_id"],
        document_id=document["document_id"],
        source_document_id=tech,
        source_version=version,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("admit"),
    )
    conn.commit()
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            "UPDATE doc_document_version_sources SET admitted_by = 'rewritten' WHERE source_id = %s",
            (source["source_id"],),
        )
    conn.rollback()
    assert project_documents.get_revision(conn, result["document_version_id"])["version_id"] == result["document_version_id"]


def test_hermes_direct_admission_is_refused(conn) -> None:
    with pytest.raises(project_document_admission.GovernanceGateRequired):
        project_document_admission.admit_source_as_revision(
            conn,
            source_id=_source_id(),
            document_id=_id("document"),
            source_document_id=_id("source-document"),
            source_version=1,
            actor="hermes",
            actor_kind="hermes",
            idempotency_key=_id("hermes"),
        )