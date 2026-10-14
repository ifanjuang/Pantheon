"""Append-only persistence for typed execution results and review dispositions.

Storing a result records a candidate returned by an execution runtime. Reviewing
it records a separate disposition. Neither operation writes APU objects, creates
ProjectClaims, admits Evidence, promotes memory or authorizes another task.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import apu_owner, pantheon_contracts


MIGRATION = Path(__file__).resolve().parent / "sql" / "010_execution_results.sql"
VARIANT_MIGRATION = Path(__file__).resolve().parent / "sql" / "020_project_change_variants.sql"
PROJECT_CHANGE_VARIANT_SCHEMA_REF = "schemas/project_change_variant_candidate.schema.yaml"
OBSERVATION_BUNDLE_SCHEMA_REF = (
    "schemas/architecture-project-understanding/observation_bundle.schema.yaml"
)
RESULT_KINDS = {
    "fragment_qualification",
    "document_alignment",
    "spatial_observation",
    "apu_object_mapping",
    "relation_candidate",
    "contradiction_candidate",
    "work_issue_candidate",
    "knowledge_edit_variant",
    "project_change_variant",
    "project_claim_candidate",
    "observation_bundle",
}
DISPOSITIONS = {
    "pending",
    "needs_clarification",
    "accepted_for_mapping",
    "selected_for_change_candidate",
    "accepted_for_claim",
    "rejected",
    "superseded",
}
AUTHORITY = {
    "is_fact": False,
    "is_evidence": False,
    "is_decision": False,
    "is_memory": False,
    "is_apu_write": False,
    "authorizes_external_effect": False,
}


class ExecutionResultError(ValueError):
    pass


class ExecutionResultNotFound(ExecutionResultError):
    pass


class ExecutionResultConflict(ExecutionResultError):
    pass


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(VARIANT_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _digest(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _non_empty(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ExecutionResultError(f"{field} is required")
    return text


def _validate_result_payload(
    *,
    kind: str,
    schema_ref: str,
    payload: dict[str, Any],
    project_ref: Any,
    task_contract_ref: str,
) -> None:
    if kind == "project_change_variant":
        if schema_ref != PROJECT_CHANGE_VARIANT_SCHEMA_REF:
            raise ExecutionResultError(
                "project_change_variant requires the canonical schema_ref"
            )
        try:
            pantheon_contracts.validate("project_change_variant_candidate", payload)
        except pantheon_contracts.ContractViolation as exc:
            raise ExecutionResultError(str(exc)) from exc
        return

    if kind != "observation_bundle":
        return
    if schema_ref != OBSERVATION_BUNDLE_SCHEMA_REF:
        raise ExecutionResultError(
            "observation_bundle requires the canonical schema_ref"
        )
    exact_project_ref = _non_empty(project_ref, "project_ref")
    if payload.get("project_ref") != exact_project_ref:
        raise ExecutionResultError(
            "observation bundle must carry the execution result Project"
        )
    if payload.get("task_contract_ref") != task_contract_ref:
        raise ExecutionResultError(
            "observation bundle must carry the execution result TaskContract"
        )
    try:
        apu_owner._validate("observation_bundle", payload)
    except apu_owner.ApuOwnerError as exc:
        raise ExecutionResultError(str(exc)) from exc


def _load_execution(conn: psycopg.Connection, execution_result_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM execution_results WHERE execution_result_id = %s",
            (execution_result_id,),
        )
        header = cur.fetchone()
        if header is None:
            raise ExecutionResultNotFound(f"unknown execution result: {execution_result_id}")
        cur.execute(
            "SELECT * FROM execution_result_items WHERE execution_result_id = %s "
            "ORDER BY ordinal, result_id",
            (execution_result_id,),
        )
        results = [dict(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT * FROM execution_clarification_requests WHERE execution_result_id = %s "
            "ORDER BY created_at, clarification_id",
            (execution_result_id,),
        )
        clarifications = [dict(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT d.* FROM execution_result_review_dispositions d "
            "JOIN execution_result_items r ON r.result_id = d.result_ref "
            "WHERE r.execution_result_id = %s ORDER BY d.occurred_at, d.disposition_id",
            (execution_result_id,),
        )
        dispositions = [dict(row) for row in cur.fetchall()]
    return {
        "execution_result": _jsonable(dict(header)),
        "results": _jsonable(results),
        "clarification_requests": _jsonable(clarifications),
        "review_dispositions": _jsonable(dispositions),
        "authority": dict(AUTHORITY),
    }


def store_execution_result(
    conn: psycopg.Connection,
    *,
    execution_result: dict[str, Any],
    idempotency_key: str,
) -> dict[str, Any]:
    if not isinstance(execution_result, dict):
        raise ExecutionResultError("execution_result must be an object")
    execution_result_id = _non_empty(
        execution_result.get("execution_result_id"), "execution_result_id"
    )
    task_contract_ref = _non_empty(
        execution_result.get("task_contract_ref"), "task_contract_ref"
    )
    produced_at = _non_empty(execution_result.get("produced_at"), "produced_at")
    project_ref = execution_result.get("project_ref")
    producer = execution_result.get("producer")
    if not isinstance(producer, dict) or not producer:
        raise ExecutionResultError("producer must be a non-empty object")
    if execution_result.get("authority") != AUTHORITY:
        raise ExecutionResultError("execution result authority boundaries are invalid")
    results = execution_result.get("results")
    if not isinstance(results, list) or not results:
        raise ExecutionResultError("results must be a non-empty array")
    clarifications = execution_result.get("clarification_requests") or []
    if not isinstance(clarifications, list):
        raise ExecutionResultError("clarification_requests must be an array")
    normalized_key = _non_empty(idempotency_key, "idempotency_key")
    payload_digest = _digest(execution_result)

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT execution_result_id, payload_digest FROM execution_results "
                "WHERE idempotency_key = %s",
                (normalized_key,),
            )
            replay = cur.fetchone()
        if replay is not None:
            if replay["payload_digest"] != payload_digest:
                raise ExecutionResultConflict(
                    "execution-result idempotency key belongs to different content"
                )
            return _load_execution(conn, replay["execution_result_id"])

        conn.execute(
            """
            INSERT INTO execution_results (
                execution_result_id, task_contract_ref, project_ref, producer,
                produced_at, evidence_pack_candidate_ref, authority,
                payload_digest, idempotency_key
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                execution_result_id,
                task_contract_ref,
                project_ref,
                Jsonb(producer),
                produced_at,
                execution_result.get("evidence_pack_candidate_ref"),
                Jsonb(AUTHORITY),
                payload_digest,
                normalized_key,
            ),
        )
        result_refs: set[str] = set()
        for ordinal, item in enumerate(results):
            if not isinstance(item, dict):
                raise ExecutionResultError("every result must be an object")
            result_id = _non_empty(item.get("result_id"), "result_id")
            if result_id in result_refs:
                raise ExecutionResultError(f"duplicate result_id: {result_id}")
            result_refs.add(result_id)
            kind = item.get("result_kind")
            if kind not in RESULT_KINDS:
                raise ExecutionResultError(f"unsupported result_kind: {kind}")
            schema_ref = _non_empty(item.get("schema_ref"), "schema_ref")
            payload = item.get("payload")
            if not isinstance(payload, dict):
                raise ExecutionResultError("result payload must be an object")
            _validate_result_payload(
                kind=kind,
                schema_ref=schema_ref,
                payload=payload,
                project_ref=project_ref,
                task_contract_ref=task_contract_ref,
            )
            conn.execute(
                "INSERT INTO execution_result_items "
                "(result_id, execution_result_id, result_kind, schema_ref, payload, payload_digest, ordinal) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (result_id, execution_result_id, kind, schema_ref, Jsonb(payload), _digest(payload), ordinal),
            )

        for clarification in clarifications:
            if not isinstance(clarification, dict):
                raise ExecutionResultError("every clarification must be an object")
            related = clarification.get("related_result_refs") or []
            if not isinstance(related, list) or any(ref not in result_refs for ref in related):
                raise ExecutionResultError("clarification references unknown results")
            answer_kind = clarification.get("answer_kind")
            if answer_kind not in {
                "free_text", "single_choice", "multiple_choice", "confirmation", "source_request"
            }:
                raise ExecutionResultError("unsupported clarification answer_kind")
            conn.execute(
                "INSERT INTO execution_clarification_requests "
                "(clarification_id, execution_result_id, related_result_refs, question, answer_kind, options, rationale) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    _non_empty(clarification.get("clarification_id"), "clarification_id"),
                    execution_result_id,
                    Jsonb(related),
                    _non_empty(clarification.get("question"), "clarification.question"),
                    answer_kind,
                    Jsonb(clarification.get("options") or []),
                    _non_empty(clarification.get("rationale"), "clarification.rationale"),
                ),
            )
        stored = _load_execution(conn, execution_result_id)
    return stored


def get_execution_result(conn: psycopg.Connection, execution_result_id: str) -> dict[str, Any]:
    return _load_execution(conn, execution_result_id)


def list_project_execution_results(
    conn: psycopg.Connection,
    *,
    project_ref: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 200:
        raise ExecutionResultError("limit must be between 1 and 200")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT execution_result_id FROM execution_results WHERE project_ref = %s "
            "ORDER BY produced_at DESC, execution_result_id LIMIT %s",
            (project_ref, limit),
        )
        ids = [row[0] for row in cur.fetchall()]
    return [_load_execution(conn, result_id) for result_id in ids]


def append_review_disposition(
    conn: psycopg.Connection,
    *,
    result_ref: str,
    disposition: str,
    reviewer: str,
    reviewer_kind: str,
    note: str | None,
    idempotency_key: str,
) -> dict[str, Any]:
    if disposition not in DISPOSITIONS:
        raise ExecutionResultError("unsupported review disposition")
    if reviewer_kind not in {"human", "system"}:
        raise ExecutionResultError("reviewer_kind must be human or system")
    reviewer = _non_empty(reviewer, "reviewer")
    key = _non_empty(idempotency_key, "idempotency_key")
    payload = {
        "result_ref": result_ref,
        "disposition": disposition,
        "reviewer": reviewer,
        "reviewer_kind": reviewer_kind,
        "note": (note or "").strip() or None,
    }
    payload_digest = _digest(payload)
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            # Reviews, idempotent replays and candidate adoption share this
            # immutable result-row lock. A replay therefore cannot bypass the
            # current semantic checks for its disposition family.
            cur.execute(
                "SELECT execution_result_id, result_kind "
                "FROM execution_result_items WHERE result_id = %s FOR UPDATE",
                (result_ref,),
            )
            row = cur.fetchone()
            if row is None:
                raise ExecutionResultNotFound(f"unknown result candidate: {result_ref}")
            execution_id = row["execution_result_id"]
            result_kind = row["result_kind"]

            if disposition == "accepted_for_claim":
                if result_kind != "project_claim_candidate":
                    raise ExecutionResultError(
                        "accepted_for_claim requires a project_claim_candidate result"
                    )
                if reviewer_kind != "human":
                    raise ExecutionResultError(
                        "accepted_for_claim requires a human reviewer"
                    )

            if disposition == "selected_for_change_candidate":
                if result_kind != "project_change_variant":
                    raise ExecutionResultError(
                        "selected_for_change_candidate requires a project_change_variant result"
                    )
                if reviewer_kind != "human":
                    raise ExecutionResultError(
                        "selected_for_change_candidate requires a human reviewer"
                    )

            cur.execute(
                "SELECT * FROM execution_result_review_dispositions WHERE idempotency_key = %s",
                (key,),
            )
            replay = cur.fetchone()
            if replay is not None:
                if replay["payload_digest"] != payload_digest:
                    raise ExecutionResultConflict(
                        "review-disposition idempotency key belongs to different content"
                    )
                return _load_execution(conn, execution_id)

        conn.execute(
            "INSERT INTO execution_result_review_dispositions "
            "(disposition_id, result_ref, disposition, reviewer, reviewer_kind, note, idempotency_key, payload_digest) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                f"disposition.{hashlib.sha256(key.encode()).hexdigest()[:24]}",
                result_ref,
                disposition,
                reviewer,
                reviewer_kind,
                payload["note"],
                key,
                payload_digest,
            ),
        )
        reviewed = _load_execution(conn, execution_id)
    return reviewed
