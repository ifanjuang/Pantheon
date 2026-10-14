"""PostgreSQL acceptance tests for Information-family projection metadata."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import psycopg
import pytest

from mvp_vertical import agency_data, agency_information, information_projection


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        relations = connection.execute(
            """
            SELECT
                to_regclass('agency_information_projection_metadata'),
                to_regclass('agency_information_document_links'),
                to_regclass('agency_information_projection_events')
            """
        ).fetchone()
        connection.rollback()
        if any(relation is None for relation in relations):
            information_projection.initialize(connection)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    # Feature-local tests use unique identities and one rollback-only transaction.
    # They must not TRUNCATE shared Agency Data authorities or replay schema DDL.
    connection.execute("BEGIN")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _information(conn) -> dict:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        # agency_projects.code is UNIQUE and this suite never truncates it, so a
        # literal only works while some other suite happens to clear the table
        # first. Unique per call keeps the file runnable on its own.
        code=f"TILLEUL-{uuid.uuid4().hex[:8].upper()}",
        display_name="Projet Tilleul",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    return agency_information.create_information(
        conn,
        project_id=project["project_id"],
        title="CCTP couverture",
        category="CCTP",
        source_type="native",
        source_note="Brouillon natif",
        index_label="B",
        information_date=date(2026, 8, 5),
        actor_kind="human",
    )


def _document(conn, project_id: str) -> str:
    document_id = _id("document")
    source_ref = f"upload://{document_id}"
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref,
            source_digest, media_type, byte_size, analysis_status
        ) VALUES (%s,%s,%s,%s,%s,'application/pdf',1,'ready')
        """,
        (document_id, project_id, project_id, source_ref, _id("digest")),
    )
    return document_id


def test_native_projection_reuses_existing_information_fields(conn) -> None:
    info = _information(conn)
    projection = information_projection.get_projection(conn, info["information_id"])
    assert projection["business_kind"] == "CCTP"
    assert projection["professional_index"] == "B"
    assert projection["business_date"] == "2026-08-05"
    assert projection["projection"]["backing_mode"] == "native"
    assert projection["document_authority_transferred"] is False


def test_backing_mode_is_calculated_from_document_links(conn) -> None:
    info = _information(conn)
    first = _document(conn, info["project_id"])
    second = _document(conn, info["project_id"])
    one = information_projection.add_document_link(
        conn,
        information_id=info["information_id"],
        document_id=first,
        role="primary",
        observed_version=1,
        observed_digest=None,
        expected_revision=0,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link"),
    )
    assert one["projection"]["backing_mode"] == "single_document"
    two = information_projection.add_document_link(
        conn,
        information_id=info["information_id"],
        document_id=second,
        role="supporting",
        observed_version=1,
        observed_digest=None,
        expected_revision=1,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link"),
    )
    assert two["projection"]["backing_mode"] == "multiple_documents"
    removed = information_projection.remove_document_link(
        conn,
        information_id=info["information_id"],
        document_id=first,
        expected_revision=2,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("unlink"),
    )
    assert removed["projection"]["backing_mode"] == "single_document"


def test_projection_metadata_preserves_distinct_dates_and_media(conn) -> None:
    info = _information(conn)
    updated = information_projection.update_projection_metadata(
        conn,
        information_id=info["information_id"],
        source_date=date(2026, 8, 1),
        received_at=datetime(2026, 8, 2, 9, tzinfo=timezone.utc),
        issued_at=datetime(2026, 8, 3, 10, tzinfo=timezone.utc),
        media_types=["pdf", "text", "table", "pdf"],
        contact_refs=[{"label": "BET Structure", "role": "auteur"}],
        expected_revision=0,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("metadata"),
    )
    metadata = updated["projection"]
    assert metadata["source_date"] == "2026-08-01"
    assert metadata["received_at"].startswith("2026-08-02T09:00:00")
    assert metadata["issued_at"].startswith("2026-08-03T10:00:00")
    assert metadata["media_types"] == ["pdf", "text", "table"]
    assert updated["business_date"] == "2026-08-05"


def test_unknown_normalized_contact_is_refused(conn) -> None:
    info = _information(conn)
    with pytest.raises(information_projection.InformationProjectionNotFound):
        information_projection.update_projection_metadata(
            conn,
            information_id=info["information_id"],
            source_date=None,
            received_at=None,
            issued_at=None,
            media_types=["text"],
            contact_refs=[{"label": "Inconnu", "person_id": "person-missing"}],
            expected_revision=0,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("metadata"),
        )


def test_stale_and_hermes_writes_are_refused(conn) -> None:
    info = _information(conn)
    information_projection.update_projection_metadata(
        conn,
        information_id=info["information_id"],
        source_date=None,
        received_at=None,
        issued_at=None,
        media_types=["text"],
        contact_refs=[],
        expected_revision=0,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("metadata"),
    )
    with pytest.raises(information_projection.StaleInformationProjectionWrite):
        information_projection.update_projection_metadata(
            conn,
            information_id=info["information_id"],
            source_date=None,
            received_at=None,
            issued_at=None,
            media_types=["text"],
            contact_refs=[],
            expected_revision=0,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("stale"),
        )
    with pytest.raises(information_projection.InformationProjectionGateRequired):
        information_projection.update_projection_metadata(
            conn,
            information_id=info["information_id"],
            source_date=None,
            received_at=None,
            issued_at=None,
            media_types=["text"],
            contact_refs=[],
            expected_revision=1,
            actor="hermes",
            actor_kind="hermes",  # type: ignore[arg-type]
            idempotency_key=_id("hermes"),
        )


def test_projection_events_are_append_only(conn) -> None:
    info = _information(conn)
    information_projection.update_projection_metadata(
        conn,
        information_id=info["information_id"],
        source_date=None,
        received_at=None,
        issued_at=None,
        media_types=["text"],
        contact_refs=[],
        expected_revision=0,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("metadata"),
    )
    event_id = conn.execute(
        "SELECT event_id FROM agency_information_projection_events WHERE information_id = %s",
        (info["information_id"],),
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with conn.transaction():
            conn.execute(
                "UPDATE agency_information_projection_events SET actor = 'changed' WHERE event_id = %s",
                (event_id,),
            )


def test_document_link_update_has_distinct_operation_and_event(conn) -> None:
    """add_document_link upserts, so the event must say which one happened.

    It always recorded `document_link_added`, so changing a link's role from
    primary to supporting entered the append-only history as a link creation
    that never occurred, and the modification left no trace at all.
    """
    info = _information(conn)
    document_id = _document(conn, info["project_id"])

    def events() -> list[str]:
        rows = conn.execute(
            "SELECT event_type FROM agency_information_projection_events "
            "WHERE information_id = %s ORDER BY expected_revision, event_id",
            (info["information_id"],),
        ).fetchall()
        return [row[0] for row in rows]

    created = information_projection.add_document_link(
        conn,
        information_id=info["information_id"],
        document_id=document_id,
        role="supporting",
        observed_version=1,
        observed_digest=None,
        expected_revision=0,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-create"),
    )
    assert created["document_link_operation"] == "created"
    assert events() == ["document_link_added"]

    # Same pair, different role: an update, not an addition.
    updated = information_projection.add_document_link(
        conn,
        information_id=info["information_id"],
        document_id=document_id,
        role="primary",
        observed_version=2,
        observed_digest="sha256:updated",
        expected_revision=1,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-update"),
    )
    assert updated["document_link_operation"] == "updated"
    assert events() == ["document_link_added", "document_link_updated"]

    # The upsert still applied, and no second link was created.
    refs = updated["projection"]["document_refs"]
    assert len(refs) == 1
    assert refs[0]["role"] == "primary"
    assert refs[0]["observed_version"] == 2
