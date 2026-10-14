"""Immutable storage for exact Cockpit -> Hermes handoff contract snapshots.

Submitting a handoff creates a Work Issue assigned to Hermes. It does not start
an Hermes run. The persisted Task Contract / Context Pack remain candidate
snapshots external to Pantheon's canonical governance records.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import card_scope, work_issue_read, work_issues
from .hermes_execution_basis import HermesExecutionBasis, HermesExecutionBasisError

MIGRATION = Path(__file__).resolve().parent / "sql" / "hermes" / "003_handoff_contracts.sql"


class HandoffSubmissionError(ValueError):
    pass


class HandoffIdempotencyConflict(HandoffSubmissionError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _existing_by_idempotency(conn: psycopg.Connection, idempotency_key: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM cockpit_hermes_handoffs WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def get_handoff_snapshot(conn: psycopg.Connection, handoff_id: str) -> dict:
    """Read one immutable handoff snapshot without changing execution state."""
    handoff_id = str(handoff_id or "").strip()
    if not handoff_id:
        raise HandoffSubmissionError("handoff_id is required")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM cockpit_hermes_handoffs WHERE handoff_id = %s",
            (handoff_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HandoffSubmissionError(f"unknown Cockpit Hermes handoff: {handoff_id}")
    snapshot = _jsonable(dict(row))
    snapshot["work_issue"] = work_issue_read.get_issue_record(conn, snapshot["work_issue_id"])
    return snapshot


def _result_from_row(conn: psycopg.Connection, row: dict) -> dict:
    issue = work_issue_read.get_issue_record(conn, row["work_issue_id"])
    return {
        "handoff_id": row["handoff_id"],
        "case_ref": row["case_ref"],
        "task_contract_ref": row["task_contract_ref"],
        "context_pack_ref": row["context_pack_ref"],
        "preview_digest": row["preview_digest"],
        "work_issue": issue,
        "execution_started": False,
        "hermes_run_created": False,
        "status": "submitted_work_issue",
    }


def _initialize_work_card_metadata(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    question: str,
    root: dict,
) -> None:
    information_ref = None
    if root.get("entity_type") == "information":
        information_ref = str(root.get("entity_id") or "").strip() or None
    workflow = {
        "objective": question.strip(),
        "milestones": [],
        "responsibilities": [],
        "skills": [],
        "functions": [],
        "tools": [],
    }
    conn.execute(
        """
        INSERT INTO work_card_metadata (
            issue_id, workflow, information_ref, result_ref, decision_request
        ) VALUES (%s, %s, %s, NULL, '{}'::jsonb)
        ON CONFLICT (issue_id) DO NOTHING
        """,
        (issue_id, Jsonb(workflow), information_ref),
    )


def submit_handoff(
    conn: psycopg.Connection,
    *,
    actor: str,
    idempotency_key: str,
    question: str,
    preview: dict,
    card_context_envelope: dict,
    selected_context: list[dict],
    include_declared_descendants: bool,
) -> dict:
    if not actor or not actor.strip():
        raise HandoffSubmissionError("human actor is required")
    if len(idempotency_key.strip()) < 8:
        raise HandoffSubmissionError("idempotency_key must contain at least 8 characters")
    if preview.get("execution_authorized") is not False:
        raise HandoffSubmissionError("handoff preview must remain execution_authorized=false")
    if preview.get("requested_effect") != "read_only":
        raise HandoffSubmissionError("this handoff submission slice accepts read_only effect only")
    try:
        basis = HermesExecutionBasis.from_values(
            requested_effect=preview.get("requested_effect"),
            task_contract_ref=(preview.get("task_contract") or {}).get("task_contract_ref"),
            context_pack_ref=(preview.get("context_pack") or {}).get("context_pack_ref"),
            preview_digest=preview.get("preview_digest"),
            label="handoff preview basis",
        )
    except HermesExecutionBasisError as exc:
        raise HandoffSubmissionError(str(exc)) from exc

    root = card_context_envelope.get("root_entity") or {}
    request_record = {
        "question": question.strip(),
        "preview_digest": basis.preview_digest,
        "task_contract_ref": basis.task_contract_ref,
        "context_pack_ref": basis.context_pack_ref,
        "card_context_envelope": card_context_envelope,
        "selected_context": selected_context,
        "include_declared_descendants": bool(include_declared_descendants),
        "actor": actor.strip(),
    }
    request_digest = _digest(request_record)

    # Important transaction boundary: resolve_case_ref() performs owner reads. It
    # must happen inside the same explicit transaction as the handoff write rather
    # than starting an implicit outer transaction before conn.transaction().
    with conn.transaction():
        case_ref = card_scope.resolve_case_ref(conn, root_entity=root)
        existing = _existing_by_idempotency(conn, idempotency_key)
        if existing is not None:
            if existing["request_digest"] != request_digest:
                raise HandoffIdempotencyConflict(
                    "idempotency key already belongs to another Hermes handoff submission"
                )
            return _result_from_row(conn, existing)

        issue_id = f"work-{uuid.uuid4().hex}"
        handoff_id = f"handoff-{uuid.uuid4().hex}"
        title_seed = question.strip().replace("\n", " ")
        title = f"Hermes · {title_seed[:140]}" if title_seed else "Hermes · question Cockpit"
        work_issues.create_issue(
            conn,
            issue_id=issue_id,
            case_ref=case_ref,
            title=title,
            description=question.strip(),
            priority="normal",
            requested_effect=basis.requested_effect,
            assigned_to="hermes",
            task_contract_ref=basis.task_contract_ref,
            context_pack_ref=basis.context_pack_ref,
            created_by=actor.strip(),
            idempotency_key=f"{idempotency_key}:work-issue",
        )
        _initialize_work_card_metadata(
            conn,
            issue_id=issue_id,
            question=question,
            root=root,
        )
        issue = work_issue_read.get_issue_record(conn, issue_id)
        conn.execute(
            """
            INSERT INTO cockpit_hermes_handoffs (
                handoff_id, work_issue_id, case_ref,
                root_entity_id, root_entity_type, question, requested_effect,
                task_contract_ref, context_pack_ref, preview_digest,
                request_digest, task_contract, context_pack, selected_context,
                include_declared_descendants, idempotency_key, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                handoff_id,
                issue_id,
                case_ref,
                root["entity_id"],
                root["entity_type"],
                question.strip(),
                basis.requested_effect,
                basis.task_contract_ref,
                basis.context_pack_ref,
                basis.preview_digest,
                request_digest,
                Jsonb(preview["task_contract"]),
                Jsonb(preview["context_pack"]),
                Jsonb(selected_context),
                bool(include_declared_descendants),
                idempotency_key,
                actor.strip(),
            ),
        )
        return {
            "handoff_id": handoff_id,
            "case_ref": case_ref,
            "task_contract_ref": basis.task_contract_ref,
            "context_pack_ref": basis.context_pack_ref,
            "preview_digest": basis.preview_digest,
            "work_issue": issue,
            "execution_started": False,
            "hermes_run_created": False,
            "status": "submitted_work_issue",
        }
