"""PostgreSQL acceptance tests for logical Project Document revision lineage."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from mvp_vertical import project_documents


@pytest.fixture
def conn():
    try:
        connection = project_documents.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_events, doc_document_versions, doc_documents, "
        "source_documents RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _technical_source(
    conn,
    *,
    project_id: str,
    source_ref: str,
    source_digest: str | None = None,
    technical_version: int = 1,
) -> tuple[str, int, str]:
    document_id = _id("source-document")
    digest = source_digest or uuid.uuid4().hex * 2
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
        ) VALUES (%s, %s, %s, %s, 'application/pdf', 1234)
        """,
        (document_id, technical_version, source_ref, digest),
    )
    conn.commit()
    return document_id, technical_version, digest


def _logical_document(conn, project_id: str = "project-alpha") -> dict:
    return project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id=project_id,
        document_type="ETUDE",
        title="Étude structure",
        discipline_code="STRUCTURE",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("create"),
    )


def test_two_different_source_refs_form_one_professional_revision_lineage(conn) -> None:
    document = _logical_document(conn)
    source_b, version_b, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="30_DCE/ETUDE_STRUCTURE_B.pdf",
    )
    source_c, version_c, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="30_DCE/ETUDE_STRUCTURE_C.pdf",
    )
    base_time = datetime(2026, 8, 8, 8, 0, tzinfo=timezone.utc)

    linked_b = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_b,
        source_version=version_b,
        revision_label="B",
        received_at=base_time,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-b"),
    )
    linked_c = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_c,
        source_version=version_c,
        revision_label="C",
        supersedes_version_id=linked_b["version_id"],
        received_at=base_time + timedelta(hours=1),
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-c"),
    )

    assert linked_b["version_seq"] == 1
    assert linked_c["version_seq"] == 2
    assert linked_c["supersedes_version_id"] == linked_b["version_id"]
    assert linked_b["source_document_id"] != linked_c["source_document_id"]
    assert [item["revision_label"] for item in project_documents.list_revisions(conn, document["document_id"])] == ["B", "C"]

    latest = project_documents.resolve_latest_received(conn, document["document_id"])
    assert latest is not None
    assert latest["purpose"] == "latest_received"
    assert latest["version"]["version_id"] == linked_c["version_id"]
    assert latest["authority"]["changes_current_authority"] is False


def test_revision_label_never_controls_latest_received_order(conn) -> None:
    document = _logical_document(conn)
    source_z, tech_z, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="study_Z.pdf",
    )
    source_a, tech_a, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="study_A.pdf",
    )
    base_time = datetime(2026, 8, 8, 8, 0, tzinfo=timezone.utc)
    first = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_z,
        source_version=tech_z,
        revision_label="Z",
        received_at=base_time,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("z"),
    )
    second = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_a,
        source_version=tech_a,
        revision_label="A",
        supersedes_version_id=first["version_id"],
        received_at=base_time + timedelta(days=1),
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("a"),
    )

    latest = project_documents.resolve_latest_received(conn, document["document_id"])
    assert latest is not None
    assert latest["version"]["version_id"] == second["version_id"]
    assert latest["version"]["revision_label"] == "A"


def test_exact_duplicate_digest_does_not_create_false_professional_revision(conn) -> None:
    document = _logical_document(conn)
    digest = "a" * 64
    first_source, first_tech, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="study_B.pdf",
        source_digest=digest,
    )
    duplicate_source, duplicate_tech, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="copy/study_B.pdf",
        source_digest=digest,
    )
    first = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=first_source,
        source_version=first_tech,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("first"),
    )
    duplicate = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=duplicate_source,
        source_version=duplicate_tech,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("duplicate"),
    )

    assert duplicate["version_id"] == first["version_id"]
    assert duplicate["duplicate_reused"] is True
    assert len(project_documents.list_revisions(conn, document["document_id"])) == 1


def test_duplicate_digest_with_different_professional_metadata_is_refused(conn) -> None:
    document = _logical_document(conn)
    digest = "b" * 64
    source_1, tech_1, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="study_B.pdf",
        source_digest=digest,
    )
    source_2, tech_2, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="study_C.pdf",
        source_digest=digest,
    )
    project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_1,
        source_version=tech_1,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("b"),
    )

    with pytest.raises(project_documents.DuplicateCaptureConflict):
        project_documents.link_revision(
            conn,
            document_id=document["document_id"],
            source_document_id=source_2,
            source_version=tech_2,
            revision_label="C",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("c"),
        )


def test_exact_technical_source_version_is_required(conn) -> None:
    document = _logical_document(conn)
    source, _, _ = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="study_B.pdf",
    )
    with pytest.raises(project_documents.SourceVersionNotFound):
        project_documents.link_revision(
            conn,
            document_id=document["document_id"],
            source_document_id=source,
            source_version=2,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("missing"),
        )


def test_cross_project_source_version_is_refused(conn) -> None:
    document = _logical_document(conn, "project-alpha")
    source, technical_version, _ = _technical_source(
        conn,
        project_id="project-beta",
        source_ref="study_B.pdf",
    )
    with pytest.raises(project_documents.CrossProjectSource):
        project_documents.link_revision(
            conn,
            document_id=document["document_id"],
            source_document_id=source,
            source_version=technical_version,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("cross-project"),
        )


def test_supersession_must_stay_inside_one_logical_document(conn) -> None:
    first_document = _logical_document(conn, "project-alpha")
    second_document = _logical_document(conn, "project-alpha")
    first_source, first_tech, _ = _technical_source(
        conn,
        project_id="project-alpha",
        source_ref="first_A.pdf",
    )
    second_source, second_tech, _ = _technical_source(
        conn,
        project_id="project-alpha",
        source_ref="second_A.pdf",
    )
    foreign_source, foreign_tech, _ = _technical_source(
        conn,
        project_id="project-alpha",
        source_ref="first_B.pdf",
    )
    first_revision = project_documents.link_revision(
        conn,
        document_id=first_document["document_id"],
        source_document_id=first_source,
        source_version=first_tech,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("first-a"),
    )
    other_revision = project_documents.link_revision(
        conn,
        document_id=second_document["document_id"],
        source_document_id=second_source,
        source_version=second_tech,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("second-a"),
    )

    with pytest.raises(project_documents.SupersessionConflict, match="same document"):
        project_documents.link_revision(
            conn,
            document_id=first_document["document_id"],
            source_document_id=foreign_source,
            source_version=foreign_tech,
            revision_label="B",
            supersedes_version_id=other_revision["version_id"],
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("cross-doc-supersede"),
        )
    assert project_documents.get_revision(conn, first_revision["version_id"])["revision_label"] == "A"


def test_declared_supersession_does_not_create_a_branch(conn) -> None:
    document = _logical_document(conn)
    sources = [
        _technical_source(
            conn,
            project_id=document["parent_project_id"],
            source_ref=f"study_{label}.pdf",
        )
        for label in ("A", "B", "C")
    ]
    revision_a = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=sources[0][0],
        source_version=sources[0][1],
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("a"),
    )
    project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=sources[1][0],
        source_version=sources[1][1],
        revision_label="B",
        supersedes_version_id=revision_a["version_id"],
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("b"),
    )

    with pytest.raises(project_documents.SupersessionConflict, match="already has a successor"):
        project_documents.link_revision(
            conn,
            document_id=document["document_id"],
            source_document_id=sources[2][0],
            source_version=sources[2][1],
            revision_label="C",
            supersedes_version_id=revision_a["version_id"],
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("c"),
        )


def test_create_and_link_are_idempotent(conn) -> None:
    create_key = _id("create")
    created = project_documents.create_document(
        conn,
        parent_project_id="project-alpha",
        document_type="ETUDE",
        title="Étude thermique",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=create_key,
    )
    create_replay = project_documents.create_document(
        conn,
        parent_project_id="project-alpha",
        document_type="ETUDE",
        title="Étude thermique",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=create_key,
    )
    assert create_replay == created

    source, technical_version, _ = _technical_source(
        conn,
        project_id="project-alpha",
        source_ref="thermal_A.pdf",
    )
    link_key = _id("link")
    linked = project_documents.link_revision(
        conn,
        document_id=created["document_id"],
        source_document_id=source,
        source_version=technical_version,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=link_key,
    )
    replayed = project_documents.link_revision(
        conn,
        document_id=created["document_id"],
        source_document_id=source,
        source_version=technical_version,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=link_key,
    )
    assert replayed == linked
    event_count = conn.execute(
        "SELECT count(*) FROM doc_document_events WHERE document_id = %s",
        (created["document_id"],),
    ).fetchone()[0]
    assert event_count == 2


def test_idempotency_key_cannot_be_reused_for_another_payload(conn) -> None:
    key = _id("create")
    project_documents.create_document(
        conn,
        parent_project_id="project-alpha",
        document_type="ETUDE",
        title="Étude A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=key,
    )
    with pytest.raises(project_documents.IdempotencyConflict):
        project_documents.create_document(
            conn,
            parent_project_id="project-alpha",
            document_type="ETUDE",
            title="Étude B",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=key,
        )


def test_events_are_append_only(conn) -> None:
    document = _logical_document(conn)
    event_id = conn.execute(
        "SELECT event_id FROM doc_document_events WHERE document_id = %s",
        (document["document_id"],),
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            "UPDATE doc_document_events SET actor = 'rewritten' WHERE event_id = %s",
            (event_id,),
        )
    conn.rollback()
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute("DELETE FROM doc_document_events WHERE event_id = %s", (event_id,))
    conn.rollback()


def test_hermes_cannot_bind_professional_document_identity_directly(conn) -> None:
    with pytest.raises(project_documents.GovernanceGateRequired):
        project_documents.create_document(
            conn,
            parent_project_id="project-alpha",
            document_type="ETUDE",
            title="Étude Hermes",
            actor="hermes",
            actor_kind="hermes",
            idempotency_key=_id("hermes"),
        )


def test_existing_technical_sources_are_not_grouped_automatically(conn) -> None:
    _technical_source(
        conn,
        project_id="project-alpha",
        source_ref="study_A.pdf",
    )
    _technical_source(
        conn,
        project_id="project-alpha",
        source_ref="study_B.pdf",
    )
    assert conn.execute("SELECT count(*) FROM doc_documents").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM doc_document_versions").fetchone()[0] == 0
