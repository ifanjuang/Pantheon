"""Bounded A/B Knowledge edit proposals projected from Execution Results.

A request retains one exact Knowledge version and selection scope. Hermes returns
immutable candidates through the canonical Execution Result envelope. Projection,
human selection and Knowledge application remain separate effects.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import knowledge, pantheon_contracts
from .policy_gate import PolicyClient


MIGRATION = Path(__file__).resolve().parent / "sql" / "014_knowledge_edit_variants.sql"
VARIANT_SCHEMA_REF = "schemas/knowledge_edit_variant_candidate.schema.yaml"
_VARIANT_CONTRACT = "knowledge_edit_variant_candidate"
VARIANT_LABELS = ("A", "B")
REVIEWABLE_STATUSES = {
    "queued_for_hermes",
    "proposed",
    "applied",
    "conflict",
    "rejected",
}
CANDIDATE_AUTHORITY = {
    "selects_variant": False,
    "applies_edit": False,
    "validates_knowledge": False,
    "admits_evidence": False,
    "promotes_memory": False,
    "authorizes_task": False,
}


class KnowledgeEditVariantError(knowledge.KnowledgeError):
    pass


class KnowledgeEditVariantConflict(knowledge.StaleKnowledgeWrite):
    pass


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _hex_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256(value: str) -> str:
    return f"sha256:{_hex_digest(value)}"


def _payload_digest(value: dict[str, Any]) -> str:
    canonical = json.dumps(
        _jsonable(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return _sha256(canonical)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _scope_payload(
    *,
    knowledge_id: str,
    base_version: int,
    selection_start: int,
    selection_end: int,
    selected_text_digest: str,
    instruction_kind: str,
    instruction: str,
    requested_variant_count: int,
) -> dict[str, Any]:
    digest = selected_text_digest
    if not digest.startswith("sha256:"):
        digest = f"sha256:{digest}"
    return {
        "knowledge_ref": knowledge_id,
        "base_version": base_version,
        "selection_start": selection_start,
        "selection_end": selection_end,
        "selected_text_digest": digest,
        "instruction_kind": instruction_kind,
        "instruction": instruction,
        "requested_variant_count": requested_variant_count,
    }


def _knowledge_snapshot(
    conn: psycopg.Connection,
    knowledge_id: str,
    *,
    lock: bool = False,
) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT knowledge_id, version, markdown, markdown_digest FROM knowledge_items "
            f"WHERE knowledge_id = %s{suffix}",
            (knowledge_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise knowledge.KnowledgeNotFound(f"unknown Knowledge item: {knowledge_id}")
    return dict(row)


def _request_row(
    conn: psycopg.Connection,
    request_id: str,
    *,
    lock: bool = False,
) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM knowledge_edit_requests WHERE request_id = %s{suffix}",
            (request_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise knowledge.KnowledgeNotFound(f"unknown intelligent edit request: {request_id}")
    return dict(row)


def _variant_row(conn: psycopg.Connection, variant_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM knowledge_edit_variants WHERE variant_id = %s",
            (variant_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise knowledge.KnowledgeNotFound(f"unknown intelligent edit variant: {variant_id}")
    return dict(row)


def _variants(conn: psycopg.Connection, request_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM knowledge_edit_variants WHERE request_id = %s "
            "ORDER BY variant_label, created_at, variant_id",
            (request_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _events(conn: psycopg.Connection, request_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM knowledge_edit_review_events WHERE request_id = %s "
            "ORDER BY occurred_at, event_id",
            (request_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _event_by_key(conn: psycopg.Connection, idempotency_key: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM knowledge_edit_review_events WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def _insert_event(
    conn: psycopg.Connection,
    *,
    request_id: str,
    event_type: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    payload: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO knowledge_edit_review_events (
            event_id, request_id, event_type, actor, actor_kind,
            idempotency_key, payload_digest, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            f"edit-review-event-{uuid.uuid4().hex}",
            request_id,
            event_type,
            actor,
            actor_kind,
            idempotency_key,
            _payload_digest(payload),
            Jsonb(payload),
        ),
    )


def _selection_diff(selected_text: str, replacement: str, label: str) -> str:
    return "".join(
        difflib.unified_diff(
            selected_text.splitlines(keepends=True),
            replacement.splitlines(keepends=True),
            fromfile="selection",
            tofile=f"variant-{label}",
        )
    )


def _scope_status(request: dict[str, Any], item: dict[str, Any]) -> str:
    start = request["selection_start"]
    end = request["selection_end"]
    if item["version"] != request["base_version"]:
        return "stale_version"
    if start < 0 or end <= start or end > len(item["markdown"]):
        return "invalid_range"
    selected = item["markdown"][start:end]
    if _hex_digest(selected) != request["selected_text_digest"]:
        return "stale_selection"
    return "current"


def get_variant_review(conn: psycopg.Connection, request_id: str) -> dict[str, Any]:
    request = _request_row(conn, request_id)
    item = _knowledge_snapshot(conn, request["knowledge_id"])
    selected_text = request.get("selected_text_snapshot") or ""
    if not selected_text and _scope_status(request, item) == "current":
        selected_text = item["markdown"][request["selection_start"]:request["selection_end"]]

    projected_variants: list[dict[str, Any]] = []
    for variant in _variants(conn, request_id):
        projected = _jsonable(dict(variant))
        projected["diff"] = _selection_diff(
            selected_text,
            str(variant["replacement_markdown"]),
            str(variant["variant_label"]),
        )
        projected["selected"] = variant["variant_id"] == request.get("selected_variant_id")
        projected_variants.append(projected)

    request_projection = _jsonable(request)
    request_projection["selected_text"] = selected_text
    request_projection["scope_status"] = _scope_status(request, item)
    request_projection["variant_count"] = len(projected_variants)
    return {
        "edit_request": request_projection,
        "variants": projected_variants,
        "review_events": _jsonable(_events(conn, request_id)),
        "knowledge": {
            "knowledge_id": item["knowledge_id"],
            "version": item["version"],
            "markdown_digest": item["markdown_digest"],
        },
        "execution_result_stored_is_variant_projected": False,
        "variant_selected_is_edit_applied": False,
        "proposal_is_evidence": False,
    }


def list_variant_reviews(
    conn: psycopg.Connection,
    *,
    knowledge_id: str,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if status is not None and status not in REVIEWABLE_STATUSES:
        raise KnowledgeEditVariantError("unsupported intelligent edit review status")
    if limit < 1 or limit > 100:
        raise KnowledgeEditVariantError("review list limit must be between 1 and 100")
    parameters: list[Any] = [knowledge_id]
    clause = ""
    if status is not None:
        clause = " AND status = %s"
        parameters.append(status)
    parameters.append(limit)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT request_id FROM knowledge_edit_requests "
            f"WHERE knowledge_id = %s{clause} ORDER BY created_at DESC, request_id LIMIT %s",
            tuple(parameters),
        )
        request_ids = [row[0] for row in cur.fetchall()]
    return [get_variant_review(conn, request_id) for request_id in request_ids]


def create_variant_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    knowledge_id: str,
    instruction_kind: str,
    instruction: str,
    base_version: int,
    selection_start: int,
    selection_end: int,
    selected_text: str,
    requested_by: str,
    requested_variant_count: int,
    idempotency_key: str,
) -> dict[str, Any]:
    if instruction_kind not in knowledge.INSTRUCTION_KINDS or not instruction.strip():
        raise KnowledgeEditVariantError("invalid or empty intelligent-edit instruction")
    if requested_variant_count not in (1, 2):
        raise KnowledgeEditVariantError("requested_variant_count must be 1 or 2")
    if not request_id.strip() or not requested_by.strip() or len(idempotency_key.strip()) < 8:
        raise KnowledgeEditVariantError("request identity, human actor and idempotency key are required")
    if selection_end <= selection_start or not selected_text:
        raise KnowledgeEditVariantError("an exact non-empty selection is required")

    request_payload = {
        "request_id": request_id,
        "knowledge_id": knowledge_id,
        "instruction_kind": instruction_kind,
        "instruction": instruction,
        "base_version": base_version,
        "selection_start": selection_start,
        "selection_end": selection_end,
        "selected_text": selected_text,
        "requested_by": requested_by,
        "requested_variant_count": requested_variant_count,
    }
    request_payload_digest = _hex_digest(
        json.dumps(request_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    )

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT request_id, request_payload_digest FROM knowledge_edit_requests "
                "WHERE request_idempotency_key = %s",
                (idempotency_key,),
            )
            replay = cur.fetchone()
        if replay is not None:
            if replay["request_payload_digest"] != request_payload_digest:
                raise knowledge.IdempotencyConflict(
                    "edit request idempotency key has different content"
                )
            return get_variant_review(conn, replay["request_id"])

        item = _knowledge_snapshot(conn, knowledge_id, lock=True)
        if item["version"] != base_version:
            raise knowledge.StaleKnowledgeWrite(
                f"offline edit is based on version {base_version}; current version is {item['version']}"
            )
        if selection_start < 0 or selection_end > len(item["markdown"]):
            raise KnowledgeEditVariantError("selection range is outside the Markdown snapshot")
        if item["markdown"][selection_start:selection_end] != selected_text:
            raise knowledge.StaleKnowledgeWrite(
                "selected text no longer matches the declared base snapshot"
            )

        selected_digest = _hex_digest(selected_text)
        scope = _scope_payload(
            knowledge_id=knowledge_id,
            base_version=base_version,
            selection_start=selection_start,
            selection_end=selection_end,
            selected_text_digest=selected_digest,
            instruction_kind=instruction_kind,
            instruction=instruction,
            requested_variant_count=requested_variant_count,
        )
        conn.execute(
            """
            INSERT INTO knowledge_edit_requests (
                request_id, knowledge_id, instruction_kind, instruction, base_version,
                selection_start, selection_end, selected_text_digest,
                selected_text_snapshot, requested_variant_count, request_scope_digest,
                replacement_markdown, status, requested_by,
                request_idempotency_key, request_payload_digest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL,
                      'queued_for_hermes', %s, %s, %s)
            """,
            (
                request_id,
                knowledge_id,
                instruction_kind,
                instruction,
                base_version,
                selection_start,
                selection_end,
                selected_digest,
                selected_text,
                requested_variant_count,
                _payload_digest(scope),
                requested_by,
                idempotency_key,
                request_payload_digest,
            ),
        )
        created = get_variant_review(conn, request_id)
    return created


def _execution_result_item(
    conn: psycopg.Connection,
    execution_result_id: str,
    result_ref: str,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT i.*, e.producer, e.task_contract_ref
              FROM execution_result_items i
              JOIN execution_results e
                ON e.execution_result_id = i.execution_result_id
             WHERE i.execution_result_id = %s AND i.result_id = %s
            """,
            (execution_result_id, result_ref),
        )
        row = cur.fetchone()
    if row is None:
        raise knowledge.KnowledgeNotFound(
            f"unknown execution result item: {execution_result_id}/{result_ref}"
        )
    return dict(row)


def _validate_candidate_payload(
    request: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    if result["result_kind"] != "knowledge_edit_variant":
        raise KnowledgeEditVariantError("execution result item is not a Knowledge edit variant")
    if result["schema_ref"] != VARIANT_SCHEMA_REF:
        raise KnowledgeEditVariantError("Knowledge edit variant schema_ref is not canonical")
    payload = dict(result["payload"])

    # Shape conformance comes from the vendored contract itself, not from a
    # hand-copied `required` set. The copy stated the same list Pantheon-Next
    # declares, with nothing to keep the two equal: a field added upstream would
    # simply stop being checked here, silently. The contract already carries the
    # three checks the copy performed — `required`, `additionalProperties: false`
    # and `candidate_kind: const` — so nothing is lost by deferring to it.
    #
    # What the schema cannot express stays below: every cross-field check
    # compares the candidate against *this* request, which the contract has no
    # view of.
    try:
        pantheon_contracts.validate(_VARIANT_CONTRACT, payload)
    except pantheon_contracts.ContractViolation as exc:
        # An unexpected field is worth naming plainly; the field list comes from
        # the contract rather than from a second copy of it.
        unknown = set(payload) - pantheon_contracts.declared_properties(_VARIANT_CONTRACT)
        if unknown:
            raise KnowledgeEditVariantError(
                "Knowledge edit variant payload has unsupported fields: "
                + ", ".join(sorted(unknown))
            ) from exc
        raise KnowledgeEditVariantError(str(exc)) from exc

    if payload["authority"] != CANDIDATE_AUTHORITY:
        raise KnowledgeEditVariantError("Knowledge edit variant claims forbidden authority")
    if payload["request_ref"] != request["request_id"]:
        raise KnowledgeEditVariantConflict("candidate targets another edit request")
    if payload["request_scope_digest"] != request["request_scope_digest"]:
        raise KnowledgeEditVariantConflict("candidate request scope digest does not match")
    if payload["knowledge_ref"] != request["knowledge_id"]:
        raise KnowledgeEditVariantConflict("candidate targets another Knowledge item")
    for field in ("base_version", "selection_start", "selection_end"):
        if payload[field] != request[field]:
            raise KnowledgeEditVariantConflict(f"candidate {field} does not match the request")
    expected_selected_digest = f"sha256:{request['selected_text_digest']}"
    if payload["selected_text_digest"] != expected_selected_digest:
        raise KnowledgeEditVariantConflict("candidate selection digest does not match")
    label = str(payload["variant_label"]).upper()
    if label not in VARIANT_LABELS:
        raise KnowledgeEditVariantError("candidate variant label must be A or B")
    if request["requested_variant_count"] == 1 and label != "A":
        raise KnowledgeEditVariantError("single-variant requests accept label A only")
    replacement = str(payload["replacement_markdown"] or "")
    if not replacement:
        raise KnowledgeEditVariantError("candidate replacement Markdown is required")
    if payload["replacement_digest"] != _sha256(replacement):
        raise KnowledgeEditVariantConflict("candidate replacement digest does not match")
    payload["variant_label"] = label
    payload["replacement_markdown"] = replacement
    return payload


def _project_execution_result_variant_inner(
    conn: psycopg.Connection,
    *,
    execution_result_id: str,
    result_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    if len(idempotency_key.strip()) < 8:
        raise KnowledgeEditVariantError("projection idempotency key is required")

    # Own the transaction before reading the Execution Result. With psycopg's
    # autocommit=False, reading it first would create an implicit outer
    # transaction and reduce the projection write to a savepoint that the API
    # connection close could roll back.
    with conn.transaction():
        result = _execution_result_item(conn, execution_result_id, result_ref)
        payload = dict(result["payload"])
        request_id = str(payload.get("request_ref") or "")
        if not request_id:
            raise KnowledgeEditVariantError("candidate request_ref is required")
        projection_digest = _payload_digest(
            {
                "execution_result_id": execution_result_id,
                "result_ref": result_ref,
                "source_payload_digest": result["payload_digest"],
            }
        )

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT request_id, payload_digest FROM knowledge_edit_variants "
                "WHERE idempotency_key = %s",
                (idempotency_key,),
            )
            replay = cur.fetchone()
        if replay is not None:
            if replay["request_id"] != request_id or replay["payload_digest"] != projection_digest:
                raise knowledge.IdempotencyConflict(
                    "variant projection idempotency key belongs to another result"
                )
            return get_variant_review(conn, request_id)

        request = _request_row(conn, request_id, lock=True)
        if request["status"] not in {"queued_for_hermes", "proposed"}:
            raise KnowledgeEditVariantConflict(
                f"variant cannot be projected from status {request['status']}"
            )
        item = _knowledge_snapshot(conn, request["knowledge_id"], lock=True)
        if _scope_status(request, item) != "current":
            raise KnowledgeEditVariantConflict(
                "Knowledge changed before the execution result was projected"
            )
        payload = _validate_candidate_payload(request, result)
        producer = dict(result.get("producer") or {})
        proposed_by = "@".join(
            part for part in (
                str(producer.get("implementation") or "execution-result"),
                str(producer.get("version") or ""),
            ) if part
        )
        variant_id = f"edit-variant-{uuid.uuid4().hex}"
        try:
            conn.execute(
                """
                INSERT INTO knowledge_edit_variants (
                    variant_id, request_id, variant_label, replacement_markdown,
                    replacement_digest, rationale, source_refs, limitations,
                    source_execution_result_id, source_result_ref, source_payload_digest,
                    proposed_by, idempotency_key, payload_digest
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s)
                """,
                (
                    variant_id,
                    request_id,
                    payload["variant_label"],
                    payload["replacement_markdown"],
                    payload["replacement_digest"],
                    payload.get("rationale"),
                    Jsonb(payload.get("source_refs") or []),
                    Jsonb(payload.get("limitations") or []),
                    execution_result_id,
                    result_ref,
                    result["payload_digest"],
                    proposed_by,
                    idempotency_key,
                    projection_digest,
                ),
            )
        except psycopg.errors.UniqueViolation as exc:
            raise knowledge.IdempotencyConflict(
                f"variant {payload['variant_label']} or execution result item is already projected"
            ) from exc
        _insert_event(
            conn,
            request_id=request_id,
            event_type="variant_projected",
            actor=proposed_by,
            actor_kind="system",
            idempotency_key=f"event:{idempotency_key}",
            payload={
                "variant_id": variant_id,
                "variant_label": payload["variant_label"],
                "execution_result_id": execution_result_id,
                "result_ref": result_ref,
                "replacement_digest": payload["replacement_digest"],
                "knowledge_mutated": False,
                "variant_selected": False,
                "evidence_admitted": False,
            },
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM knowledge_edit_variants WHERE request_id = %s",
                (request_id,),
            )
            projected_count = cur.fetchone()[0]
        if projected_count >= request["requested_variant_count"]:
            conn.execute(
                "UPDATE knowledge_edit_requests SET status = 'proposed', "
                "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s",
                (request_id,),
            )
        projected = get_variant_review(conn, request_id)
    return projected


def select_variant(
    conn: psycopg.Connection,
    *,
    request_id: str,
    variant_id: str,
    actor: str,
    idempotency_key: str,
) -> dict[str, Any]:
    payload = {"request_id": request_id, "variant_id": variant_id, "actor": actor}

    # Idempotency lookup and selection are one top-level transaction. A lookup
    # before this block would open an implicit transaction and turn the actual
    # selection into a savepoint.
    with conn.transaction():
        replay = _event_by_key(conn, idempotency_key)
        if replay is not None:
            if replay["request_id"] != request_id or replay["payload_digest"] != _payload_digest(payload):
                raise knowledge.IdempotencyConflict(
                    "variant selection idempotency key belongs to another review event"
                )
            return get_variant_review(conn, request_id)

        request = _request_row(conn, request_id, lock=True)
        if request["status"] != "proposed":
            raise KnowledgeEditVariantConflict(
                f"variant cannot be selected from status {request['status']}"
            )
        variant = _variant_row(conn, variant_id)
        if variant["request_id"] != request_id:
            raise KnowledgeEditVariantError("variant does not belong to this edit request")
        conn.execute(
            "UPDATE knowledge_edit_requests SET selected_variant_id = %s, selected_by = %s, "
            "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s",
            (variant_id, actor, request_id),
        )
        _insert_event(
            conn,
            request_id=request_id,
            event_type="variant_selected",
            actor=actor,
            actor_kind="human",
            idempotency_key=idempotency_key,
            payload={
                "variant_id": variant_id,
                "variant_label": variant["variant_label"],
                "replacement_digest": variant["replacement_digest"],
                "edit_applied": False,
                "knowledge_mutated": False,
                "evidence_admitted": False,
            },
        )
        selected = get_variant_review(conn, request_id)
    return selected


def reject_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    actor: str,
    reason: str,
    idempotency_key: str,
) -> dict[str, Any]:
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise KnowledgeEditVariantError("rejection reason is required")
    payload = {"request_id": request_id, "actor": actor, "reason": normalized_reason}

    with conn.transaction():
        replay = _event_by_key(conn, idempotency_key)
        if replay is not None:
            if replay["request_id"] != request_id or replay["payload_digest"] != _payload_digest(payload):
                raise knowledge.IdempotencyConflict(
                    "rejection idempotency key belongs to another review event"
                )
            return get_variant_review(conn, request_id)

        request = _request_row(conn, request_id, lock=True)
        if request["status"] not in {"queued_for_hermes", "proposed"}:
            raise KnowledgeEditVariantConflict(
                f"edit request cannot be rejected from status {request['status']}"
            )
        conn.execute(
            "UPDATE knowledge_edit_requests SET status = 'rejected', "
            "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s",
            (request_id,),
        )
        _insert_event(
            conn,
            request_id=request_id,
            event_type="request_rejected",
            actor=actor,
            actor_kind="human",
            idempotency_key=idempotency_key,
            payload={
                "reason": normalized_reason,
                "knowledge_mutated": False,
                "task_authorized": False,
                "evidence_admitted": False,
            },
        )
        rejected = get_variant_review(conn, request_id)
    return rejected


def apply_selected_variant(
    conn: psycopg.Connection,
    *,
    request_id: str,
    actor: str,
    idempotency_key: str,
    policy_client: PolicyClient | None = None,
    decision_payload: dict[str, Any] | None = None,
    required_ceiling: str = "C2",
) -> dict[str, Any]:
    """Apply exactly the variant selected under the same transaction lock.

    The wrapper owns one top-level transaction from selected-variant validation
    through the existing Knowledge apply owner. apply_edit_request therefore
    runs as a nested savepoint intentionally: the request row remains locked,
    so another review action cannot change selected_variant_id or the prepared
    replacement between review and persistence.
    """
    variant: dict[str, Any] | None = None

    def record_application(
        active: psycopg.Connection, applied_result: dict[str, Any]
    ) -> None:
        """Write the variant audit inside the same accepted effect."""
        if variant is None or _event_by_key(active, idempotency_key) is not None:
            return
        _insert_event(
            active,
            request_id=request_id,
            event_type="variant_applied",
            actor=actor,
            actor_kind="human",
            idempotency_key=idempotency_key,
            payload={
                "variant_id": variant["variant_id"],
                "variant_label": variant["variant_label"],
                "replacement_digest": variant["replacement_digest"],
                "applied_version": applied_result["knowledge"]["version"],
                "review_status_promoted": False,
                "evidence_admitted": False,
            },
        )

    with conn.transaction():
        request = _request_row(conn, request_id, lock=True)
        if request["status"] != "applied":
            if request["status"] != "proposed":
                raise KnowledgeEditVariantConflict(
                    f"selected variant cannot be applied from status {request['status']}"
                )
            if not request.get("selected_variant_id"):
                raise KnowledgeEditVariantError(
                    "select one proposal variant before applying it"
                )
            variant = _variant_row(conn, request["selected_variant_id"])
            if variant["request_id"] != request_id:
                raise KnowledgeEditVariantError(
                    "selected variant does not belong to this request"
                )

            # Prepare exactly the immutable variant currently selected while
            # the request row remains locked through the delegated apply.
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE knowledge_edit_requests SET replacement_markdown = %s, "
                    "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s "
                    "AND selected_variant_id = %s AND status = 'proposed'",
                    (variant["replacement_markdown"], request_id, variant["variant_id"]),
                )
                if cur.rowcount != 1:
                    raise KnowledgeEditVariantConflict(
                        "selected variant changed before application"
                    )

        apply_conflict: knowledge.StaleKnowledgeWrite | None = None
        applied: dict[str, Any] | None = None
        try:
            applied = knowledge.apply_edit_request(
                conn,
                request_id=request_id,
                actor=actor,
                actor_kind="human",
                idempotency_key=idempotency_key,
                on_applied=record_application,
                policy_client=policy_client,
                decision_payload=decision_payload,
                required_ceiling=required_ceiling,
            )
        except knowledge.StaleKnowledgeWrite as exc:
            # apply_edit_request has already converted the still-proposed request
            # to durable conflict. Catch inside this enclosing transaction so that
            # transition commits instead of being undone by the wrapper rollback.
            apply_conflict = exc
        review = get_variant_review(conn, request_id)

    if apply_conflict is not None:
        raise apply_conflict
    assert applied is not None
    return {**applied, "review": review}


def project_execution_result_variant(
    conn: psycopg.Connection,
    *,
    execution_result_id: str,
    result_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Project a candidate and persist a stale-scope conflict after rollback."""
    try:
        return _project_execution_result_variant_inner(
            conn,
            execution_result_id=execution_result_id,
            result_ref=result_ref,
            idempotency_key=idempotency_key,
        )
    except KnowledgeEditVariantConflict:
        # The failed projection transaction has rolled back. Re-open one
        # explicit transaction for the durable conflict transition so no
        # preliminary read can turn that write into a savepoint.
        with conn.transaction():
            result = _execution_result_item(conn, execution_result_id, result_ref)
            request_id = str(dict(result.get("payload") or {}).get("request_ref") or "")
            if request_id:
                try:
                    request = _request_row(conn, request_id)
                    item = _knowledge_snapshot(conn, request["knowledge_id"])
                except knowledge.KnowledgeNotFound:
                    pass
                else:
                    if (
                        request["status"] in {"queued_for_hermes", "proposed"}
                        and _scope_status(request, item) != "current"
                    ):
                        conn.execute(
                            "UPDATE knowledge_edit_requests SET status = 'conflict', "
                            "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s "
                            "AND status IN ('queued_for_hermes', 'proposed')",
                            (request_id,),
                        )
        raise
