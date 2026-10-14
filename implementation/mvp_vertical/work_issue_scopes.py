"""Aggregate-owned EntityRef scopes for governed Work Issues.

A scope link makes one WorkIssue visible in several relevant contexts. It is not
an Information relation, does not widen a Context Pack and grants no execution
authority. Canonical WorkIssue lifecycle remains owned by ``work_issues``.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row

from . import pantheon_contracts, work_issues


MIGRATION = Path(__file__).resolve().parent / "sql" / "016_work_issue_scopes.sql"
SCHEMA = pantheon_contracts.schema_path("work_issue_scope_link")

ALLOWED_SCOPE_TYPES = frozenset(
    {
        "agency",
        "project",
        "information",
        "decision",
        "person",
        "organization",
        "apu_object",
    }
)
ALLOWED_SCOPE_ROLES = frozenset({"primary", "related"})
_STATUS_ORDER = {
    "review": 0,
    "waiting": 1,
    "open": 2,
    "in_progress": 3,
    "done": 4,
    "cancelled": 5,
}


class WorkIssueScopeError(work_issues.WorkIssueError):
    """Base refusal for WorkIssue scope operations."""


class ScopeLinkNotFound(WorkIssueScopeError):
    pass


class ScopeConflict(WorkIssueScopeError):
    pass


class ScopeOwnerUnavailable(WorkIssueScopeError):
    pass


def _event_id() -> str:
    return f"work-scope-event-{uuid.uuid4().hex}"


def _as_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _clean(mapping: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        output[key] = _as_iso(value) if isinstance(value, datetime) else value
    return output


@lru_cache(maxsize=1)
def _validator() -> jsonschema.Draft202012Validator:
    try:
        schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WorkIssueScopeError(
            f"unable to load governed WorkIssue scope schema: {exc}"
        ) from exc
    if not isinstance(schema, dict):
        raise WorkIssueScopeError("governed WorkIssue scope schema must be an object")
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def _validated_link(row: dict[str, Any]) -> dict[str, Any]:
    item = _clean(row)
    projection = {
        "scope_link_id": item["scope_link_id"],
        "issue_ref": item["issue_id"],
        "scope_ref": {
            "entity_type": item["entity_type"],
            "entity_id": item["entity_id"],
        },
        "scope_role": item["scope_role"],
        "rationale": item.get("rationale"),
        "created_by": item["created_by"],
        "created_at": item["created_at"],
        "retired_at": item.get("retired_at"),
        "retired_by": item.get("retired_by"),
    }
    try:
        _validator().validate(projection)
    except jsonschema.ValidationError as exc:
        raise WorkIssueScopeError(
            f"stored WorkIssue scope violates its governed contract: {exc}"
        ) from exc
    return projection


def _issue_locked(conn: psycopg.Connection, issue_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM work_issues WHERE issue_id = %s FOR UPDATE",
            (issue_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise work_issues.IssueNotFound(f"unknown Work Issue: {issue_id}")
    return dict(row)


def _scope_row(
    conn: psycopg.Connection,
    scope_link_id: str,
    *,
    lock: bool = False,
) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM work_issue_scope_links WHERE scope_link_id = %s{suffix}",
            (scope_link_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ScopeLinkNotFound(f"unknown WorkIssue scope link: {scope_link_id}")
    return dict(row)


def _event_replayed(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    idempotency_key: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT issue_id, event_type, payload
              FROM work_issue_scope_events
             WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return False
    if (
        row["issue_id"] != issue_id
        or row["event_type"] != event_type
        or (row["payload"] or {}) != payload
    ):
        raise ScopeConflict("idempotency key belongs to another WorkIssue scope effect")
    return True


def _insert_event(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    scope_link_id: str,
    event_type: str,
    actor: str,
    expected_version: int,
    idempotency_key: str,
    payload: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO work_issue_scope_events (
            event_id, issue_id, scope_link_id, event_type, actor,
            expected_version, resulting_version, idempotency_key, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            _event_id(),
            issue_id,
            scope_link_id,
            event_type,
            actor,
            expected_version,
            expected_version + 1,
            idempotency_key,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        ),
    )


def _bump_issue_version(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    expected_version: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE work_issues
               SET version = version + 1,
                   updated_at = clock_timestamp()
             WHERE issue_id = %s AND version = %s
            """,
            (issue_id, expected_version),
        )
        if cur.rowcount != 1:
            raise work_issues.StaleWrite(
                "WorkIssue changed before its scope effect was persisted"
            )


def _normalize_scope_input(scope: dict[str, Any]) -> dict[str, Any]:
    scope_link_id = str(scope.get("scope_link_id") or "").strip()
    entity_type = str(scope.get("entity_type") or "").strip()
    entity_id = str(scope.get("entity_id") or "").strip()
    scope_role = str(scope.get("scope_role") or "related").strip()
    rationale = scope.get("rationale")
    if not scope_link_id:
        raise WorkIssueScopeError("scope_link_id is required")
    if entity_type not in ALLOWED_SCOPE_TYPES:
        raise WorkIssueScopeError(f"unsupported WorkIssue scope type: {entity_type!r}")
    if not entity_id:
        raise WorkIssueScopeError("scope entity_id is required")
    if scope_role not in ALLOWED_SCOPE_ROLES:
        raise WorkIssueScopeError(f"unsupported WorkIssue scope role: {scope_role!r}")
    if rationale is not None:
        rationale = str(rationale).strip() or None
    return {
        "scope_link_id": scope_link_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "scope_role": scope_role,
        "rationale": rationale,
    }


def list_scope_links(
    conn: psycopg.Connection,
    issue_id: str,
    *,
    include_retired: bool = False,
) -> list[dict[str, Any]]:
    terminal_filter = "" if include_retired else "AND retired_at IS NULL"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT *
              FROM work_issue_scope_links
             WHERE issue_id = %s
               {terminal_filter}
             ORDER BY
                   CASE scope_role WHEN 'primary' THEN 0 ELSE 1 END,
                   created_at,
                   scope_link_id
            """,
            (issue_id,),
        )
        return [_validated_link(dict(row)) for row in cur.fetchall()]


def list_scope_events(
    conn: psycopg.Connection,
    issue_id: str,
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT event_id, issue_id AS issue_ref, scope_link_id AS scope_link_ref,
                   event_type, actor, expected_version, resulting_version,
                   idempotency_key, payload, occurred_at
              FROM work_issue_scope_events
             WHERE issue_id = %s
             ORDER BY occurred_at, event_id
            """,
            (issue_id,),
        )
        return [_clean(dict(row)) for row in cur.fetchall()]


def get_scoped_issue(
    conn: psycopg.Connection,
    issue_id: str,
    *,
    include_retired_scopes: bool = False,
) -> dict[str, Any]:
    aggregate = work_issues.get_issue(conn, issue_id)
    return {
        **aggregate,
        "scope_links": list_scope_links(
            conn,
            issue_id,
            include_retired=include_retired_scopes,
        ),
        "scope_events": list_scope_events(conn, issue_id),
        "scope_is_not_authorization": True,
    }


def add_scope(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    scope_link_id: str,
    entity_type: str,
    entity_id: str,
    scope_role: str,
    actor: str,
    expected_version: int,
    idempotency_key: str,
    rationale: str | None = None,
) -> dict[str, Any]:
    normalized = _normalize_scope_input(
        {
            "scope_link_id": scope_link_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "scope_role": scope_role,
            "rationale": rationale,
        }
    )
    payload = {
        "scope_link_id": normalized["scope_link_id"],
        "scope_ref": {
            "entity_type": normalized["entity_type"],
            "entity_id": normalized["entity_id"],
        },
        "scope_role": normalized["scope_role"],
        "rationale": normalized["rationale"],
    }

    with conn.transaction():
        if _event_replayed(
            conn,
            issue_id=issue_id,
            idempotency_key=idempotency_key,
            event_type="scope_linked",
            payload=payload,
        ):
            return get_scoped_issue(conn, issue_id)
        issue = _issue_locked(conn, issue_id)
        if issue["version"] != expected_version:
            raise work_issues.StaleWrite(
                f"stale WorkIssue version: expected {expected_version}, current {issue['version']}"
            )
        try:
            conn.execute(
                """
                INSERT INTO work_issue_scope_links (
                    scope_link_id, issue_id, entity_type, entity_id, scope_role,
                    rationale, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    normalized["scope_link_id"],
                    issue_id,
                    normalized["entity_type"],
                    normalized["entity_id"],
                    normalized["scope_role"],
                    normalized["rationale"],
                    actor,
                ),
            )
        except psycopg.errors.UniqueViolation as exc:
            raise ScopeConflict("an active WorkIssue scope or primary scope already exists") from exc
        except psycopg.errors.RaiseException as exc:
            message = str(exc)
            if "owner is not implemented" in message:
                raise ScopeOwnerUnavailable(message) from exc
            raise WorkIssueScopeError(message) from exc
        _bump_issue_version(
            conn,
            issue_id=issue_id,
            expected_version=expected_version,
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            scope_link_id=normalized["scope_link_id"],
            event_type="scope_linked",
            actor=actor,
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        return get_scoped_issue(conn, issue_id)


def retire_scope(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    scope_link_id: str,
    actor: str,
    expected_version: int,
    idempotency_key: str,
    rationale: str | None = None,
) -> dict[str, Any]:
    payload = {
        "scope_link_id": scope_link_id,
        "rationale": str(rationale).strip() if rationale else None,
    }
    with conn.transaction():
        if _event_replayed(
            conn,
            issue_id=issue_id,
            idempotency_key=idempotency_key,
            event_type="scope_retired",
            payload=payload,
        ):
            return get_scoped_issue(conn, issue_id, include_retired_scopes=True)
        issue = _issue_locked(conn, issue_id)
        if issue["version"] != expected_version:
            raise work_issues.StaleWrite(
                f"stale WorkIssue version: expected {expected_version}, current {issue['version']}"
            )
        link = _scope_row(conn, scope_link_id, lock=True)
        if link["issue_id"] != issue_id:
            raise ScopeConflict("scope link belongs to another WorkIssue")
        if link["retired_at"] is not None:
            raise ScopeConflict("WorkIssue scope link is already retired")
        if link["scope_role"] == "primary":
            raise ScopeConflict(
                "primary WorkIssue scope must be replaced atomically, not retired alone"
            )
        conn.execute(
            """
            UPDATE work_issue_scope_links
               SET retired_at = clock_timestamp(), retired_by = %s
             WHERE scope_link_id = %s AND retired_at IS NULL
            """,
            (actor, scope_link_id),
        )
        _bump_issue_version(
            conn,
            issue_id=issue_id,
            expected_version=expected_version,
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            scope_link_id=scope_link_id,
            event_type="scope_retired",
            actor=actor,
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        return get_scoped_issue(conn, issue_id, include_retired_scopes=True)


def replace_primary_scope(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    current_scope_link_id: str,
    replacement_scope_link_id: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    expected_version: int,
    idempotency_key: str,
    rationale: str | None = None,
) -> dict[str, Any]:
    normalized = _normalize_scope_input(
        {
            "scope_link_id": replacement_scope_link_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "scope_role": "primary",
            "rationale": rationale,
        }
    )
    payload = {
        "retired_scope_link_id": current_scope_link_id,
        "replacement_scope_link_id": replacement_scope_link_id,
        "replacement_scope_ref": {
            "entity_type": normalized["entity_type"],
            "entity_id": normalized["entity_id"],
        },
        "rationale": normalized["rationale"],
    }
    with conn.transaction():
        if _event_replayed(
            conn,
            issue_id=issue_id,
            idempotency_key=idempotency_key,
            event_type="primary_scope_replaced",
            payload=payload,
        ):
            return get_scoped_issue(conn, issue_id, include_retired_scopes=True)
        issue = _issue_locked(conn, issue_id)
        if issue["version"] != expected_version:
            raise work_issues.StaleWrite(
                f"stale WorkIssue version: expected {expected_version}, current {issue['version']}"
            )
        current = _scope_row(conn, current_scope_link_id, lock=True)
        if current["issue_id"] != issue_id or current["scope_role"] != "primary":
            raise ScopeConflict("current scope link is not this WorkIssue's active primary")
        if current["retired_at"] is not None:
            raise ScopeConflict("current primary WorkIssue scope is already retired")

        conn.execute(
            """
            UPDATE work_issue_scope_links
               SET retired_at = clock_timestamp(), retired_by = %s
             WHERE scope_link_id = %s AND retired_at IS NULL
            """,
            (actor, current_scope_link_id),
        )
        try:
            conn.execute(
                """
                INSERT INTO work_issue_scope_links (
                    scope_link_id, issue_id, entity_type, entity_id, scope_role,
                    rationale, created_by
                ) VALUES (%s, %s, %s, %s, 'primary', %s, %s)
                """,
                (
                    replacement_scope_link_id,
                    issue_id,
                    normalized["entity_type"],
                    normalized["entity_id"],
                    normalized["rationale"],
                    actor,
                ),
            )
        except psycopg.errors.RaiseException as exc:
            message = str(exc)
            if "owner is not implemented" in message:
                raise ScopeOwnerUnavailable(message) from exc
            raise WorkIssueScopeError(message) from exc
        except psycopg.errors.UniqueViolation as exc:
            raise ScopeConflict("replacement WorkIssue scope is already active") from exc

        _bump_issue_version(
            conn,
            issue_id=issue_id,
            expected_version=expected_version,
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            scope_link_id=replacement_scope_link_id,
            event_type="primary_scope_replaced",
            actor=actor,
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        return get_scoped_issue(conn, issue_id, include_retired_scopes=True)


def create_scoped_issue(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    case_ref: str,
    title: str,
    description: str,
    created_by: str,
    idempotency_key: str,
    scopes: Iterable[dict[str, Any]],
    issue_type: str = "action",
    priority: str = "normal",
    requested_effect: str = "draft",
    assigned_to: str | None = None,
    task_contract_ref: str | None = None,
    context_pack_ref: str | None = None,
) -> dict[str, Any]:
    normalized_scopes = [_normalize_scope_input(scope) for scope in scopes]
    if not normalized_scopes:
        raise WorkIssueScopeError("a scoped WorkIssue requires at least one scope")
    if sum(scope["scope_role"] == "primary" for scope in normalized_scopes) != 1:
        raise WorkIssueScopeError("a scoped WorkIssue requires exactly one primary scope")
    identities = {
        (scope["entity_type"], scope["entity_id"])
        for scope in normalized_scopes
    }
    if len(identities) != len(normalized_scopes):
        raise WorkIssueScopeError("duplicate WorkIssue scope endpoint in create request")

    with conn.transaction():
        work_issues.create_issue(
            conn,
            issue_id=issue_id,
            case_ref=case_ref,
            title=title,
            description=description,
            created_by=created_by,
            idempotency_key=idempotency_key,
            issue_type=issue_type,
            priority=priority,
            requested_effect=requested_effect,
            assigned_to=assigned_to,
            task_contract_ref=task_contract_ref,
            context_pack_ref=context_pack_ref,
        )
        current = work_issues.get_issue(conn, issue_id)["work_issue"]
        for index, scope in enumerate(normalized_scopes):
            add_scope(
                conn,
                issue_id=issue_id,
                actor=created_by,
                expected_version=current["version"],
                idempotency_key=f"{idempotency_key}:scope:{index}",
                **scope,
            )
            current = work_issues.get_issue(conn, issue_id)["work_issue"]
        return get_scoped_issue(conn, issue_id)


def list_scoped_issue_projections(
    conn: psycopg.Connection,
    *,
    entity_type: str,
    entity_id: str,
    include_terminal: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if entity_type not in ALLOWED_SCOPE_TYPES:
        raise WorkIssueScopeError(f"unsupported WorkIssue scope type: {entity_type!r}")
    if not entity_id.strip():
        raise WorkIssueScopeError("scope entity_id is required")
    if limit < 1 or limit > 500:
        raise WorkIssueScopeError("limit must be between 1 and 500")
    terminal_filter = "" if include_terminal else "AND w.status NOT IN ('done', 'cancelled')"
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT w.issue_id
              FROM work_issue_scope_links s
              JOIN work_issues w ON w.issue_id = s.issue_id
             WHERE s.entity_type = %s
               AND s.entity_id = %s
               AND s.retired_at IS NULL
               {terminal_filter}
             ORDER BY
                   CASE w.status
                       WHEN 'review' THEN 0
                       WHEN 'waiting' THEN 1
                       WHEN 'open' THEN 2
                       WHEN 'in_progress' THEN 3
                       WHEN 'done' THEN 4
                       WHEN 'cancelled' THEN 5
                       ELSE 99
                   END,
                   w.updated_at DESC,
                   w.issue_id
             LIMIT %s
            """,
            (entity_type, entity_id, limit),
        )
        issue_ids = [row[0] for row in cur.fetchall()]

    if not issue_ids:
        return []

    from . import work_issue_read
    from .work_activity_projection import project_work_activity

    projections: list[dict[str, Any]] = []
    for issue_id in issue_ids:
        aggregate = get_scoped_issue(conn, issue_id)
        aggregate["work_issue"] = work_issue_read.get_issue_record(conn, issue_id)
        aggregate["work_activity"] = project_work_activity(aggregate)
        projections.append(aggregate)
    projections.sort(
        key=lambda projection: _STATUS_ORDER.get(
            projection["work_issue"]["status"], 99
        )
    )
    return projections
