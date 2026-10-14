"""Structured human review for Project ChangeCandidates.

A revision request is a human review decision on one proposal envelope. It never
mutates the Project, starts Hermes, authorizes a task, or admits Evidence.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any
import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import agency_change_candidates, agency_data


MIGRATION = Path(__file__).resolve().parent / "sql" / "005_change_candidate_review.sql"
ANNOTATION_TYPES = {
    "source_required",
    "question",
    "hypothesis",
    "contradiction",
    "needs_deeper_review",
}


class ChangeCandidateReviewError(agency_change_candidates.ChangeCandidateError):
    pass


class ChangeCandidateReviewConflict(agency_change_candidates.ChangeCandidateConflict):
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


def _candidate_row(
    conn: psycopg.Connection,
    candidate_id: str,
    *,
    lock: bool = False,
) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM agency_change_candidates WHERE candidate_id = %s{suffix}",
            (candidate_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise agency_change_candidates.ChangeCandidateNotFound(
            f"unknown Agency ChangeCandidate: {candidate_id}"
        )
    return _jsonable(dict(row))


def _event_by_idempotency(conn: psycopg.Connection, idempotency_key: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_change_candidate_events WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    return _jsonable(dict(row)) if row else None


def _review_events(conn: psycopg.Connection, candidate_id: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT event_id, event_type, actor, actor_kind, idempotency_key, payload, occurred_at
              FROM agency_change_candidate_events
             WHERE candidate_id = %s
             ORDER BY occurred_at, event_id
            """,
            (candidate_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return _jsonable(rows)


def _source_refs(values: list[str] | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        if len(value) > 2_000:
            raise ChangeCandidateReviewError("annotation source_ref cannot exceed 2000 characters")
        seen.add(value)
        output.append(value)
    if len(output) > 50:
        raise ChangeCandidateReviewError("an annotation cannot contain more than 50 source_refs")
    return output


def normalize_annotations(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        raise ChangeCandidateReviewError("at least one structured review annotation is required")
    if len(values) > 50:
        raise ChangeCandidateReviewError("review annotations cannot contain more than 50 entries")

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(values):
        if not isinstance(raw, dict):
            raise ChangeCandidateReviewError(f"review annotation {index + 1} must be an object")
        annotation_type = str(raw.get("annotation_type") or "").strip()
        if annotation_type not in ANNOTATION_TYPES:
            raise ChangeCandidateReviewError(
                f"unsupported review annotation type: {annotation_type or 'empty'}"
            )
        message = str(raw.get("message") or "").strip()
        if not message:
            raise ChangeCandidateReviewError(
                f"review annotation {index + 1} requires a message"
            )
        if len(message) > 5_000:
            raise ChangeCandidateReviewError("review annotation message cannot exceed 5000 characters")
        field = str(raw.get("field") or "").strip() or None
        if field and len(field) > 200:
            raise ChangeCandidateReviewError("review annotation field cannot exceed 200 characters")
        normalized.append(
            {
                "annotation_type": annotation_type,
                "field": field,
                "message": message,
                "source_refs": _source_refs(raw.get("source_refs")),
            }
        )
    return normalized


def list_revision_requested_project_candidates(
    conn: psycopg.Connection,
    *,
    project_id: str,
    limit: int = 100,
) -> list[dict]:
    ensure_schema(conn)
    if limit < 1 or limit > 500:
        raise ChangeCandidateReviewError("candidate list limit must be between 1 and 500")
    agency_data.get_project(conn, project_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM agency_change_candidates
             WHERE entity_id = %s
               AND status = 'revision_requested'
             ORDER BY created_at DESC, candidate_id
             LIMIT %s
            """,
            (project_id, limit),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return _jsonable(rows)


def get_project_candidate_review(
    conn: psycopg.Connection,
    *,
    candidate_id: str,
) -> dict:
    ensure_schema(conn)
    candidate = _candidate_row(conn, candidate_id)
    return {
        "change_candidate": candidate,
        "review_events": _review_events(conn, candidate_id),
    }


def request_project_candidate_revision(
    conn: psycopg.Connection,
    *,
    candidate_id: str,
    actor: str,
    annotations: list[dict[str, Any]],
    idempotency_key: str,
    note: str | None = None,
) -> dict:
    ensure_schema(conn)
    normalized_actor = actor.strip()
    normalized_key = idempotency_key.strip()
    normalized_note = (note or "").strip() or None
    if not normalized_actor:
        raise ChangeCandidateReviewError("human actor is required")
    if len(normalized_key) < 8:
        raise ChangeCandidateReviewError("idempotency_key must contain at least 8 characters")
    if normalized_note and len(normalized_note) > 10_000:
        raise ChangeCandidateReviewError("revision request note cannot exceed 10000 characters")
    normalized_annotations = normalize_annotations(annotations)

    replayed = _event_by_idempotency(conn, normalized_key)
    if replayed is not None:
        if replayed["candidate_id"] != candidate_id or replayed["event_type"] != "revision_requested":
            raise agency_change_candidates.ChangeCandidateIdempotencyConflict(
                "idempotency key already belongs to another ChangeCandidate decision"
            )
        return get_project_candidate_review(conn, candidate_id=candidate_id)

    with conn.transaction():
        candidate = _candidate_row(conn, candidate_id, lock=True)
        if candidate["status"] != "pending_review":
            raise ChangeCandidateReviewConflict(
                f"ChangeCandidate cannot request revision from status {candidate['status']}"
            )
        conn.execute(
            """
            UPDATE agency_change_candidates
               SET status = 'revision_requested',
                   review_annotations = %s,
                   decision_note = %s,
                   decided_at = CURRENT_TIMESTAMP,
                   decided_by = %s
             WHERE candidate_id = %s
            """,
            (Jsonb(normalized_annotations), normalized_note, normalized_actor, candidate_id),
        )
        conn.execute(
            """
            INSERT INTO agency_change_candidate_events (
                event_id, candidate_id, event_type, actor, actor_kind, idempotency_key, payload
            ) VALUES (%s, %s, 'revision_requested', %s, 'human', %s, %s)
            """,
            (
                f"change-event-{uuid.uuid4().hex}",
                candidate_id,
                normalized_actor,
                normalized_key,
                Jsonb(
                    {
                        "base_revision": candidate["base_revision"],
                        "proposal_digest": candidate["proposal_digest"],
                        "annotations": normalized_annotations,
                        "note": normalized_note,
                        "project_mutated": False,
                        "task_authorized": False,
                        "evidence_admitted": False,
                    }
                ),
            ),
        )

    return get_project_candidate_review(conn, candidate_id=candidate_id)
