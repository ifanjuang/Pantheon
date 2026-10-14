"""Append-only review events for individual APU mapping candidates.

A review may target either one legacy ``apu_object_mapping`` candidate or one
exact ``identity.represents`` relation candidate carried by a canonical
Observation Bundle. It may select one proposed existing object, mark the
candidate unmatched, request clarification or reject it. It never writes an APU
object or confirms a canonical identity.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row

from . import execution_results


MIGRATION = Path(__file__).resolve().parent / "sql" / "011_apu_mapping_reviews.sql"
ACTIONS = {
    "select_existing_object",
    "mark_unmatched",
    "needs_clarification",
    "reject_mapping",
}
AUTHORITY = {
    "confirms_stable_identity": False,
    "writes_apu": False,
    "adopts_project_truth": False,
    "admits_evidence": False,
    "promotes_memory": False,
}


class ApuMappingReviewError(execution_results.ExecutionResultError):
    pass


class ApuMappingReviewNotFound(ApuMappingReviewError):
    pass


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _non_empty(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ApuMappingReviewError(f"{field} is required")
    return text


def _mapping_candidate(execution: dict[str, Any], result_ref: str, mapping_ref: str) -> dict[str, Any]:
    result = next(
        (item for item in execution.get("results", []) if item.get("result_id") == result_ref),
        None,
    )
    if result is None:
        raise ApuMappingReviewNotFound("mapping result does not belong to execution result")
    payload = result.get("payload")
    if not isinstance(payload, dict):
        raise ApuMappingReviewError("mapping result payload must be an object")

    if result.get("result_kind") == "apu_object_mapping":
        mappings = payload.get("mappings")
        if not isinstance(mappings, list):
            raise ApuMappingReviewError("mapping result payload must contain mappings")
        mapping = next(
            (item for item in mappings if isinstance(item, dict) and item.get("mapping_id") == mapping_ref),
            None,
        )
        if mapping is None:
            raise ApuMappingReviewNotFound("unknown mapping candidate")
        return mapping

    if result.get("result_kind") != "observation_bundle":
        raise ApuMappingReviewError("result must be apu_object_mapping or observation_bundle")
    relations = payload.get("relation_claim_candidates")
    if not isinstance(relations, list):
        raise ApuMappingReviewError("observation bundle must contain relation_claim_candidates")
    relation = next(
        (
            item
            for item in relations
            if isinstance(item, dict) and item.get("relation_claim_id") == mapping_ref
        ),
        None,
    )
    if relation is None:
        raise ApuMappingReviewNotFound("unknown Observation Bundle identity candidate")
    if relation.get("relation_type") != "identity.represents":
        raise ApuMappingReviewError("Observation Bundle review requires identity.represents")
    if relation.get("proof_status") != "candidate" or relation.get("assertion_mode") != "proposed":
        raise ApuMappingReviewError("Observation Bundle identity relation must remain proposed candidate")
    subject_ref = relation.get("subject_ref") or {}
    object_ref = relation.get("object_ref") or {}
    if subject_ref.get("entity_type") != "source_representation":
        raise ApuMappingReviewError("identity candidate must start from a source representation")
    if object_ref.get("entity_type") != "stable_object":
        raise ApuMappingReviewError("identity candidate must target a stable object")
    return {
        "mapping_id": relation["relation_claim_id"],
        "candidate_object_ref": subject_ref.get("entity_id"),
        "certainty": relation.get("certainty"),
        "rationale": relation.get("notes") or "Observation Bundle identity candidate.",
        "match_candidates": [
            {
                "stable_object_ref": object_ref.get("entity_id"),
                "certainty": relation.get("certainty"),
                "rationale": relation.get("notes") or "Observation Bundle identity candidate.",
            }
        ],
        "source_relation_claim": relation,
    }


def append_mapping_review(
    conn,
    *,
    execution_result_id: str,
    result_ref: str,
    mapping_ref: str,
    action: str,
    selected_stable_object_ref: str | None,
    clarification_question: str | None,
    note: str | None,
    reviewer: str,
    idempotency_key: str,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ApuMappingReviewError("unsupported mapping review action")
    reviewer = _non_empty(reviewer, "reviewer")
    key = _non_empty(idempotency_key, "idempotency_key")
    execution = execution_results.get_execution_result(conn, execution_result_id)
    mapping = _mapping_candidate(execution, result_ref, mapping_ref)

    selected = (selected_stable_object_ref or "").strip() or None
    question = (clarification_question or "").strip() or None
    normalized_note = (note or "").strip() or None
    if action == "select_existing_object":
        if selected is None:
            raise ApuMappingReviewError("selected_stable_object_ref is required")
        candidates = {
            str(item.get("stable_object_ref") or "").strip()
            for item in mapping.get("match_candidates", [])
            if isinstance(item, dict)
        }
        if selected not in candidates:
            raise ApuMappingReviewError("selected stable object is not a mapping candidate")
    elif selected is not None:
        raise ApuMappingReviewError("selected_stable_object_ref is allowed only for selection")

    if action == "needs_clarification":
        if question is None:
            raise ApuMappingReviewError("clarification_question is required")
    elif question is not None:
        raise ApuMappingReviewError("clarification_question is allowed only for clarification")

    payload = {
        "execution_result_id": execution_result_id,
        "result_ref": result_ref,
        "mapping_ref": mapping_ref,
        "action": action,
        "selected_stable_object_ref": selected,
        "clarification_question": question,
        "note": normalized_note,
        "reviewer": reviewer,
    }
    payload_digest = _digest(payload)
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM apu_mapping_review_events WHERE idempotency_key = %s",
                (key,),
            )
            replay = cur.fetchone()
            if replay is not None:
                if replay["payload_digest"] != payload_digest:
                    raise execution_results.ExecutionResultConflict(
                        "mapping-review idempotency key belongs to different content"
                    )
                return _jsonable(dict(replay)) | {"authority": dict(AUTHORITY)}
        review_id = f"mapping-review.{hashlib.sha256(key.encode()).hexdigest()[:24]}"
        conn.execute(
            """
            INSERT INTO apu_mapping_review_events (
                review_id, execution_result_id, result_ref, mapping_ref, action,
                selected_stable_object_ref, clarification_question, note,
                reviewer, idempotency_key, payload_digest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                review_id,
                execution_result_id,
                result_ref,
                mapping_ref,
                action,
                selected,
                question,
                normalized_note,
                reviewer,
                key,
                payload_digest,
            ),
        )
    return get_mapping_review(conn, review_id)


def get_mapping_review(conn, review_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM apu_mapping_review_events WHERE review_id = %s", (review_id,))
        row = cur.fetchone()
    if row is None:
        raise ApuMappingReviewNotFound(f"unknown mapping review: {review_id}")
    return _jsonable(dict(row)) | {"authority": dict(AUTHORITY)}


def list_mapping_reviews(
    conn,
    *,
    execution_result_id: str,
    result_ref: str,
    mapping_ref: str,
) -> list[dict[str, Any]]:
    execution = execution_results.get_execution_result(conn, execution_result_id)
    _mapping_candidate(execution, result_ref, mapping_ref)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM apu_mapping_review_events
            WHERE execution_result_id = %s AND result_ref = %s AND mapping_ref = %s
            ORDER BY occurred_at, review_id
            """,
            (execution_result_id, result_ref, mapping_ref),
        )
        rows = cur.fetchall()
    return [_jsonable(dict(row)) | {"authority": dict(AUTHORITY)} for row in rows]
