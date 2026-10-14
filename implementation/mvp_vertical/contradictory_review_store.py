"""Append-only PostgreSQL storage for contradictory review candidates.

Storage preserves the exact compiled candidate report. It does not validate
Evidence, close ZEUS, authorize a task, mutate the reviewed artifact or approve
any next action.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row

from .contradictory_review import REPORT_STATUSES, report_from_payload

MIGRATION = Path(__file__).resolve().parent / "sql" / "003_contradictory_review_candidates.sql"


class ContradictoryReviewStoreError(ValueError):
    """Base refusal for contradictory review candidate persistence."""


class ContradictoryReviewNotFound(ContradictoryReviewStoreError):
    pass


class ContradictoryReviewConflict(ContradictoryReviewStoreError):
    pass


def _canonical_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _row(conn, review_id: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM contradictory_review_candidates WHERE review_id = %s",
            (review_id,),
        )
        value = cur.fetchone()
    return dict(value) if value is not None else None


def persist_candidate(
    conn,
    *,
    project_id: str,
    submitted_by: str,
    report_payload: dict[str, Any],
) -> dict[str, Any]:
    """Persist one exact compiled report, idempotently by deterministic review id."""
    project_id = str(project_id or "").strip()
    submitted_by = str(submitted_by or "").strip()
    if not project_id:
        raise ContradictoryReviewStoreError("project_id is required")
    if not submitted_by:
        raise ContradictoryReviewStoreError("submitted_by is required")

    report = report_from_payload(report_payload).as_dict()
    authority = report.get("authority") or {}
    if any(
        authority.get(field) is not False
        for field in ("is_evidence", "is_approval", "is_zeus_closure", "is_task_authorization")
    ):
        raise ContradictoryReviewStoreError("candidate report exceeds the storage authority ceiling")
    if report["status"] not in REPORT_STATUSES:
        raise ContradictoryReviewStoreError("unsupported contradictory review status")

    report_digest = _canonical_digest(report)
    existing = _row(conn, report["review_id"])
    if existing is not None:
        if existing["project_id"] != project_id or existing["report_digest"] != report_digest:
            raise ContradictoryReviewConflict(
                "review id already exists with another project or report payload"
            )
        return existing

    with conn.transaction():
        conn.execute(
            """
            INSERT INTO contradictory_review_candidates (
                review_id, project_id, task_contract_ref, candidate_id,
                candidate_digest, execution_id, review_status, report_digest,
                report, submitted_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                report["review_id"],
                project_id,
                report["task_contract_ref"],
                report["candidate"]["candidate_id"],
                report["candidate"]["digest"],
                report["produced_by"]["execution_id"],
                report["status"],
                report_digest,
                json.dumps(report, ensure_ascii=False, sort_keys=True),
                submitted_by,
            ),
        )
    persisted = _row(conn, report["review_id"])
    if persisted is None:
        raise ContradictoryReviewStoreError("candidate report was not persisted")
    return persisted


def get_candidate(conn, review_id: str) -> dict[str, Any]:
    value = _row(conn, str(review_id or "").strip())
    if value is None:
        raise ContradictoryReviewNotFound(f"unknown contradictory review: {review_id}")
    return value


def list_project_candidates(conn, project_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
    project_id = str(project_id or "").strip()
    if not project_id:
        raise ContradictoryReviewStoreError("project_id is required")
    if limit < 1 or limit > 200:
        raise ContradictoryReviewStoreError("limit must be between 1 and 200")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM contradictory_review_candidates
             WHERE project_id = %s
             ORDER BY submitted_at DESC, review_id
             LIMIT %s
            """,
            (project_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]
