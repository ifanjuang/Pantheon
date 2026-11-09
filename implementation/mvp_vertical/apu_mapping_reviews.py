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
    "accept_claim_candidate",
    "accept_object_candidate",
    "accept_retirement",
}
# Actions that make sense for each candidate kind. An identity candidate is
# matched to a stable object; a claim candidate is accepted for a claim write.
IDENTITY_ACTIONS = {"select_existing_object", "mark_unmatched", "needs_clarification", "reject_mapping"}
CLAIM_ACTIONS = {"accept_claim_candidate", "needs_clarification", "reject_mapping"}
# A new-object candidate is accepted for an add_object write; a retirement
# candidate for a retire_object write. Neither selects an existing object.
OBJECT_ACTIONS = {"accept_object_candidate", "needs_clarification", "reject_mapping"}
RETIREMENT_ACTIONS = {"accept_retirement", "needs_clarification", "reject_mapping"}
ACTIONS_BY_KIND = {
    "claim": CLAIM_ACTIONS,
    "object": OBJECT_ACTIONS,
    "retirement": RETIREMENT_ACTIONS,
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
    lifecycle = lifecycle_candidate(execution, result_ref, mapping_ref)
    if lifecycle is not None:
        return lifecycle
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
    if relation is None or relation.get("relation_type") != "identity.represents":
        claim = claim_candidate(execution, result_ref, mapping_ref)
        if claim is not None:
            return claim
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


def lifecycle_candidate(
    execution: dict[str, Any], result_ref: str, candidate_ref: str
) -> dict[str, Any] | None:
    """Return one new-object or retirement candidate of an Observation Bundle, or None.

    As for claims, the candidate is returned exactly as the bundle carries it.
    A new-object candidate must name a candidate source representation of the
    same bundle: an object enters the APU only with the occurrence observing it.
    """
    result = next(
        (item for item in execution.get("results", []) if item.get("result_id") == result_ref),
        None,
    )
    if result is None or result.get("result_kind") != "observation_bundle":
        return None
    payload = result.get("payload")
    if not isinstance(payload, dict):
        return None
    for kind, field, id_field in (
        ("object", "object_candidates", "object_candidate_id"),
        ("retirement", "retirement_candidates", "retirement_candidate_id"),
    ):
        for item in payload.get(field) or []:
            if not isinstance(item, dict) or item.get(id_field) != candidate_ref:
                continue
            if kind == "object":
                representation_id = item.get("source_representation_ref")
                representation = next(
                    (
                        rep
                        for rep in payload.get("source_representations") or []
                        if isinstance(rep, dict) and rep.get("representation_id") == representation_id
                    ),
                    None,
                )
                if representation is None:
                    raise ApuMappingReviewError("object candidate names an unknown source representation")
                if representation.get("proof_status") != "candidate":
                    raise ApuMappingReviewError("object candidate source representation must remain candidate")
            return {
                "mapping_id": candidate_ref,
                "candidate_kind": kind,
                "candidate": item,
                "project_ref": payload.get("project_ref"),
                "rationale": item.get("rationale") or "Observation Bundle lifecycle candidate.",
                "match_candidates": [],
            }
    return None


def claim_candidate(
    execution: dict[str, Any], result_ref: str, candidate_ref: str
) -> dict[str, Any] | None:
    """Return one non-identity claim candidate of an Observation Bundle, or None.

    The candidate is returned exactly as the bundle carries it, so a later write
    can be compared with it field for field.
    """
    result = next(
        (item for item in execution.get("results", []) if item.get("result_id") == result_ref),
        None,
    )
    if result is None or result.get("result_kind") != "observation_bundle":
        return None
    payload = result.get("payload")
    if not isinstance(payload, dict):
        return None
    for family, field, id_field in (
        ("attribute", "attribute_claim_candidates", "attribute_claim_id"),
        ("relation", "relation_claim_candidates", "relation_claim_id"),
    ):
        for item in payload.get(field) or []:
            if not isinstance(item, dict) or item.get(id_field) != candidate_ref:
                continue
            if family == "relation" and str(item.get("relation_type") or "").startswith("identity."):
                return None
            if item.get("proof_status") != "candidate":
                raise ApuMappingReviewError("Observation Bundle claim candidate must remain candidate")
            return {
                "mapping_id": candidate_ref,
                "candidate_kind": "claim",
                "claim_family": family,
                "claim_candidate": item,
                "project_ref": payload.get("project_ref"),
                "rationale": item.get("notes") or "Observation Bundle claim candidate.",
                "match_candidates": [],
            }
    return None


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
    superseded_claim_ref: str | None = None,
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
    superseded = (superseded_claim_ref or "").strip() or None
    kind = mapping.get("candidate_kind") or "identity"
    allowed = ACTIONS_BY_KIND.get(kind, IDENTITY_ACTIONS)
    if action not in allowed:
        raise ApuMappingReviewError(f"{action} does not apply to a {kind} candidate")
    if superseded is not None and action != "accept_claim_candidate":
        raise ApuMappingReviewError("superseded_claim_ref is allowed only for claim acceptance")
    if superseded is not None and superseded == mapping.get("mapping_id"):
        raise ApuMappingReviewError("a claim candidate cannot replace itself")
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
    # Added only when set, so the digest of every earlier review is unchanged
    # and replaying its idempotency key still matches.
    if superseded is not None:
        payload["superseded_claim_ref"] = superseded
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
                reviewer, idempotency_key, payload_digest, superseded_claim_ref
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                superseded,
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
