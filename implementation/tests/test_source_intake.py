"""PostgreSQL acceptance tests for generic Source intake admission."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from mvp_vertical import agency_data, source_intake


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        relations = connection.execute(
            """
            SELECT
                to_regclass('agency_sources'),
                to_regclass('agency_source_relations'),
                to_regclass('agency_source_events')
            """
        ).fetchone()
        connection.rollback()
        if any(relation is None for relation in relations):
            source_intake.initialize(connection)
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    # Feature-local tests use unique identities and one rollback-only transaction.
    # They must not TRUNCATE shared Agency Data authorities or replay schema DDL.
    #
    # The previous fixture truncated agency_projects — an authority other suites
    # own — on every test. TRUNCATE needs ACCESS EXCLUSIVE, so it blocked behind
    # any connection still holding a read lock, and a module-scoped fixture
    # elsewhere holds one for the length of its module. That turned an ordinary
    # serial run into a stall. Every identity here is already uuid-unique, so the
    # truncation bought no isolation it did not already have.
    connection.execute("BEGIN")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, code: str | None = None) -> dict:
    # agency_projects.code is UNIQUE. A fixed literal only worked while the
    # fixture truncated the table on every test; without that it collides with
    # any project another suite left behind.
    code = code or f"TILLEUL-{uuid.uuid4().hex[:8].upper()}"
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=code,
        display_name=f"Projet {code}",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )


def _source(conn, *, suffix: str = "mail") -> dict:
    return source_intake.create_source(
        conn,
        source_id=_id("source"),
        source_kind="email",
        origin_system="gmail",
        origin_external_ref=_id(suffix),
        raw_source_ref=f"gmail://messages/{_id('message')}",
        received_at=datetime.now(timezone.utc),
        declared_project_name="Maison Tilleul",
        actor="intake-user",
        actor_kind="human",
        idempotency_key=_id("source-create"),
    )


def test_source_is_preserved_without_project_or_information(conn) -> None:
    # Admitting a Source must create no Information. Asserted as a delta rather
    # than a global count of zero: the latter only held because the fixture
    # truncated a table this suite does not own.
    before = conn.execute("SELECT count(*) FROM agency_information_cards").fetchone()[0]

    source = _source(conn)

    assert source["project_link_status"] == "unassigned"
    assert source["project_id"] is None
    assert source["declared_project_name"] == "Maison Tilleul"
    assert source["revision"] == 1
    after = conn.execute("SELECT count(*) FROM agency_information_cards").fetchone()[0]
    assert after == before


def test_candidate_project_is_not_an_authoritative_link(conn) -> None:
    project = _project(conn)
    source = _source(conn)
    suggested = source_intake.suggest_projects(
        conn,
        source_id=source["source_id"],
        candidates=[
            {
                "project_ref": project["project_id"],
                "score": 0.93,
                "basis": ["declared_name_match", "sender_match"],
                "producer": "deterministic-project-matcher",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        expected_revision=1,
        actor="intake-user",
        actor_kind="human",
        idempotency_key=_id("suggest"),
    )
    assert suggested["project_link_status"] == "suggested"
    assert suggested["project_id"] is None
    assert suggested["candidate_project_refs"][0]["score"] == 0.93


def test_project_suggestion_cannot_implicitly_unlink_a_linked_source(conn) -> None:
    linked_project = _project(conn)
    candidate_project = _project(conn)
    source = _source(conn)
    linked = source_intake.link_project(
        conn,
        source_id=source["source_id"],
        project_id=linked_project["project_id"],
        expected_revision=1,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link"),
    )

    with pytest.raises(
        source_intake.SourceIntakeError,
        match="linked Source must be explicitly unlinked before project suggestions",
    ):
        source_intake.suggest_projects(
            conn,
            source_id=source["source_id"],
            candidates=[
                {
                    "project_ref": candidate_project["project_id"],
                    "score": 0.91,
                    "basis": ["declared_name_match"],
                    "producer": "deterministic-project-matcher",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            expected_revision=linked["revision"],
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("suggest-linked"),
        )

    current = source_intake.get_source(conn, source["source_id"])
    assert current["project_link_status"] == "linked"
    assert current["project_id"] == linked_project["project_id"]
    assert current["revision"] == linked["revision"]


def test_link_unlink_exclude_and_restore_are_explicit_revision_checked_actions(conn) -> None:
    project = _project(conn)
    source = _source(conn)
    linked = source_intake.link_project(
        conn,
        source_id=source["source_id"],
        project_id=project["project_id"],
        expected_revision=1,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link"),
    )
    assert linked["project_link_status"] == "linked"
    assert linked["project_id"] == project["project_id"]

    unlinked = source_intake.unlink_project(
        conn,
        source_id=source["source_id"],
        expected_revision=2,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("unlink"),
    )
    assert unlinked["project_link_status"] == "unassigned"
    assert unlinked["project_id"] is None

    excluded = source_intake.exclude_source(
        conn,
        source_id=source["source_id"],
        expected_revision=3,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("exclude"),
    )
    assert excluded["project_link_status"] == "excluded"

    restored = source_intake.restore_source(
        conn,
        source_id=source["source_id"],
        expected_revision=4,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("restore"),
    )
    assert restored["project_link_status"] == "unassigned"


def test_stale_link_is_refused(conn) -> None:
    project = _project(conn)
    source = _source(conn)
    source_intake.update_metadata(
        conn,
        source_id=source["source_id"],
        changes={"mime_type": "message/rfc822"},
        expected_revision=1,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("metadata"),
    )
    with pytest.raises(source_intake.StaleSourceWrite):
        source_intake.link_project(
            conn,
            source_id=source["source_id"],
            project_id=project["project_id"],
            expected_revision=1,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("stale-link"),
        )


def test_idempotent_create_replays_and_conflicting_payload_is_refused(conn) -> None:
    source_id = _id("source")
    key = _id("create")
    kwargs = {
        "source_id": source_id,
        "source_kind": "url",
        "origin_system": "cockpit",
        "origin_external_ref": _id("url"),
        "raw_source_ref": "https://example.test/resource",
        "received_at": datetime.now(timezone.utc),
        "actor": "reviewer",
        "actor_kind": "human",
        "idempotency_key": key,
    }
    first = source_intake.create_source(conn, **kwargs)
    replay = source_intake.create_source(conn, **kwargs)
    assert replay == first

    with pytest.raises(source_intake.SourceIdempotencyConflict):
        source_intake.create_source(conn, **{**kwargs, "raw_source_ref": "https://example.test/other"})


def test_attachments_are_independent_sources_with_contains_relation(conn) -> None:
    parent = _source(conn, suffix="parent")
    child = source_intake.create_source(
        conn,
        source_id=_id("source"),
        source_kind="document",
        origin_system="gmail",
        origin_external_ref=_id("attachment"),
        raw_source_ref=f"blob://{_id('pdf')}",
        received_at=datetime.now(timezone.utc),
        mime_type="application/pdf",
        actor="intake-user",
        actor_kind="human",
        idempotency_key=_id("child-create"),
    )
    relation = source_intake.relate_contained_source(
        conn,
        source_id=parent["source_id"],
        target_source_id=child["source_id"],
        actor="intake-user",
        actor_kind="human",
        idempotency_key=_id("contains"),
    )
    assert relation["relation_type"] == "contains"
    assert source_intake.get_source(conn, child["source_id"])["source_id"] == child["source_id"]


def test_hermes_cannot_directly_create_or_link_source(conn) -> None:
    with pytest.raises(source_intake.SourceGovernanceGateRequired):
        source_intake.create_source(
            conn,
            source_id=_id("source"),
            source_kind="text",
            origin_system="hermes",
            origin_external_ref=_id("result"),
            raw_source_ref="native://candidate",
            received_at=datetime.now(timezone.utc),
            actor="hermes",
            actor_kind="hermes",
            idempotency_key=_id("hermes-create"),
        )


def test_source_events_are_append_only(conn) -> None:
    source = _source(conn)
    event_id = conn.execute(
        "SELECT event_id FROM agency_source_events WHERE source_id = %s",
        (source["source_id"],),
    ).fetchone()[0]
    # Each refusal aborts its own savepoint, not the fixture's transaction: a
    # bare rollback here would discard the source this test just created and
    # make the second assertion pass vacuously.
    for statement in (
        "UPDATE agency_source_events SET actor = 'changed' WHERE event_id = %s",
        "DELETE FROM agency_source_events WHERE event_id = %s",
    ):
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            with conn.transaction():
                conn.execute(statement, (event_id,))

    # The event survives both refusals.
    assert conn.execute(
        "SELECT actor FROM agency_source_events WHERE event_id = %s", (event_id,)
    ).fetchone() is not None
