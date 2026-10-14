"""Human-attention Decision Requests with typed immutable resolutions.

A Decision Request is an unresolved Gate. Questions resolve to HumanResponse;
validation, approval and arbitration resolve to Decision records. None of these
objects transitions a WorkIssue, resumes Hermes, admits Evidence or proves an
external effect merely because it was recorded.

A non-question request may bind one exact consequential effect before review.
Those bounds are copied unchanged into the immutable Decision record. Runtime
effect owners may compare that Decision with their own EffectExpectation; they
may not manufacture Decision fields after the human has decided.
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

from . import pantheon_contracts


MIGRATION = Path(__file__).resolve().parent / "sql" / "018_decision_requests.sql"
HUMAN_RESPONSE_MIGRATION = (
    Path(__file__).resolve().parent / "sql" / "038_human_response_resolution.sql"
)
EFFECT_BINDING_MIGRATION = (
    Path(__file__).resolve().parent / "sql" / "039_decision_effect_binding.sql"
)
REQUEST_SCHEMA = pantheon_contracts.schema_path("decision_request")
RESPONSE_SCHEMA = pantheon_contracts.schema_path("human_response")
DECISION_SCHEMA = pantheon_contracts.schema_path("mvp_governed_loop_objects")

DECISION_VALUES = frozenset({"approve", "refuse", "request_revision", "request_more_evidence"})
DECISION_TYPES = frozenset({"question", "validation", "approval", "arbitration"})
RESPONSE_MODES = frozenset({"decision_value", "single_option", "multiple_options", "free_text"})
PRIORITIES = frozenset({"low", "normal", "high", "urgent"})
APPROVAL_LEVELS = frozenset({"C0", "C1", "C2", "C3", "C4", "C5"})


class DecisionRequestError(ValueError):
    """Base refusal for the Decision Request aggregate."""


class DecisionRequestNotFound(DecisionRequestError):
    pass


class DecisionRecordNotFound(DecisionRequestError):
    pass


class HumanResponseNotFound(DecisionRequestError):
    pass


class DecisionRequestConflict(DecisionRequestError):
    pass


class StaleDecisionRequest(DecisionRequestError):
    pass


def _event_id() -> str:
    return f"decision-event-{uuid.uuid4().hex}"


def _clean(mapping: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in mapping.items()
    }


def _load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DecisionRequestError(f"unable to load governed schema {path.name}: {exc}") from exc
    if not isinstance(schema, dict):
        raise DecisionRequestError(f"governed schema {path.name} must be an object")
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=1)
def _request_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        _load_schema(REQUEST_SCHEMA),
        format_checker=jsonschema.FormatChecker(),
    )


@lru_cache(maxsize=1)
def _response_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        _load_schema(RESPONSE_SCHEMA),
        format_checker=jsonschema.FormatChecker(),
    )


@lru_cache(maxsize=1)
def _decision_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        _load_schema(DECISION_SCHEMA),
        format_checker=jsonschema.FormatChecker(),
    )


def _digest(value: str | dict[str, Any]) -> dict[str, str]:
    if isinstance(value, dict):
        if value.get("algorithm") != "sha256" or not isinstance(value.get("value"), str):
            raise DecisionRequestError("digest must use sha256 and provide a value")
        value = value["value"]
    normalized = str(value).strip().lower()
    if len(normalized) != 64 or any(character not in "0123456789abcdef" for character in normalized):
        raise DecisionRequestError("digest must be a 64-character lowercase sha256 value")
    return {"algorithm": "sha256", "value": normalized}


def _string_list(values: Iterable[str] | None, *, field: str) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = str(value).strip()
        if not item:
            raise DecisionRequestError(f"{field} cannot contain an empty item")
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def _normalize_scope(value: dict[str, Any] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DecisionRequestError("decision_scope must be an object")
    scope_type = str(value.get("scope_type") or "").strip()
    scope_id = str(value.get("scope_id") or "").strip()
    if not scope_type or not scope_id:
        raise DecisionRequestError("decision_scope requires scope_type and scope_id")
    if set(value) != {"scope_type", "scope_id"}:
        raise DecisionRequestError("decision_scope accepts only scope_type and scope_id")
    return {"scope_type": scope_type, "scope_id": scope_id}


def _normalize_expiry(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise DecisionRequestError("expires_at must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise DecisionRequestError("expires_at must include a timezone")
    return parsed.isoformat()


def _normalize_effect_binding(
    *,
    decision_type: str,
    approval_level: str | None,
    decision_scope: dict[str, Any] | None,
    expires_at: datetime | str | None,
) -> tuple[str | None, dict[str, str] | None, str | None]:
    level = str(approval_level).strip() if approval_level is not None else None
    scope = _normalize_scope(decision_scope)
    expiry = _normalize_expiry(expires_at)
    values = (level, scope, expiry)
    if any(value is not None for value in values) and not all(value is not None for value in values):
        raise DecisionRequestError(
            "effect-bound Decision Request requires approval_level, decision_scope and expires_at together"
        )
    if level is not None and level not in APPROVAL_LEVELS:
        raise DecisionRequestError("approval_level must be C0..C5")
    if decision_type == "question" and level is not None:
        raise DecisionRequestError("question Decision Requests cannot carry effect-bound Decision fields")
    return level, scope, expiry


def _normalize_options(
    options: Iterable[dict[str, Any]] | None,
    *,
    response_mode: str,
    recommendation_candidate: str | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ordinal, raw in enumerate(options or []):
        option_id = str(raw.get("option_id") or "").strip()
        label = str(raw.get("label") or "").strip()
        consequence = str(raw.get("consequence") or "").strip()
        if not option_id or not label or not consequence:
            raise DecisionRequestError("each Decision option requires id, label and consequence")
        if option_id in seen:
            raise DecisionRequestError(f"duplicate Decision option: {option_id}")
        seen.add(option_id)
        normalized.append(
            {
                "option_id": option_id,
                "label": label,
                "consequence": consequence,
                "limitations": _string_list(raw.get("limitations"), field="limitations"),
                "ordinal": ordinal,
            }
        )
    if response_mode in {"single_option", "multiple_options"} and len(normalized) < 2:
        raise DecisionRequestError("option response modes require at least two options")
    if response_mode in {"decision_value", "free_text"} and normalized:
        raise DecisionRequestError("decision_value and free_text requests cannot carry options")
    if recommendation_candidate is not None and recommendation_candidate not in seen:
        raise DecisionRequestError("recommendation_candidate must reference one request option")
    return normalized


def _request_row(conn: psycopg.Connection, request_id: str, *, lock: bool = False) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM agency_decision_requests WHERE request_id = %s{suffix}",
            (request_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise DecisionRequestNotFound(f"unknown Decision Request: {request_id}")
    return dict(row)


def _decision_row(conn: psycopg.Connection, decision_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM agency_decision_records WHERE decision_id = %s", (decision_id,))
        row = cur.fetchone()
    if row is None:
        raise DecisionRecordNotFound(f"unknown Decision record: {decision_id}")
    return dict(row)


def _response_row(conn: psycopg.Connection, response_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM agency_human_responses WHERE response_id = %s", (response_id,))
        row = cur.fetchone()
    if row is None:
        raise HumanResponseNotFound(f"unknown HumanResponse: {response_id}")
    return dict(row)


def _options(conn: psycopg.Connection, request_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT option_id, label, consequence, limitations
              FROM agency_decision_options
             WHERE request_id = %s
             ORDER BY ordinal, option_id
            """,
            (request_id,),
        )
        return [_clean(dict(row)) for row in cur.fetchall()]


def _events(conn: psycopg.Connection, request_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT event_id, request_id AS request_ref, decision_id AS decision_ref,
                   response_id AS response_ref, event_type, actor,
                   expected_revision, resulting_revision,
                   idempotency_key, payload, occurred_at
              FROM agency_decision_events
             WHERE request_id = %s
             ORDER BY occurred_at, event_id
            """,
            (request_id,),
        )
        return [_clean(dict(row)) for row in cur.fetchall()]


def _request_projection(row: dict[str, Any], options: list[dict[str, Any]]) -> dict[str, Any]:
    request = _clean(row)
    projection = {
        "request_id": request["request_id"],
        "status": request["status"],
        "decision_type": request["decision_type"],
        "question": request["question"],
        "priority": request["priority"],
        "response_mode": request["response_mode"],
        "options": [
            {
                "option_id": option["option_id"],
                "label": option["label"],
                "consequence": option["consequence"],
                "limitations": option.get("limitations") or [],
            }
            for option in options
        ],
        "recommendation_candidate": request.get("recommendation_candidate"),
        "blocking": request["blocking"],
        "project_ref": request.get("project_id"),
        "work_issue_ref": request.get("work_issue_id"),
        "conversation_ref": request.get("conversation_ref"),
        "candidate_ref": request["candidate_ref"],
        "candidate_digest": _digest(request["candidate_digest"]),
        "approval_level": request.get("approval_level"),
        "decision_scope": request.get("decision_scope"),
        "expires_at": request.get("expires_at"),
        "evidence_pack_ref": request.get("evidence_pack_ref"),
        "evidence_pack_digest": _digest(request["evidence_pack_digest"]) if request.get("evidence_pack_digest") else None,
        "source_refs": request.get("source_refs") or [],
        "evidence_gaps": request.get("evidence_gaps") or [],
        "blocked_action": request.get("blocked_action"),
        "next_safe_action": request.get("next_safe_action"),
        "decision_surface": request["decision_surface"],
        "decision_owner": request["decision_owner"],
        "created_by": request["created_by"],
        "created_at": request["created_at"],
        "revision": request["revision"],
        "resolved_decision_ref": request.get("resolved_decision_id"),
        "resolved_response_ref": request.get("resolved_response_id"),
        "resolved_at": request.get("resolved_at"),
        "cancelled_by": request.get("cancelled_by"),
        "cancelled_at": request.get("cancelled_at"),
    }
    try:
        _request_validator().validate(projection)
    except jsonschema.ValidationError as exc:
        raise DecisionRequestError(f"stored Decision Request violates its governed contract: {exc}") from exc
    return projection


def _human_response_projection(row: dict[str, Any]) -> dict[str, Any]:
    response = _clean(row)
    projection = {
        "response_id": response["response_id"],
        "request_id": response["request_id"],
        "responded_by": response["responded_by"],
        "identity_assurance": response["identity_assurance"],
        "authenticated_principal": response.get("authenticated_principal"),
        "selected_option_ids": response.get("selected_option_ids") or [],
        "response_text": response.get("response_text"),
        "candidate_digest": _digest(response["candidate_digest"]),
        "recorded_at": response["recorded_at"],
    }
    try:
        _response_validator().validate(projection)
    except jsonschema.ValidationError as exc:
        raise DecisionRequestError(f"stored HumanResponse violates its governed contract: {exc}") from exc
    return projection


def _decision_projection(row: dict[str, Any]) -> dict[str, Any]:
    decision = _clean(row)
    projection = {
        "object_type": "decision_record",
        "object_id": decision["decision_id"],
        "decision_id": decision["decision_id"],
        "status": decision["status"],
        "applies_to": decision["applies_to"],
        "related_evidence_pack": decision.get("related_evidence_pack"),
        "decision": decision["decision"],
        "decided_by": decision["decided_by"],
        "identity_assurance": decision["identity_assurance"],
        "authenticated_principal": decision.get("authenticated_principal"),
        "recorded_at": decision["recorded_at"],
        "supersedes_decision_id": decision.get("supersedes_decision_id"),
        "candidate_digest": _digest(decision["candidate_digest"]),
        "approval_level": decision.get("approval_level"),
        "scope": decision.get("scope"),
        "object_identity": decision.get("object_identity"),
        "content_digest": decision.get("content_digest"),
        "expires_at": decision.get("expires_at"),
        "signature": decision.get("signature"),
        "evidence_pack_digest": _digest(decision["evidence_pack_digest"]) if decision.get("evidence_pack_digest") else None,
        "decision_surface": decision["decision_surface"],
        "rationale": decision.get("rationale"),
        "consequences": decision.get("consequences") or {},
        "governance_refs": [
            "docs/governance/USER_DECISION_GATE.md",
            "docs/governance/MVP_GOVERNED_TASK_LOOP.md",
        ],
    }
    projection = {key: value for key, value in projection.items() if value is not None}
    try:
        _decision_validator().validate(projection)
    except jsonschema.ValidationError as exc:
        raise DecisionRequestError(f"stored Decision record violates its governed contract: {exc}") from exc
    return projection


def get_request(conn: psycopg.Connection, request_id: str) -> dict[str, Any]:
    row = _request_row(conn, request_id)
    request = _request_projection(row, _options(conn, request_id))
    response = (
        _human_response_projection(_response_row(conn, row["resolved_response_id"]))
        if row.get("resolved_response_id")
        else None
    )
    decision = (
        _decision_projection(_decision_row(conn, row["resolved_decision_id"]))
        if row.get("resolved_decision_id")
        else None
    )
    return {
        "decision_request": request,
        "human_response": response,
        "decision_record": decision,
        "events": _events(conn, request_id),
        "attention_required": request["status"] == "pending",
        "request_is_not_decision": True,
        "human_response_is_not_decision": True,
        "resolution_is_not_authorization": True,
        "decision_is_not_execution": True,
    }


def get_response(conn: psycopg.Connection, response_id: str) -> dict[str, Any]:
    return {
        "human_response": _human_response_projection(_response_row(conn, response_id)),
        "human_response_is_not_decision": True,
        "response_is_not_authorization": True,
        "response_is_not_evidence": True,
    }


def get_decision(conn: psycopg.Connection, decision_id: str) -> dict[str, Any]:
    return {
        "decision_record": _decision_projection(_decision_row(conn, decision_id)),
        "decision_is_not_execution": True,
        "result_validated": False,
    }


def policy_decision_payload(
    conn: psycopg.Connection,
    decision_id: str,
    *,
    expectation: dict[str, Any],
) -> dict[str, Any]:
    """Project one persisted Decision into the PDP transport shape.

    This is a read projection only. It never adds authority or fills missing
    Decision material. Direct consequential effects fail closed unless the exact
    canonical record is an authenticated, approved, effect-bound and signed
    Decision.
    """
    record = get_decision(conn, decision_id)["decision_record"]
    if record.get("decision") != "approve":
        raise DecisionRequestError("consequential effect requires an approved Decision record")
    if record.get("identity_assurance") != "authenticated":
        raise DecisionRequestError("consequential effect requires authenticated Decision identity")
    fields = (
        "decision_id",
        "decided_by",
        "approval_level",
        "scope",
        "object_identity",
        "content_digest",
        "expires_at",
        "signature",
    )
    missing = [field for field in fields if record.get(field) in (None, "")]
    if missing:
        raise DecisionRequestError(
            "canonical Decision is not effect-bound and signed; missing: " + ", ".join(missing)
        )
    return {
        "decision": {field: record[field] for field in fields},
        "expectation": dict(expectation),
    }


def _event_replayed(
    conn: psycopg.Connection,
    *,
    request_id: str,
    event_type: str,
    idempotency_key: str,
    payload: dict[str, Any],
) -> bool:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT request_id, event_type, payload FROM agency_decision_events WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return False
    if row["request_id"] != request_id or row["event_type"] != event_type or (row["payload"] or {}) != payload:
        raise DecisionRequestConflict("idempotency key belongs to another Decision Request effect")
    return True


def _insert_event(
    conn: psycopg.Connection,
    *,
    request_id: str,
    event_type: str,
    actor: str,
    expected_revision: int,
    idempotency_key: str,
    payload: dict[str, Any],
    decision_id: str | None = None,
    response_id: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO agency_decision_events (
            event_id, request_id, decision_id, response_id, event_type, actor,
            expected_revision, resulting_revision, idempotency_key, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            _event_id(), request_id, decision_id, response_id, event_type, actor,
            expected_revision, expected_revision + 1, idempotency_key,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        ),
    )


def create_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    decision_type: str,
    question: str,
    priority: str,
    response_mode: str,
    blocking: bool,
    candidate_ref: str,
    candidate_digest: str | dict[str, str],
    decision_surface: str,
    decision_owner: str,
    created_by: str,
    idempotency_key: str,
    options: Iterable[dict[str, Any]] | None = None,
    recommendation_candidate: str | None = None,
    project_ref: str | None = None,
    work_issue_ref: str | None = None,
    conversation_ref: str | None = None,
    approval_level: str | None = None,
    decision_scope: dict[str, Any] | None = None,
    expires_at: datetime | str | None = None,
    evidence_pack_ref: str | None = None,
    evidence_pack_digest: str | dict[str, str] | None = None,
    source_refs: Iterable[str] | None = None,
    evidence_gaps: Iterable[str] | None = None,
    blocked_action: str | None = None,
    next_safe_action: str | None = None,
) -> dict[str, Any]:
    if decision_type not in DECISION_TYPES:
        raise DecisionRequestError(f"unsupported decision_type: {decision_type!r}")
    if priority not in PRIORITIES:
        raise DecisionRequestError(f"unsupported priority: {priority!r}")
    if response_mode not in RESPONSE_MODES:
        raise DecisionRequestError(f"unsupported response_mode: {response_mode!r}")
    if decision_type == "question" and response_mode == "decision_value":
        raise DecisionRequestError("question Decision Requests cannot use decision_value response mode")
    question = str(question).strip()
    if not question:
        raise DecisionRequestError("Decision Request question is required")
    if blocking and not work_issue_ref:
        raise DecisionRequestError("blocking Decision Request requires a WorkIssue")
    digest = _digest(candidate_digest)
    evidence_digest = _digest(evidence_pack_digest) if evidence_pack_digest else None
    if bool(evidence_pack_ref) != bool(evidence_digest):
        raise DecisionRequestError("Evidence Pack reference and digest must be supplied together")
    level, bounded_scope, expiry = _normalize_effect_binding(
        decision_type=decision_type,
        approval_level=approval_level,
        decision_scope=decision_scope,
        expires_at=expires_at,
    )
    normalized_options = _normalize_options(
        options,
        response_mode=response_mode,
        recommendation_candidate=recommendation_candidate,
    )
    immutable_payload = {
        "request_id": request_id,
        "decision_type": decision_type,
        "question": question,
        "priority": priority,
        "response_mode": response_mode,
        "options": [{key: value for key, value in option.items() if key != "ordinal"} for option in normalized_options],
        "recommendation_candidate": recommendation_candidate,
        "blocking": bool(blocking),
        "project_ref": project_ref,
        "work_issue_ref": work_issue_ref,
        "conversation_ref": conversation_ref,
        "candidate_ref": str(candidate_ref).strip(),
        "candidate_digest": digest,
        "approval_level": level,
        "decision_scope": bounded_scope,
        "expires_at": expiry,
        "evidence_pack_ref": evidence_pack_ref,
        "evidence_pack_digest": evidence_digest,
        "source_refs": _string_list(source_refs, field="source_refs"),
        "evidence_gaps": _string_list(evidence_gaps, field="evidence_gaps"),
        "blocked_action": str(blocked_action).strip() if blocked_action else None,
        "next_safe_action": str(next_safe_action).strip() if next_safe_action else None,
        "decision_surface": str(decision_surface).strip(),
        "decision_owner": str(decision_owner).strip(),
        "created_by": str(created_by).strip(),
    }
    if not immutable_payload["candidate_ref"]:
        raise DecisionRequestError("candidate_ref is required")
    if not immutable_payload["decision_surface"] or not immutable_payload["decision_owner"]:
        raise DecisionRequestError("decision_surface and decision_owner are required")
    if not immutable_payload["created_by"]:
        raise DecisionRequestError("created_by is required")

    with conn.transaction():
        if _event_replayed(
            conn,
            request_id=request_id,
            event_type="request_created",
            idempotency_key=idempotency_key,
            payload=immutable_payload,
        ):
            return get_request(conn, request_id)
        try:
            conn.execute(
                """
                INSERT INTO agency_decision_requests (
                    request_id, status, decision_type, question, priority,
                    response_mode, recommendation_candidate, blocking,
                    project_id, work_issue_id, conversation_ref,
                    candidate_ref, candidate_digest, approval_level,
                    decision_scope, expires_at,
                    evidence_pack_ref, evidence_pack_digest,
                    source_refs, evidence_gaps, blocked_action, next_safe_action,
                    decision_surface, decision_owner, created_by
                ) VALUES (
                    %s, 'pending', %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s::jsonb, %s,
                    %s, %s, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    request_id, decision_type, question, priority, response_mode,
                    recommendation_candidate, blocking, project_ref, work_issue_ref,
                    conversation_ref, immutable_payload["candidate_ref"], digest["value"],
                    level, json.dumps(bounded_scope) if bounded_scope else None, expiry,
                    evidence_pack_ref, evidence_digest["value"] if evidence_digest else None,
                    json.dumps(immutable_payload["source_refs"]),
                    json.dumps(immutable_payload["evidence_gaps"]),
                    immutable_payload["blocked_action"], immutable_payload["next_safe_action"],
                    immutable_payload["decision_surface"], immutable_payload["decision_owner"],
                    immutable_payload["created_by"],
                ),
            )
            for option in normalized_options:
                conn.execute(
                    """
                    INSERT INTO agency_decision_options (
                        request_id, option_id, label, consequence, limitations, ordinal
                    ) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                    """,
                    (
                        request_id, option["option_id"], option["label"], option["consequence"],
                        json.dumps(option["limitations"]), option["ordinal"],
                    ),
                )
        except psycopg.errors.UniqueViolation as exc:
            raise DecisionRequestConflict("Decision Request identity or pending WorkIssue blocker already exists") from exc
        except (psycopg.errors.ForeignKeyViolation, psycopg.errors.RaiseException) as exc:
            raise DecisionRequestError(str(exc)) from exc
        _insert_event(
            conn,
            request_id=request_id,
            event_type="request_created",
            actor=immutable_payload["created_by"],
            expected_revision=0,
            idempotency_key=idempotency_key,
            payload=immutable_payload,
        )
        return get_request(conn, request_id)


def _selected_and_response(
    *,
    request: dict[str, Any],
    selected_option_ids: Iterable[str] | None,
    response_text: str | None,
) -> tuple[list[str], str | None]:
    selected = _string_list(selected_option_ids, field="selected_option_ids")
    response = str(response_text).strip() if response_text else None
    option_ids = {option["option_id"] for option in request.get("options") or []}
    unknown = [option_id for option_id in selected if option_id not in option_ids]
    if unknown:
        raise DecisionRequestError(f"unknown selected Decision option: {unknown[0]}")
    return selected, response


def _validate_human_response(
    *,
    request: dict[str, Any],
    selected_option_ids: Iterable[str] | None,
    response_text: str | None,
) -> tuple[list[str], str | None]:
    selected, response = _selected_and_response(
        request=request,
        selected_option_ids=selected_option_ids,
        response_text=response_text,
    )
    mode = request["response_mode"]
    if mode == "decision_value":
        raise DecisionRequestError("question Decision Requests cannot resolve with decision_value")
    if mode == "single_option" and len(selected) != 1:
        raise DecisionRequestError("single-option question requires exactly one option")
    if mode == "multiple_options" and not selected:
        raise DecisionRequestError("multiple-option question requires at least one option")
    if mode == "free_text" and not response:
        raise DecisionRequestError("free-text question requires a response")
    if mode in {"single_option", "multiple_options"} and response:
        raise DecisionRequestError("option question cannot also carry a free-text response")
    return selected, response


def _validate_decision_response(
    *,
    request: dict[str, Any],
    decision: str,
    selected_option_ids: Iterable[str] | None,
    response_text: str | None,
) -> tuple[list[str], str | None]:
    if decision not in DECISION_VALUES:
        raise DecisionRequestError(f"unsupported decision value: {decision!r}")
    selected, response = _selected_and_response(
        request=request,
        selected_option_ids=selected_option_ids,
        response_text=response_text,
    )
    if decision == "approve":
        mode = request["response_mode"]
        if mode == "single_option" and len(selected) != 1:
            raise DecisionRequestError("single-option approval requires exactly one option")
        if mode == "multiple_options" and not selected:
            raise DecisionRequestError("multiple-option approval requires at least one option")
        if mode == "free_text" and not response:
            raise DecisionRequestError("free-text approval requires a response")
        if mode == "decision_value" and (selected or response):
            raise DecisionRequestError("decision-value approval cannot carry an option or free-text response")
    elif selected or response:
        raise DecisionRequestError("refusal, revision or more-evidence decisions cannot claim an approved response")
    return selected, response


def _validate_identity(
    identity_assurance: str,
    authenticated_principal: dict[str, Any] | None,
) -> None:
    if identity_assurance not in {"declared", "authenticated"}:
        raise DecisionRequestError("identity_assurance must be declared or authenticated")
    if identity_assurance == "authenticated":
        if not isinstance(authenticated_principal, dict):
            raise DecisionRequestError("authenticated identity assurance requires authenticated_principal")
        if not authenticated_principal.get("user_id") or not authenticated_principal.get("identity_provider"):
            raise DecisionRequestError("authenticated_principal requires user_id and identity_provider")
    elif authenticated_principal is not None:
        raise DecisionRequestError("declared identity assurance cannot carry authenticated_principal")


def _check_pending_revision(row: dict[str, Any], expected_revision: int) -> None:
    if row["status"] != "pending":
        raise DecisionRequestConflict("Decision Request is no longer pending")
    if row["revision"] != expected_revision:
        raise StaleDecisionRequest(
            f"stale Decision Request revision: expected {expected_revision}, current {row['revision']}"
        )


def resolve_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    decided_by: str,
    identity_assurance: str,
    expected_revision: int,
    idempotency_key: str,
    decision_id: str | None = None,
    response_id: str | None = None,
    decision: str | None = None,
    selected_option_ids: Iterable[str] | None = None,
    response_text: str | None = None,
    authenticated_principal: dict[str, Any] | None = None,
    rationale: str | None = None,
    signature: str | None = None,
) -> dict[str, Any]:
    _validate_identity(identity_assurance, authenticated_principal)
    actor = str(decided_by).strip()
    if not actor:
        raise DecisionRequestError("human actor is required")

    with conn.transaction():
        row = _request_row(conn, request_id, lock=True)
        request = _request_projection(row, _options(conn, request_id))

        if request["decision_type"] == "question":
            response_identity = str(response_id or "").strip()
            if not response_identity:
                raise DecisionRequestError("question resolution requires response_id")
            if decision_id is not None or decision is not None:
                raise DecisionRequestError("question resolution cannot carry Decision identity or value")
            if signature is not None:
                raise DecisionRequestError("HumanResponse cannot carry a Decision issuer signature")
            if rationale is not None and str(rationale).strip():
                raise DecisionRequestError("question resolution cannot carry Decision rationale")
            selected, response = _validate_human_response(
                request=request,
                selected_option_ids=selected_option_ids,
                response_text=response_text,
            )
            payload = {
                "response_id": response_identity,
                "responded_by": actor,
                "selected_option_ids": selected,
                "response_text": response,
                "identity_assurance": identity_assurance,
                "authenticated_principal": authenticated_principal,
                "candidate_digest": request["candidate_digest"],
            }
            if _event_replayed(
                conn,
                request_id=request_id,
                event_type="request_resolved",
                idempotency_key=idempotency_key,
                payload=payload,
            ):
                return get_request(conn, request_id)
            _check_pending_revision(row, expected_revision)
            try:
                conn.execute(
                    """
                    INSERT INTO agency_human_responses (
                        response_id, request_id, responded_by, identity_assurance,
                        authenticated_principal, selected_option_ids, response_text,
                        candidate_digest
                    ) VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                    """,
                    (
                        response_identity,
                        request_id,
                        actor,
                        identity_assurance,
                        json.dumps(authenticated_principal) if authenticated_principal else None,
                        json.dumps(selected),
                        response,
                        request["candidate_digest"]["value"],
                    ),
                )
                conn.execute(
                    """
                    UPDATE agency_decision_requests
                       SET status = 'resolved', resolved_response_id = %s,
                           resolved_at = clock_timestamp(), revision = revision + 1,
                           updated_at = clock_timestamp()
                     WHERE request_id = %s AND status = 'pending' AND revision = %s
                    """,
                    (response_identity, request_id, expected_revision),
                )
            except psycopg.errors.UniqueViolation as exc:
                raise DecisionRequestConflict("HumanResponse identity exists or request is already resolved") from exc
            _insert_event(
                conn,
                request_id=request_id,
                response_id=response_identity,
                event_type="request_resolved",
                actor=actor,
                expected_revision=expected_revision,
                idempotency_key=idempotency_key,
                payload=payload,
            )
            return get_request(conn, request_id)

        if response_id is not None:
            raise DecisionRequestError("decision resolution cannot carry response_id")
        decision_identity = str(decision_id or "").strip()
        if not decision_identity:
            raise DecisionRequestError("decision resolution requires decision_id")
        if decision is None:
            raise DecisionRequestError("decision resolution requires decision value")
        selected, response = _validate_decision_response(
            request=request,
            decision=decision,
            selected_option_ids=selected_option_ids,
            response_text=response_text,
        )
        effect_bound = request.get("approval_level") is not None
        signature_value = str(signature).strip() if signature else None
        if signature_value and not effect_bound:
            raise DecisionRequestError("unbound Decision cannot carry an issuer signature")
        if signature_value and identity_assurance != "authenticated":
            raise DecisionRequestError("issuer signature requires authenticated identity assurance")
        payload = {
            "decision_id": decision_identity,
            "decision": decision,
            "decided_by": actor,
            "selected_option_ids": selected,
            "response_text": response,
            "identity_assurance": identity_assurance,
            "authenticated_principal": authenticated_principal,
            "rationale": str(rationale).strip() if rationale else None,
            "candidate_digest": request["candidate_digest"],
            "approval_level": request.get("approval_level"),
            "scope": request.get("decision_scope"),
            "object_identity": request["candidate_ref"] if effect_bound else None,
            "content_digest": request["candidate_digest"]["value"] if effect_bound else None,
            "expires_at": request.get("expires_at"),
            "signature": signature_value,
        }
        if _event_replayed(
            conn,
            request_id=request_id,
            event_type="request_resolved",
            idempotency_key=idempotency_key,
            payload=payload,
        ):
            return get_request(conn, request_id)
        _check_pending_revision(row, expected_revision)
        consequences = {
            "request_id": request_id,
            "decision_type": request["decision_type"],
            "response_mode": request["response_mode"],
            "selected_option_ids": selected,
            "response_text": response,
            "blocking_work_issue_ref": request.get("work_issue_ref") if request["blocking"] else None,
            "work_issue_transitioned": False,
            "runtime_continuation_authorized": False,
            "action_executed": False,
            "result_validated": False,
        }
        try:
            conn.execute(
                """
                INSERT INTO agency_decision_records (
                    decision_id, request_id, applies_to, related_evidence_pack,
                    decision, decided_by, identity_assurance,
                    authenticated_principal, candidate_digest,
                    approval_level, scope, object_identity, content_digest,
                    expires_at, signature,
                    evidence_pack_digest, decision_surface, rationale, consequences
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s::jsonb, %s, %s, %s, %s,
                    %s, %s, %s, %s::jsonb
                )
                """,
                (
                    decision_identity, request_id, request_id, request.get("evidence_pack_ref"),
                    decision, actor, identity_assurance,
                    json.dumps(authenticated_principal) if authenticated_principal else None,
                    request["candidate_digest"]["value"],
                    request.get("approval_level"),
                    json.dumps(request.get("decision_scope")) if effect_bound else None,
                    request["candidate_ref"] if effect_bound else None,
                    request["candidate_digest"]["value"] if effect_bound else None,
                    request.get("expires_at") if effect_bound else None,
                    signature_value,
                    request["evidence_pack_digest"]["value"] if request.get("evidence_pack_digest") else None,
                    request["decision_surface"], payload["rationale"],
                    json.dumps(consequences, sort_keys=True, separators=(",", ":")),
                ),
            )
            conn.execute(
                """
                UPDATE agency_decision_requests
                   SET status = 'resolved', resolved_decision_id = %s,
                       resolved_at = clock_timestamp(), revision = revision + 1,
                       updated_at = clock_timestamp()
                 WHERE request_id = %s AND status = 'pending' AND revision = %s
                """,
                (decision_identity, request_id, expected_revision),
            )
        except psycopg.errors.UniqueViolation as exc:
            raise DecisionRequestConflict("Decision identity exists or request is already resolved") from exc
        except psycopg.errors.RaiseException as exc:
            raise DecisionRequestError(str(exc)) from exc
        _insert_event(
            conn,
            request_id=request_id,
            decision_id=decision_identity,
            event_type="request_resolved",
            actor=actor,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        return get_request(conn, request_id)


def cancel_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    cancelled_by: str,
    expected_revision: int,
    idempotency_key: str,
    rationale: str,
) -> dict[str, Any]:
    rationale = str(rationale).strip()
    if not rationale:
        raise DecisionRequestError("Decision Request cancellation requires a rationale")
    payload = {"cancelled_by": cancelled_by, "rationale": rationale}
    with conn.transaction():
        if _event_replayed(
            conn,
            request_id=request_id,
            event_type="request_cancelled",
            idempotency_key=idempotency_key,
            payload=payload,
        ):
            return get_request(conn, request_id)
        row = _request_row(conn, request_id, lock=True)
        _check_pending_revision(row, expected_revision)
        conn.execute(
            """
            UPDATE agency_decision_requests
               SET status = 'cancelled', cancelled_by = %s,
                   cancelled_at = clock_timestamp(), revision = revision + 1,
                   updated_at = clock_timestamp()
             WHERE request_id = %s AND status = 'pending' AND revision = %s
            """,
            (cancelled_by, request_id, expected_revision),
        )
        _insert_event(
            conn,
            request_id=request_id,
            event_type="request_cancelled",
            actor=cancelled_by,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        return get_request(conn, request_id)


def list_requests(
    conn: psycopg.Connection,
    *,
    status: str | None = "pending",
    project_ref: str | None = None,
    work_issue_ref: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if status not in {None, "pending", "resolved", "cancelled"}:
        raise DecisionRequestError(f"unsupported Decision Request status: {status!r}")
    if limit < 1 or limit > 500:
        raise DecisionRequestError("limit must be between 1 and 500")
    filters: list[str] = []
    params: list[Any] = []
    if status is not None:
        filters.append("status = %s")
        params.append(status)
    if project_ref is not None:
        filters.append("project_id = %s")
        params.append(project_ref)
    if work_issue_ref is not None:
        filters.append("work_issue_id = %s")
        params.append(work_issue_ref)
    where = " AND ".join(filters) if filters else "true"
    params.append(limit)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT request_id
              FROM agency_decision_requests
             WHERE {where}
             ORDER BY
                   CASE priority
                       WHEN 'urgent' THEN 0
                       WHEN 'high' THEN 1
                       WHEN 'normal' THEN 2
                       WHEN 'low' THEN 3
                       ELSE 99
                   END,
                   created_at,
                   request_id
             LIMIT %s
            """,
            tuple(params),
        )
        request_ids = [row[0] for row in cur.fetchall()]
    return [get_request(conn, request_id) for request_id in request_ids]
