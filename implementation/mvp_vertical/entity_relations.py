"""Project-scoped relations keyed by two EntityRef values.

A relation is not canonical when it is written. It is proposed, and a human then
canonizes, rejects or retires it — every other family in this repository already
works that way, and relations were the exception. Hermes may propose, which is the
only act it is admitted to; the gate is in the schema as well as here, so a caller
that bypasses this module still cannot write a Hermes canonization.

The endpoint vocabulary is open to every project-scoped type the plan names, so a
later tranche adds a resolver arm rather than migrating a CHECK. `relation_type`
stays closed on the four canonical meanings — generic in shape, closed in meaning.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .entity_ref import EntityRef, EntityRefError


MIGRATION = Path(__file__).resolve().parent / "sql" / "015_entity_relations.sql"
RELATION_TYPES = {"responds_to", "relies_on", "supersedes", "contradicts"}
# Shape, not support: an endpoint whose owner table does not exist yet is refused
# by the resolver in 015_entity_relations.sql, with the type named. Keeping one
# enforcement point beats keeping two in sync.
ADMITTED_ENTITY_TYPES = {
    "project", "information", "decision", "person", "organization", "apu_object",
}
PROPOSAL_ACTOR_KINDS = {"human", "hermes"}


class EntityRelationError(ValueError):
    pass


class EntityRelationNotFound(EntityRelationError):
    pass


class EntityRelationConflict(EntityRelationError):
    pass


class EntityRelationGateRequired(EntityRelationError):
    pass


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: dict[str, Any]) -> str:
    rendered = json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _actor(actor: str, actor_kind: str, *, proposing: bool = False) -> str:
    """Normalize the actor and apply the gate for the act being performed.

    Proposing admits Hermes. Canonizing, rejecting and retiring do not: those are
    the acts that make a relation true, and they stay human.
    """
    normalized = str(actor or "").strip()
    if not normalized:
        raise EntityRelationError("actor is required")
    allowed = PROPOSAL_ACTOR_KINDS if proposing else {"human"}
    if actor_kind not in allowed:
        raise EntityRelationGateRequired(
            "a Hermes actor may propose an Entity relation and nothing else"
            if proposing
            else "deciding an Entity relation requires an explicit human action"
        )
    return normalized


def _entity_ref(value: dict[str, Any], label: str) -> EntityRef:
    try:
        ref = EntityRef.from_mapping(value, label=label)
    except EntityRefError as exc:
        raise EntityRelationError(str(exc)) from exc
    if ref.entity_type not in ADMITTED_ENTITY_TYPES:
        raise EntityRelationError(
            f"{label}.entity_type must be one of {sorted(ADMITTED_ENTITY_TYPES)}"
        )
    return ref


def _row(conn: psycopg.Connection, relation_id: str, *, lock: bool = False) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM agency_entity_relations WHERE relation_id = %s{suffix}",
            (relation_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise EntityRelationNotFound(f"unknown Entity relation: {relation_id}")
    return dict(row)


def _project(row: dict[str, Any]) -> dict[str, Any]:
    value = _jsonable(dict(row))
    return {
        "relation_id": value["relation_id"],
        "project_ref": value["project_id"],
        "from": {
            "entity_type": value["from_entity_type"],
            "entity_id": value["from_entity_id"],
        },
        "relation_type": value["relation_type"],
        "to": {
            "entity_type": value["to_entity_type"],
            "entity_id": value["to_entity_id"],
        },
        "rationale": value.get("rationale"),
        "source_refs": list(value.get("source_refs") or []),
        "status": value["status"],
        "revision": value["revision"],
        "created_by": value["created_by"],
        "created_at": value["created_at"],
        "retired_at": value.get("retired_at"),
        "retired_by": value.get("retired_by"),
    }


def get_relation(conn: psycopg.Connection, relation_id: str) -> dict[str, Any]:
    return _project(_row(conn, relation_id))


def list_project_relations(
    conn: psycopg.Connection,
    *,
    project_id: str,
    include_retired: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 500:
        raise EntityRelationError("limit must be between 1 and 500")
    # "not retired" now means "not closed": a rejected proposal is closed too, and
    # listing it beside open relations would present a refused edge as a live one.
    retired_clause = "" if include_retired else " AND status IN ('proposed', 'canonical')"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_entity_relations WHERE project_id = %s"
            f"{retired_clause} ORDER BY created_at, relation_id LIMIT %s",
            (project_id, limit),
        )
        rows = cur.fetchall()
    return [_project(dict(row)) for row in rows]


def list_entity_relations(
    conn: psycopg.Connection,
    *,
    entity: dict[str, Any],
    include_retired: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    ref = _entity_ref(entity, "entity")
    if limit < 1 or limit > 500:
        raise EntityRelationError("limit must be between 1 and 500")
    # "not retired" now means "not closed": a rejected proposal is closed too, and
    # listing it beside open relations would present a refused edge as a live one.
    retired_clause = "" if include_retired else " AND status IN ('proposed', 'canonical')"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_entity_relations WHERE "
            "((from_entity_type = %s AND from_entity_id = %s) OR "
            " (to_entity_type = %s AND to_entity_id = %s))"
            f"{retired_clause} ORDER BY created_at, relation_id LIMIT %s",
            (ref.entity_type, ref.entity_id, ref.entity_type, ref.entity_id, limit),
        )
        rows = cur.fetchall()
    return [_project(dict(row)) for row in rows]


def _event_replay(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    relation_id: str,
    payload_digest: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT relation_id, payload_digest, result_snapshot "
            "FROM agency_entity_relation_events WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["relation_id"] != relation_id or row["payload_digest"] != payload_digest:
        raise EntityRelationConflict(
            "Entity relation idempotency key belongs to another effect"
        )
    return _jsonable(dict(row["result_snapshot"]))


def _record_event(
    conn: psycopg.Connection,
    *,
    relation_id: str,
    event_type: str,
    actor: str,
    idempotency_key: str,
    actor_kind: str = "human",
    payload_digest: str,
    payload: dict[str, Any],
    snapshot: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO agency_entity_relation_events (
            event_id, relation_id, event_type, actor, actor_kind,
            idempotency_key, payload_digest, payload, result_snapshot
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            f"entity-relation-event-{uuid.uuid4().hex}",
            relation_id,
            event_type,
            actor,
            actor_kind,
            idempotency_key,
            payload_digest,
            Jsonb(payload),
            Jsonb(snapshot),
        ),
    )


def propose_relation(
    conn: psycopg.Connection,
    *,
    relation_id: str,
    project_id: str,
    from_ref: dict[str, Any],
    to_ref: dict[str, Any],
    relation_type: str,
    rationale: str | None,
    source_refs: list[str] | None,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
) -> dict[str, Any]:
    normalized_actor = _actor(actor, actor_kind, proposing=True)
    if not relation_id.strip() or not project_id.strip():
        raise EntityRelationError("relation_id and project_id are required")
    if relation_type not in RELATION_TYPES:
        raise EntityRelationError("unsupported Entity relation type")
    origin = _entity_ref(from_ref, "from")
    target = _entity_ref(to_ref, "to")
    if origin.key == target.key:
        raise EntityRelationError("Entity relation cannot target itself")
    normalized_sources = list(dict.fromkeys(str(value).strip() for value in source_refs or [] if str(value).strip()))
    payload = {
        "operation": "propose_relation",
        "relation_id": relation_id,
        "project_id": project_id,
        "from": origin.as_dict(),
        "to": target.as_dict(),
        "relation_type": relation_type,
        "rationale": rationale,
        "source_refs": normalized_sources,
        "actor": normalized_actor,
    }
    payload_digest = _digest(payload)
    with conn.transaction():
        replay = _event_replay(
            conn,
            idempotency_key=idempotency_key,
            relation_id=relation_id,
            payload_digest=payload_digest,
        )
        if replay is not None:
            return replay
        try:
            conn.execute(
                """
                INSERT INTO agency_entity_relations (
                    relation_id, project_id,
                    from_entity_type, from_entity_id,
                    to_entity_type, to_entity_id,
                    relation_type, rationale, source_refs, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    relation_id,
                    project_id,
                    origin.entity_type,
                    origin.entity_id,
                    target.entity_type,
                    target.entity_id,
                    relation_type,
                    rationale,
                    Jsonb(normalized_sources),
                    normalized_actor,
                ),
            )
        except psycopg.errors.UniqueViolation as exc:
            raise EntityRelationConflict(
                "an open Entity relation already carries this edge"
            ) from exc
        snapshot = get_relation(conn, relation_id)
        _record_event(
            conn,
            relation_id=relation_id,
            event_type="relation_proposed",
            actor=normalized_actor,
            actor_kind=actor_kind,
            idempotency_key=idempotency_key,
            payload_digest=payload_digest,
            payload=payload,
            snapshot=snapshot,
        )
        return snapshot


def _decide(
    conn: psycopg.Connection,
    *,
    relation_id: str,
    operation: str,
    event_type: str,
    from_status: str,
    to_status: str,
    closes: bool,
    expected_revision: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """One human decision on one relation.

    Canonizing, rejecting and retiring differ only in which transition they make
    and whether they close the relation. Writing them once keeps the optimistic
    lock, the replay check and the audit record identical across all three, which
    is what a reader of the history is entitled to assume.
    """
    normalized_actor = _actor(actor, actor_kind)
    payload = {
        "operation": operation,
        "relation_id": relation_id,
        "expected_revision": expected_revision,
        "actor": normalized_actor,
    }
    payload_digest = _digest(payload)
    with conn.transaction():
        replay = _event_replay(
            conn,
            idempotency_key=idempotency_key,
            relation_id=relation_id,
            payload_digest=payload_digest,
        )
        if replay is not None:
            return replay
        current = _row(conn, relation_id, lock=True)
        if current["revision"] != expected_revision:
            raise EntityRelationConflict(
                f"stale Entity relation revision: expected {expected_revision}, "
                f"current {current['revision']}"
            )
        if current["status"] != from_status:
            raise EntityRelationConflict(
                f"Entity relation is {current['status']}, not {from_status}"
            )
        if closes:
            conn.execute(
                "UPDATE agency_entity_relations "
                "   SET status = %s, retired_at = clock_timestamp(), retired_by = %s, "
                "       revision = revision + 1 "
                " WHERE relation_id = %s",
                (to_status, normalized_actor, relation_id),
            )
        else:
            conn.execute(
                "UPDATE agency_entity_relations "
                "   SET status = %s, revision = revision + 1 "
                " WHERE relation_id = %s",
                (to_status, relation_id),
            )
        snapshot = get_relation(conn, relation_id)
        _record_event(
            conn,
            relation_id=relation_id,
            event_type=event_type,
            actor=normalized_actor,
            idempotency_key=idempotency_key,
            payload_digest=payload_digest,
            payload=payload,
            snapshot=snapshot,
        )
        return snapshot


def canonize_relation(
    conn: psycopg.Connection,
    *,
    relation_id: str,
    expected_revision: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """A human makes a proposed relation true. Hermes cannot reach this."""
    return _decide(
        conn,
        relation_id=relation_id,
        operation="canonize_relation",
        event_type="relation_canonized",
        from_status="proposed",
        to_status="canonical",
        closes=False,
        expected_revision=expected_revision,
        actor=actor,
        actor_kind=actor_kind,
        idempotency_key=idempotency_key,
    )


def reject_relation(
    conn: psycopg.Connection,
    *,
    relation_id: str,
    expected_revision: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """A human refuses a proposal. It closes, and the edge is free again."""
    return _decide(
        conn,
        relation_id=relation_id,
        operation="reject_relation",
        event_type="relation_rejected",
        from_status="proposed",
        to_status="rejected",
        closes=True,
        expected_revision=expected_revision,
        actor=actor,
        actor_kind=actor_kind,
        idempotency_key=idempotency_key,
    )


def retire_relation(
    conn: psycopg.Connection,
    *,
    relation_id: str,
    expected_revision: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """A human withdraws a relation that was canonical. Retiring is not deleting."""
    return _decide(
        conn,
        relation_id=relation_id,
        operation="retire_relation",
        event_type="relation_retired",
        from_status="canonical",
        to_status="retired",
        closes=True,
        expected_revision=expected_revision,
        actor=actor,
        actor_kind=actor_kind,
        idempotency_key=idempotency_key,
    )
