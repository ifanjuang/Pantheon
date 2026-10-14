"""Bounded Agency Data owner for hierarchical Category classification.

Category is a logical classification/navigation record. CategoryAssignment is
an explicit N:N link to an existing owner record. Neither concept transfers
ownership, changes lifecycle status, establishes Evidence, or authorizes work.

The Tag Registry remains a separate transversal vocabulary. Semantic governed
relations remain owned by ``agency_entity_relations``.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import agency_data, project_documents, store, work_issues


MIGRATION = Path(__file__).resolve().parent / "sql" / "034_category_classification.sql"
SUPPORTED_ENTITY_TYPES = {"project", "information", "document", "knowledge", "work_issue"}
ACTOR_KINDS = {"human", "system"}
CATEGORY_MUTABLE_FIELDS = {"title", "description", "parent_category_id", "applies_to", "sort_order"}
AUTHORITY = {
    "is_authorization": False,
    "is_approval": False,
    "is_evidence": False,
    "is_lifecycle_status": False,
    "transfers_ownership": False,
    "is_semantic_entity_relation": False,
}


class AgencyClassificationError(ValueError):
    """Base refusal for Category classification operations."""


class CategoryNotFound(AgencyClassificationError):
    pass


class CategoryAssignmentNotFound(AgencyClassificationError):
    pass


class StaleCategoryWrite(AgencyClassificationError):
    pass


class StaleCategoryAssignmentWrite(AgencyClassificationError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    """Connect with the existing owners required by Category endpoints."""
    conn = store.connect(dsn)
    conn.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(project_documents.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _with_boundary(row: dict[str, Any]) -> dict[str, Any]:
    result = _jsonable(dict(row))
    result["owner_system"] = "postgres"
    result["authority"] = dict(AUTHORITY)
    return result


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AgencyClassificationError(f"{field} is required")
    return text


def _optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_actor(actor: str, actor_kind: str) -> tuple[str, str]:
    actor = _required(actor, "actor")
    actor_kind = _required(actor_kind, "actor_kind")
    if actor_kind not in ACTOR_KINDS:
        raise AgencyClassificationError(
            "Category persistence accepts human or system actors; Hermes may suggest classification but not persist it directly"
        )
    return actor, actor_kind


def _normalize_applies_to(values: list[str] | tuple[str, ...]) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise AgencyClassificationError("applies_to must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value:
            continue
        if value not in SUPPORTED_ENTITY_TYPES:
            raise AgencyClassificationError(f"unsupported Category entity type: {value}")
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    if not normalized:
        raise AgencyClassificationError("applies_to requires at least one supported entity type")
    return normalized


def _category_row(conn: psycopg.Connection, category_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM agency_categories WHERE category_id = %s{suffix}",
            (category_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise CategoryNotFound(f"unknown Category: {category_id}")
    return dict(row)


def _assignment_row(conn: psycopg.Connection, assignment_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM agency_category_assignments WHERE assignment_id = %s{suffix}",
            (assignment_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise CategoryAssignmentNotFound(f"unknown CategoryAssignment: {assignment_id}")
    return dict(row)


def get_category(conn: psycopg.Connection, category_id: str) -> dict:
    return _with_boundary(_category_row(conn, category_id))


def list_categories(conn: psycopg.Connection, *, include_archived: bool = False) -> list[dict]:
    archived_clause = "" if include_archived else "WHERE archived_at IS NULL"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT * FROM agency_categories
            {archived_clause}
            ORDER BY sort_order, lower(title), category_id
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_with_boundary(row) for row in rows]


def list_root_categories(conn: psycopg.Connection, *, include_archived: bool = False) -> list[dict]:
    archived_clause = "" if include_archived else "AND archived_at IS NULL"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT * FROM agency_categories
             WHERE parent_category_id IS NULL
               {archived_clause}
             ORDER BY sort_order, lower(title), category_id
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_with_boundary(row) for row in rows]


def list_child_categories(
    conn: psycopg.Connection,
    category_id: str,
    *,
    include_archived: bool = False,
) -> list[dict]:
    _category_row(conn, category_id)
    archived_clause = "" if include_archived else "AND archived_at IS NULL"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT * FROM agency_categories
             WHERE parent_category_id = %s
               {archived_clause}
             ORDER BY sort_order, lower(title), category_id
            """,
            (category_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_with_boundary(row) for row in rows]


def list_category_assignments(
    conn: psycopg.Connection,
    category_id: str,
    *,
    include_retired: bool = False,
) -> list[dict]:
    _category_row(conn, category_id)
    retired_clause = "" if include_retired else "AND retired_at IS NULL"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT * FROM agency_category_assignments
             WHERE category_id = %s
               {retired_clause}
             ORDER BY assigned_at, assignment_id
            """,
            (category_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_with_boundary(row) for row in rows]


def list_entity_category_assignments(
    conn: psycopg.Connection,
    *,
    entity_type: str,
    entity_id: str,
    include_retired: bool = False,
) -> list[dict]:
    entity_type = _required(entity_type, "entity_type")
    entity_id = _required(entity_id, "entity_id")
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise AgencyClassificationError(f"unsupported Category entity type: {entity_type}")
    retired_clause = "" if include_retired else "AND a.retired_at IS NULL"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT a.*, c.title AS category_title,
                   c.parent_category_id, c.sort_order AS category_sort_order,
                   c.archived_at AS category_archived_at
              FROM agency_category_assignments a
              JOIN agency_categories c ON c.category_id = a.category_id
             WHERE a.entity_type = %s
               AND a.entity_id = %s
               {retired_clause}
             ORDER BY c.sort_order, lower(c.title), a.assigned_at, a.assignment_id
            """,
            (entity_type, entity_id),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_with_boundary(row) for row in rows]


def get_category_collection(conn: psycopg.Connection, category_id: str) -> dict:
    """Read the logical Collection inputs without projecting Cockpit Cards here."""
    return {
        "category": get_category(conn, category_id),
        "child_categories": list_child_categories(conn, category_id),
        "assignments": list_category_assignments(conn, category_id),
        "collection_is_projection_input": True,
        "classification_is_not_authorization": True,
    }


def create_category(
    conn: psycopg.Connection,
    *,
    category_id: str,
    title: str,
    applies_to: list[str],
    actor: str,
    actor_kind: str = "human",
    description: str = "",
    parent_category_id: str | None = None,
    sort_order: int = 0,
) -> dict:
    actor, _actor_kind = _validate_actor(actor, actor_kind)
    category_id = _required(category_id, "category_id")
    title = _required(title, "title")
    parent_category_id = _optional(parent_category_id)
    normalized_applies_to = _normalize_applies_to(applies_to)
    if int(sort_order) < 0:
        raise AgencyClassificationError("sort_order must be non-negative")

    with conn.transaction():
        conn.execute(
            """
            INSERT INTO agency_categories (
                category_id, title, description, parent_category_id, applies_to,
                sort_order, created_by, updated_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                category_id,
                title,
                str(description or ""),
                parent_category_id,
                Jsonb(normalized_applies_to),
                int(sort_order),
                actor,
                actor,
            ),
        )
        row = _category_row(conn, category_id)
    return _with_boundary(row)


def update_category(
    conn: psycopg.Connection,
    *,
    category_id: str,
    changes: dict[str, Any],
    actor: str,
    expected_revision: int,
    actor_kind: str = "human",
) -> dict:
    actor, _actor_kind = _validate_actor(actor, actor_kind)
    if not isinstance(changes, dict) or not changes:
        raise AgencyClassificationError("Category update requires at least one change")
    unknown = set(changes) - CATEGORY_MUTABLE_FIELDS
    if unknown:
        raise AgencyClassificationError(
            f"unsupported Category field(s): {', '.join(sorted(unknown))}"
        )

    normalized = dict(changes)
    if "title" in normalized:
        normalized["title"] = _required(normalized["title"], "title")
    if "description" in normalized:
        normalized["description"] = str(normalized["description"] or "")
    if "parent_category_id" in normalized:
        normalized["parent_category_id"] = _optional(normalized["parent_category_id"])
    if "applies_to" in normalized:
        normalized["applies_to"] = _normalize_applies_to(normalized["applies_to"])
    if "sort_order" in normalized:
        normalized["sort_order"] = int(normalized["sort_order"])
        if normalized["sort_order"] < 0:
            raise AgencyClassificationError("sort_order must be non-negative")

    with conn.transaction():
        current = _category_row(conn, category_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleCategoryWrite(
                f"stale Category revision: expected {expected_revision}, current {current['revision']}"
            )
        assignments: list[str] = []
        params: list[Any] = []
        for field in sorted(normalized):
            assignments.append(f"{field} = %s")
            value = normalized[field]
            params.append(Jsonb(value) if field == "applies_to" else value)
        assignments.extend(
            ["updated_by = %s", "updated_at = clock_timestamp()", "revision = revision + 1"]
        )
        params.extend([actor, category_id])
        conn.execute(
            f"UPDATE agency_categories SET {', '.join(assignments)} WHERE category_id = %s",
            tuple(params),
        )
        row = _category_row(conn, category_id)
    return _with_boundary(row)


def archive_category(
    conn: psycopg.Connection,
    *,
    category_id: str,
    actor: str,
    expected_revision: int,
    actor_kind: str = "human",
) -> dict:
    actor, _actor_kind = _validate_actor(actor, actor_kind)
    with conn.transaction():
        current = _category_row(conn, category_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleCategoryWrite(
                f"stale Category revision: expected {expected_revision}, current {current['revision']}"
            )
        if current["archived_at"] is not None:
            raise AgencyClassificationError("Category is already archived")
        conn.execute(
            """
            UPDATE agency_categories
               SET archived_at = clock_timestamp(),
                   updated_by = %s,
                   updated_at = clock_timestamp(),
                   revision = revision + 1
             WHERE category_id = %s
            """,
            (actor, category_id),
        )
        row = _category_row(conn, category_id)
    return _with_boundary(row)


def assign_category(
    conn: psycopg.Connection,
    *,
    assignment_id: str,
    category_id: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    actor_kind: str = "human",
    rationale: str | None = None,
) -> dict:
    actor, _actor_kind = _validate_actor(actor, actor_kind)
    assignment_id = _required(assignment_id, "assignment_id")
    category_id = _required(category_id, "category_id")
    entity_type = _required(entity_type, "entity_type")
    entity_id = _required(entity_id, "entity_id")
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise AgencyClassificationError(f"unsupported Category entity type: {entity_type}")

    with conn.transaction():
        conn.execute(
            """
            INSERT INTO agency_category_assignments (
                assignment_id, category_id, entity_type, entity_id,
                assigned_by, rationale
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                assignment_id,
                category_id,
                entity_type,
                entity_id,
                actor,
                _optional(rationale),
            ),
        )
        row = _assignment_row(conn, assignment_id)
    return _with_boundary(row)


def retire_category_assignment(
    conn: psycopg.Connection,
    *,
    assignment_id: str,
    actor: str,
    expected_revision: int,
    actor_kind: str = "human",
) -> dict:
    actor, _actor_kind = _validate_actor(actor, actor_kind)
    with conn.transaction():
        current = _assignment_row(conn, assignment_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleCategoryAssignmentWrite(
                "stale CategoryAssignment revision: "
                f"expected {expected_revision}, current {current['revision']}"
            )
        if current["retired_at"] is not None:
            raise AgencyClassificationError("CategoryAssignment is already retired")
        conn.execute(
            """
            UPDATE agency_category_assignments
               SET retired_at = clock_timestamp(),
                   retired_by = %s,
                   revision = revision + 1
             WHERE assignment_id = %s
            """,
            (actor, assignment_id),
        )
        row = _assignment_row(conn, assignment_id)
    return _with_boundary(row)
