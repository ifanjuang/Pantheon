"""Immutable rich candidate material returned by one admitted Hermes run.

This is deliberately separate from the bounded Work Issue normalized return.
A result candidate may support review and later Evidence work, but it is not
Evidence, Knowledge, a Decision, professional truth or an external action.
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

MIGRATION = Path(__file__).resolve().parent / "sql" / "hermes" / "006_result_candidates.sql"

MAX_LIST_ITEMS = 500
MAX_STRING_ITEM = 20_000
MAX_SUMMARY = 20_000
MAX_RESULT_TYPE = 200
MAX_CONFIDENCE_NOTE = 10_000
MAX_PAYLOAD_CHARS = 500_000


class HermesResultCandidateError(ValueError):
    pass


class HermesResultCandidateConflict(HermesResultCandidateError):
    pass


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise HermesResultCandidateError("candidate payload must be JSON serializable") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _string_list(values: list[Any] | None, *, field: str) -> list[str]:
    if values is None:
        return []
    if len(values) > MAX_LIST_ITEMS:
        raise HermesResultCandidateError(f"{field} exceeds {MAX_LIST_ITEMS} entries")
    output: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value:
            raise HermesResultCandidateError(f"{field} entries must be non-empty strings")
        if len(value) > MAX_STRING_ITEM:
            raise HermesResultCandidateError(
                f"{field} entries must be at most {MAX_STRING_ITEM} characters"
            )
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def normalize_candidate(candidate: dict) -> dict:
    allowed = {
        "result_type",
        "candidate_payload",
        "confidence_note",
        "known_limits",
        "open_questions",
        "source_refs",
        "missing_evidence",
    }
    unknown = sorted(set(candidate) - allowed)
    if unknown:
        raise HermesResultCandidateError(
            "unsupported Hermes result candidate field(s): " + ", ".join(unknown)
        )
    result_type = str(candidate.get("result_type") or "").strip()
    if not result_type or len(result_type) > MAX_RESULT_TYPE:
        raise HermesResultCandidateError("result_type is required and must be at most 200 characters")
    payload = candidate.get("candidate_payload", {})
    if not isinstance(payload, dict):
        raise HermesResultCandidateError("candidate_payload must be an object")
    payload_raw = _canonical(payload)
    if len(payload_raw) > MAX_PAYLOAD_CHARS:
        raise HermesResultCandidateError(
            f"candidate_payload exceeds {MAX_PAYLOAD_CHARS} serialized characters"
        )
    confidence_note = candidate.get("confidence_note")
    if confidence_note is not None:
        confidence_note = str(confidence_note).strip() or None
        if confidence_note and len(confidence_note) > MAX_CONFIDENCE_NOTE:
            raise HermesResultCandidateError(
                f"confidence_note must be at most {MAX_CONFIDENCE_NOTE} characters"
            )
    return {
        "result_type": result_type,
        "candidate_payload": payload,
        "confidence_note": confidence_note,
        "known_limits": _string_list(candidate.get("known_limits"), field="known_limits"),
        "open_questions": _string_list(candidate.get("open_questions"), field="open_questions"),
        "source_refs": _string_list(candidate.get("source_refs"), field="source_refs"),
        "missing_evidence": _string_list(candidate.get("missing_evidence"), field="missing_evidence"),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _row_by_run(conn: psycopg.Connection, run_id: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM hermes_result_candidates WHERE run_id = %s", (run_id,))
        row = cur.fetchone()
    return _jsonable(dict(row)) if row else None


def get_result_candidate_for_run(conn: psycopg.Connection, run_id: str) -> dict | None:
    """Read the immutable rich candidate owned by one Hermes run, when present."""
    run_id = str(run_id or "").strip()
    if not run_id:
        raise HermesResultCandidateError("run_id is required")
    return _row_by_run(conn, run_id)


def _row_by_idempotency(conn: psycopg.Connection, idempotency_key: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM hermes_result_candidates WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    return _jsonable(dict(row)) if row else None


def get_result_candidate(conn: psycopg.Connection, result_candidate_id: str) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM hermes_result_candidates WHERE result_candidate_id = %s",
            (result_candidate_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HermesResultCandidateError(f"unknown Hermes result candidate: {result_candidate_id}")
    return _jsonable(dict(row))


def create_result_candidate(
    conn: psycopg.Connection,
    *,
    run_id: str,
    admission_id: str,
    issue_id: str,
    summary: str,
    trace_refs: list[str],
    evidence_candidate_refs: list[str],
    candidate: dict,
    actor: str,
    idempotency_key: str,
) -> dict:
    if not actor.strip():
        raise HermesResultCandidateError("Hermes actor is required")
    if len(idempotency_key.strip()) < 8:
        raise HermesResultCandidateError("idempotency_key must contain at least 8 characters")
    summary = summary.strip()
    if not summary or len(summary) > MAX_SUMMARY:
        raise HermesResultCandidateError("summary is required and must be at most 20000 characters")

    normalized = normalize_candidate(candidate)
    normalized_trace_refs = _string_list(trace_refs, field="trace_refs")
    if not normalized_trace_refs:
        raise HermesResultCandidateError("trace_refs requires at least one entry")
    normalized_evidence_refs = _string_list(
        evidence_candidate_refs,
        field="evidence_candidate_refs",
    )
    material = {
        "run_id": run_id,
        "admission_id": admission_id,
        "issue_id": issue_id,
        "summary": summary,
        "trace_refs": normalized_trace_refs,
        "evidence_candidate_refs": normalized_evidence_refs,
        **normalized,
        "created_by": actor.strip(),
    }
    result_digest = _digest(material)

    replay = _row_by_idempotency(conn, idempotency_key)
    if replay is not None:
        if replay["run_id"] != run_id or replay["result_digest"] != result_digest:
            raise HermesResultCandidateConflict(
                "idempotency key already belongs to another Hermes result candidate"
            )
        return replay

    existing = _row_by_run(conn, run_id)
    if existing is not None:
        if existing["result_digest"] != result_digest:
            raise HermesResultCandidateConflict(
                "Hermes run already owns a different immutable result candidate"
            )
        return existing

    result_candidate_id = f"result-candidate-{uuid.uuid4().hex}"
    conn.execute(
        """
        INSERT INTO hermes_result_candidates (
            result_candidate_id, run_id, admission_id, issue_id,
            result_type, summary, candidate_payload, confidence_note,
            known_limits, open_questions, source_refs, trace_refs,
            missing_evidence, evidence_candidate_refs, result_digest,
            idempotency_key, created_by
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            result_candidate_id,
            run_id,
            admission_id,
            issue_id,
            normalized["result_type"],
            summary,
            Jsonb(normalized["candidate_payload"]),
            normalized["confidence_note"],
            Jsonb(normalized["known_limits"]),
            Jsonb(normalized["open_questions"]),
            Jsonb(normalized["source_refs"]),
            Jsonb(normalized_trace_refs),
            Jsonb(normalized["missing_evidence"]),
            Jsonb(normalized_evidence_refs),
            result_digest,
            idempotency_key,
            actor.strip(),
        ),
    )
    return get_result_candidate(conn, result_candidate_id)
