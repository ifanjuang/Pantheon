"""PostgreSQL acceptance tests for canonical EntityRef relations."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import agency_data, entity_relations


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        exists = connection.execute(
            "SELECT to_regclass('public.agency_entity_relations')"
        ).fetchone()[0]
        if exists is None:
            entity_relations.ensure_schema(connection)
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.commit()
    connection.execute("BEGIN")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, label: str) -> str:
    project_id = _id("project")
    conn.execute(
        "INSERT INTO agency_projects "
        "(project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id(label), f"Projet {label}"),
    )
    return project_id


def _information(conn, project_id: str, label: str) -> str:
    information_id = _id("information")
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, status
        ) VALUES (%s, %s, %s, %s, 'note', 'human', 'test source', 'A', 'draft')
        """,
        (information_id, _id("series"), project_id, label),
    )
    return information_id


def _propose(conn, project_id: str, origin: str, target: str, *, relation_id: str | None = None,
             actor: str = "architect@example.test", actor_kind: str = "human"):
    return entity_relations.propose_relation(
        conn,
        relation_id=relation_id or _id("relation"),
        project_id=project_id,
        from_ref={"entity_type": "information", "entity_id": origin},
        to_ref={"entity_type": "information", "entity_id": target},
        relation_type="responds_to",
        rationale="Réponse explicite",
        source_refs=["source-1"],
        actor=actor,
        actor_kind=actor_kind,
        idempotency_key=_id("create-key"),
    )


def _create(conn, project_id: str, origin: str, target: str, *, relation_id: str | None = None):
    """Propose then canonize — what most of these tests mean by an existing relation."""
    relation = _propose(conn, project_id, origin, target, relation_id=relation_id)
    return entity_relations.canonize_relation(
        conn,
        relation_id=relation["relation_id"],
        expected_revision=relation["revision"],
        actor="architect@example.test",
        actor_kind="human",
        idempotency_key=_id("canonize-key"),
    )


def test_create_and_list_relation_in_one_project(conn) -> None:
    project_id = _project(conn, "same")
    origin = _information(conn, project_id, "Réponse")
    target = _information(conn, project_id, "Demande")

    relation = _create(conn, project_id, origin, target)

    assert relation["project_ref"] == project_id
    assert relation["from"] == {"entity_type": "information", "entity_id": origin}
    assert relation["to"] == {"entity_type": "information", "entity_id": target}
    assert relation["relation_type"] == "responds_to"
    assert entity_relations.list_project_relations(
        conn, project_id=project_id
    ) == [relation]


def test_cross_project_relation_is_refused_by_scope_trigger(conn) -> None:
    project_a = _project(conn, "a")
    project_b = _project(conn, "b")
    origin = _information(conn, project_a, "A")
    target = _information(conn, project_b, "B")

    with pytest.raises(psycopg.errors.RaiseException, match="different Projects"):
        _create(conn, project_a, origin, target)


def test_unknown_polymorphic_endpoint_is_refused(conn) -> None:
    project_id = _project(conn, "unknown")
    origin = _information(conn, project_id, "Known")

    with pytest.raises(psycopg.errors.RaiseException, match="unknown information EntityRef"):
        _create(conn, project_id, origin, _id("missing-information"))


def test_active_edge_is_unique_but_can_be_recreated_after_retirement(conn) -> None:
    project_id = _project(conn, "lifecycle")
    origin = _information(conn, project_id, "Origin")
    target = _information(conn, project_id, "Target")
    first = _create(conn, project_id, origin, target)

    with pytest.raises(entity_relations.EntityRelationConflict, match="already carries this edge"):
        _create(conn, project_id, origin, target)

    retired = entity_relations.retire_relation(
        conn,
        relation_id=first["relation_id"],
        # A canonized relation has already advanced once, so the retiring caller
        # holds revision 2. Hardcoding 1 encoded the two-state lifecycle.
        expected_revision=first["revision"],
        actor="architect@example.test",
        actor_kind="human",
        idempotency_key=_id("retire-key"),
    )
    assert retired["retired_at"] is not None
    assert retired["retired_by"] == "architect@example.test"

    replacement = _create(conn, project_id, origin, target)
    assert replacement["relation_id"] != first["relation_id"]


def test_relation_identity_is_immutable_and_events_are_append_only(conn) -> None:
    project_id = _project(conn, "immutable")
    origin = _information(conn, project_id, "Origin")
    target = _information(conn, project_id, "Target")
    relation = _create(conn, project_id, origin, target)

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        with conn.transaction():
            conn.execute(
                "UPDATE agency_entity_relations SET relation_type = 'contradicts' "
                "WHERE relation_id = %s",
                (relation["relation_id"],),
            )

    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with conn.transaction():
            conn.execute(
                "UPDATE agency_entity_relation_events SET actor = 'other' "
                "WHERE relation_id = %s",
                (relation["relation_id"],),
            )


def test_hermes_may_propose_but_never_decide(conn) -> None:
    """The gate moved rather than opened.

    Hermes used to be refused outright, which meant a relation could only exist
    if a human typed it and was canonical the instant it was written — the one
    family in this repository with no candidate state. Hermes may now propose;
    canonizing, rejecting and retiring remain human acts.
    """
    project_id = _project(conn, "gate")
    origin = _information(conn, project_id, "Origin")
    target = _information(conn, project_id, "Target")

    proposal = _propose(conn, project_id, origin, target, actor="hermes", actor_kind="hermes")
    assert proposal["status"] == "proposed"
    assert proposal["created_by"] == "hermes"

    for decide in (
        entity_relations.canonize_relation,
        entity_relations.reject_relation,
        entity_relations.retire_relation,
    ):
        with pytest.raises(entity_relations.EntityRelationGateRequired):
            decide(
                conn,
                relation_id=proposal["relation_id"],
                expected_revision=proposal["revision"],
                actor="hermes",
                actor_kind="hermes",
                idempotency_key=_id("gate-key"),
            )


def test_a_relation_is_not_canonical_when_it_is_written(conn) -> None:
    project_id = _project(conn, "lifecycle")
    origin = _information(conn, project_id, "Origin")
    target = _information(conn, project_id, "Target")

    proposal = _propose(conn, project_id, origin, target)
    assert proposal["status"] == "proposed"

    # A proposal is not visible as an established relation... it is open, so it
    # lists; what distinguishes it is its status, and a reader must be able to see
    # that before treating the edge as true.
    listed = entity_relations.list_project_relations(conn, project_id=project_id)
    assert [item["status"] for item in listed] == ["proposed"]

    canonical = entity_relations.canonize_relation(
        conn,
        relation_id=proposal["relation_id"],
        expected_revision=proposal["revision"],
        actor="architect@example.test",
        actor_kind="human",
        idempotency_key=_id("canonize"),
    )
    assert canonical["status"] == "canonical"
    assert canonical["revision"] == proposal["revision"] + 1

    retired = entity_relations.retire_relation(
        conn,
        relation_id=proposal["relation_id"],
        expected_revision=canonical["revision"],
        actor="architect@example.test",
        actor_kind="human",
        idempotency_key=_id("retire"),
    )
    assert retired["status"] == "retired"
    assert retired["retired_by"] == "architect@example.test"
    assert entity_relations.list_project_relations(conn, project_id=project_id) == []


def test_a_rejected_proposal_frees_the_edge(conn) -> None:
    """Uniqueness covers open relations, so a refusal must release the edge.

    Otherwise one refused proposal would permanently block the relation it
    proposed, and a human who rejected it could never assert it themselves.
    """
    project_id = _project(conn, "reject")
    origin = _information(conn, project_id, "Origin")
    target = _information(conn, project_id, "Target")

    proposal = _propose(conn, project_id, origin, target, actor="hermes", actor_kind="hermes")
    with pytest.raises(entity_relations.EntityRelationConflict):
        _propose(conn, project_id, origin, target)

    rejected = entity_relations.reject_relation(
        conn,
        relation_id=proposal["relation_id"],
        expected_revision=proposal["revision"],
        actor="architect@example.test",
        actor_kind="human",
        idempotency_key=_id("reject"),
    )
    assert rejected["status"] == "rejected"
    assert rejected["retired_by"] == "architect@example.test"

    again = _propose(conn, project_id, origin, target)
    assert again["status"] == "proposed"


def test_a_canonical_relation_cannot_be_canonized_twice(conn) -> None:
    project_id = _project(conn, "twice")
    origin = _information(conn, project_id, "Origin")
    target = _information(conn, project_id, "Target")
    relation = _create(conn, project_id, origin, target)

    with pytest.raises(entity_relations.EntityRelationConflict):
        entity_relations.canonize_relation(
            conn,
            relation_id=relation["relation_id"],
            expected_revision=relation["revision"],
            actor="architect@example.test",
            actor_kind="human",
            idempotency_key=_id("again"),
        )
