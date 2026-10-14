"""Controlled PostgreSQL adapter for the first governed Work Issue slice.

This is persistence, not a queue. Hermes receives no database credentials and
may affect an issue only through the methods that explicitly admit its actor
kind and transition ceiling.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row

from . import pantheon_contracts
from .store import dsn_from_env


MIGRATION = Path(__file__).resolve().parent / "sql" / "001_work_issues.sql"
SCHEMA = pantheon_contracts.schema_path("work_issue_slice")

ISSUE_STATUSES = {"open", "in_progress", "waiting", "review", "done", "cancelled"}
HERMES_TARGETS = {"in_progress", "waiting", "review"}
ALLOWED_TRANSITIONS = {
    "open": {"in_progress", "waiting", "cancelled"},
    "in_progress": {"waiting", "review", "cancelled"},
    "waiting": {"in_progress", "review", "cancelled"},
    "review": {"in_progress", "waiting", "done", "cancelled"},
}
RETURN_TO_RUN_STATUS = {
    "result_candidate": "returned",
    "partial": "partial",
    "failed": "failed",
    "capability_gap": "partial",
}
RETURN_TO_ISSUE_STATUS = {
    "result_candidate": "review",
    "partial": "waiting",
    "failed": "waiting",
    "capability_gap": "waiting",
}


class WorkIssueError(ValueError):
    """Base refusal for the controlled Work Issue adapter."""


class IssueNotFound(WorkIssueError):
    pass


class StaleWrite(WorkIssueError):
    pass


class TransitionRefused(WorkIssueError):
    pass


@lru_cache(maxsize=1)
def _governed_schema() -> dict[str, Any]:
    try:
        schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WorkIssueError(f"unable to load governed Work Issue schema: {exc}") from exc
    if not isinstance(schema, dict):
        raise WorkIssueError("governed Work Issue schema must be an object")
    return schema


def _governed_enum(definition: str) -> frozenset[str]:
    try:
        values = _governed_schema()["$defs"][definition]["enum"]
    except (KeyError, TypeError) as exc:
        raise WorkIssueError(
            f"governed Work Issue schema is missing enum: {definition}"
        ) from exc
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        raise WorkIssueError(
            f"governed Work Issue enum is invalid: {definition}"
        )
    return frozenset(values)


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = psycopg.connect(dsn or dsn_from_env())
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def _event_id() -> str:
    return f"event-{uuid.uuid4().hex}"


def _as_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _issue_row(conn: psycopg.Connection, issue_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM work_issues WHERE issue_id = %s{suffix}", (issue_id,))
        row = cur.fetchone()
    if row is None:
        raise IssueNotFound(f"unknown Work Issue: {issue_id}")
    return dict(row)


def _event_replayed(conn: psycopg.Connection, issue_id: str, idempotency_key: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT issue_id FROM issue_events WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return False
    if row[0] != issue_id:
        raise WorkIssueError("idempotency key already belongs to another issue")
    return True


def _insert_event(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    event_type: str,
    actor: str,
    actor_kind: str,
    expected_version: int,
    idempotency_key: str,
    run_ref: str | None = None,
    payload: dict | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO issue_events (
            event_id, issue_id, run_ref, event_type, actor, actor_kind,
            expected_version, resulting_version, idempotency_key, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            _event_id(),
            issue_id,
            run_ref,
            event_type,
            actor,
            actor_kind,
            expected_version,
            expected_version + 1,
            idempotency_key,
            json.dumps(payload or {}),
        ),
    )


def _transition_locked(
    conn: psycopg.Connection,
    issue: dict,
    *,
    to_status: str,
    actor: str,
    actor_kind: str,
    expected_version: int,
    idempotency_key: str,
    close_reason: str | None = None,
) -> dict:
    current = issue["status"]
    if issue["version"] != expected_version:
        raise StaleWrite(
            f"stale Work Issue version: expected {expected_version}, current {issue['version']}"
        )
    if to_status not in ISSUE_STATUSES or to_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise TransitionRefused(f"transition refused: {current} -> {to_status}")
    if actor_kind == "hermes" and to_status not in HERMES_TARGETS:
        raise TransitionRefused("Hermes may not close or cancel a Work Issue")
    if actor_kind not in {"human", "hermes"}:
        raise TransitionRefused("only a human or admitted Hermes adapter may change status")
    if to_status in {"done", "cancelled"}:
        if actor_kind != "human" or not close_reason:
            raise TransitionRefused("terminal status requires a human and a close reason")
        allowed_close_reasons = _governed_enum("close_reason")
        if close_reason not in allowed_close_reasons:
            expected = ", ".join(sorted(allowed_close_reasons))
            raise TransitionRefused(
                f"unsupported close reason: {close_reason!r}; expected one of: {expected}"
            )
    elif close_reason is not None:
        raise TransitionRefused("an active Work Issue cannot carry a close reason")

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE work_issues
               SET status = %s, close_reason = %s, version = version + 1,
                   updated_at = CURRENT_TIMESTAMP
             WHERE issue_id = %s AND version = %s
            """,
            (to_status, close_reason, issue["issue_id"], expected_version),
        )
        if cur.rowcount != 1:
            raise StaleWrite("Work Issue changed before the transition was persisted")

    _insert_event(
        conn,
        issue_id=issue["issue_id"],
        event_type="status_changed",
        actor=actor,
        actor_kind=actor_kind,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        payload={
            "transition": {
                "from_status": current,
                "to_status": to_status,
                "actor_kind": actor_kind,
            }
        },
    )
    return _issue_row(conn, issue["issue_id"])


def create_issue(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    case_ref: str,
    title: str,
    description: str,
    created_by: str,
    idempotency_key: str,
    issue_type: str = "action",
    priority: str = "normal",
    requested_effect: str = "draft",
    assigned_to: str | None = None,
    task_contract_ref: str | None = None,
    context_pack_ref: str | None = None,
) -> dict:
    with conn.transaction():
        if _event_replayed(conn, issue_id, idempotency_key):
            return get_issue(conn, issue_id)
        conn.execute(
            """
            INSERT INTO work_issues (
                issue_id, case_ref, title, description, origin, issue_type,
                priority, assigned_to, requested_effect, status,
                task_contract_ref, context_pack_ref, created_by
            ) VALUES (%s, %s, %s, %s, 'human', %s, %s, %s, %s, 'open', %s, %s, %s)
            """,
            (
                issue_id, case_ref, title, description, issue_type, priority,
                assigned_to, requested_effect, task_contract_ref, context_pack_ref, created_by,
            ),
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            event_type="issue_created",
            actor=created_by,
            actor_kind="human",
            expected_version=0,
            idempotency_key=idempotency_key,
        )
        projection = get_issue(conn, issue_id)
    return projection


def add_comment(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    comment_id: str,
    body: str,
    author: str,
    expected_version: int,
    idempotency_key: str,
) -> dict:
    with conn.transaction():
        if _event_replayed(conn, issue_id, idempotency_key):
            return get_issue(conn, issue_id)
        issue = _issue_row(conn, issue_id, lock=True)
        if issue["version"] != expected_version:
            raise StaleWrite("comment was based on a stale Work Issue version")
        conn.execute(
            "INSERT INTO issue_comments (comment_id, issue_id, body, author) VALUES (%s, %s, %s, %s)",
            (comment_id, issue_id, body, author),
        )
        conn.execute(
            "UPDATE work_issues SET version = version + 1, updated_at = CURRENT_TIMESTAMP "
            "WHERE issue_id = %s AND version = %s",
            (issue_id, expected_version),
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            event_type="comment_added",
            actor=author,
            actor_kind="human",
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload={"comment_id": comment_id},
        )
        projection = get_issue(conn, issue_id)
    return projection


def start_hermes_run(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    run_id: str,
    task_contract_ref: str,
    context_pack_ref: str,
    actor: str,
    expected_version: int,
    idempotency_key: str,
) -> dict:
    if not task_contract_ref or not context_pack_ref:
        raise WorkIssueError("an admitted Hermes run requires Task Contract and Context Pack refs")
    with conn.transaction():
        if _event_replayed(conn, issue_id, idempotency_key):
            return get_issue(conn, issue_id)
        issue = _issue_row(conn, issue_id, lock=True)
        if issue["assigned_to"] != "hermes":
            raise TransitionRefused("Work Issue is not assigned to Hermes")
        if issue["task_contract_ref"] != task_contract_ref:
            raise TransitionRefused("Hermes run does not match the issue's Task Contract")
        if issue["context_pack_ref"] != context_pack_ref:
            raise TransitionRefused("Hermes run does not match the issue's Context Pack")
        if issue["status"] not in {"open", "waiting"}:
            raise TransitionRefused("a Hermes run may start only from open or waiting")
        conn.execute(
            """
            INSERT INTO hermes_runs (
                run_id, issue_id, task_contract_ref, context_pack_ref, status,
                requested_effect, started_at
            ) VALUES (%s, %s, %s, %s, 'running', %s, CURRENT_TIMESTAMP)
            """,
            (
                run_id, issue_id, task_contract_ref, context_pack_ref,
                issue["requested_effect"],
            ),
        )
        _transition_locked(
            conn,
            issue,
            to_status="in_progress",
            actor=actor,
            actor_kind="hermes",
            expected_version=expected_version,
            idempotency_key=f"{idempotency_key}:status",
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            run_ref=run_id,
            event_type="hermes_started",
            actor=actor,
            actor_kind="hermes",
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload={"task_contract_ref": task_contract_ref, "context_pack_ref": context_pack_ref},
        )
        projection = get_issue(conn, issue_id)
    return projection


def record_hermes_return(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    run_id: str,
    normalized_return: dict,
    actor: str,
    expected_version: int,
    idempotency_key: str,
) -> dict:
    outcome = normalized_return.get("outcome")
    if outcome not in RETURN_TO_RUN_STATUS:
        raise WorkIssueError(f"unsupported normalized return outcome: {outcome!r}")
    if not normalized_return.get("summary") or not normalized_return.get("trace_refs"):
        raise WorkIssueError("normalized return requires summary and trace_refs")

    with conn.transaction():
        if _event_replayed(conn, issue_id, idempotency_key):
            return get_issue(conn, issue_id)
        issue = _issue_row(conn, issue_id, lock=True)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM hermes_runs WHERE run_id = %s AND issue_id = %s FOR UPDATE",
                (run_id, issue_id),
            )
            run = cur.fetchone()
        if run is None or run["status"] != "running":
            raise TransitionRefused("Hermes return requires the issue's running Hermes run")

        conn.execute(
            """
            UPDATE hermes_runs
               SET status = %s, normalized_return = %s::jsonb,
                   returned_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
             WHERE run_id = %s
            """,
            (RETURN_TO_RUN_STATUS[outcome], json.dumps(normalized_return), run_id),
        )
        target = RETURN_TO_ISSUE_STATUS[outcome]
        _transition_locked(
            conn,
            issue,
            to_status=target,
            actor=actor,
            actor_kind="hermes",
            expected_version=expected_version,
            idempotency_key=f"{idempotency_key}:status",
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            run_ref=run_id,
            event_type="hermes_returned",
            actor=actor,
            actor_kind="hermes",
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload={"outcome": outcome},
        )
        if target == "review":
            _insert_event(
                conn,
                issue_id=issue_id,
                run_ref=run_id,
                event_type="review_requested",
                actor=actor,
                actor_kind="hermes",
                expected_version=expected_version,
                idempotency_key=f"{idempotency_key}:review",
            )
        projection = get_issue(conn, issue_id)
    return projection


def close_issue(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    decided_by: str,
    close_reason: str,
    expected_version: int,
    idempotency_key: str,
) -> dict:
    with conn.transaction():
        if _event_replayed(conn, issue_id, idempotency_key):
            return get_issue(conn, issue_id)
        issue = _issue_row(conn, issue_id, lock=True)
        _transition_locked(
            conn,
            issue,
            to_status="done",
            actor=decided_by,
            actor_kind="human",
            expected_version=expected_version,
            idempotency_key=f"{idempotency_key}:status",
            close_reason=close_reason,
        )
        _insert_event(
            conn,
            issue_id=issue_id,
            event_type="issue_closed",
            actor=decided_by,
            actor_kind="human",
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload={"close_reason": close_reason},
        )
        projection = get_issue(conn, issue_id)
    return projection


def transition_issue(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    to_status: str,
    actor: str,
    actor_kind: str,
    expected_version: int,
    idempotency_key: str,
    close_reason: str | None = None,
) -> dict:
    with conn.transaction():
        if _event_replayed(conn, issue_id, idempotency_key):
            return get_issue(conn, issue_id)
        issue = _issue_row(conn, issue_id, lock=True)
        _transition_locked(
            conn,
            issue,
            to_status=to_status,
            actor=actor,
            actor_kind=actor_kind,
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            close_reason=close_reason,
        )
        projection = get_issue(conn, issue_id)
    return projection


def _clean(mapping: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        out[key] = _as_iso(value) if isinstance(value, datetime) else value
    return out


def get_issue(conn: psycopg.Connection, issue_id: str) -> dict:
    issue = _clean(_issue_row(conn, issue_id))
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT comment_id, issue_id AS issue_ref, body, author, created_at "
            "FROM issue_comments WHERE issue_id = %s ORDER BY created_at, comment_id",
            (issue_id,),
        )
        comments = [_clean(dict(row)) for row in cur.fetchall()]
        cur.execute(
            """
            SELECT run_id, issue_id AS issue_ref, task_contract_ref, context_pack_ref,
                   status, requested_effect, started_at, returned_at, normalized_return,
                   created_at, updated_at
              FROM hermes_runs WHERE issue_id = %s ORDER BY created_at, run_id
            """,
            (issue_id,),
        )
        runs = [_clean(dict(row)) for row in cur.fetchall()]
        cur.execute(
            """
            SELECT event_id, issue_id AS issue_ref, run_ref, event_type, actor,
                   actor_kind, expected_version, resulting_version,
                   idempotency_key, payload, occurred_at
              FROM issue_events WHERE issue_id = %s ORDER BY occurred_at, event_id
            """,
            (issue_id,),
        )
        events = []
        for row in cur.fetchall():
            item = _clean(dict(row))
            payload = item.pop("payload", {}) or {}
            if item["event_type"] == "status_changed" and "transition" in payload:
                item["transition"] = payload["transition"]
            events.append(item)

    issue["issue_id"] = issue.pop("issue_id")
    projection = {
        "work_issue": issue,
        "comments": comments,
        "hermes_runs": runs,
        "events": events,
        "governance_refs": [
            "docs/governance/WORK_ISSUE_AND_DELEGATED_MERGE_MODEL.md",
            "docs/governance/TASK_CONTRACTS.md",
            "docs/governance/CONTEXT_PACKS.md",
            "docs/governance/APPROVALS.md",
        ],
    }
    try:
        jsonschema.Draft202012Validator(
            _governed_schema(),
            format_checker=jsonschema.FormatChecker(),
        ).validate(projection)
    except jsonschema.ValidationError as exc:
        raise WorkIssueError(f"stored Work Issue projection violates its governed contract: {exc}") from exc
    return projection
