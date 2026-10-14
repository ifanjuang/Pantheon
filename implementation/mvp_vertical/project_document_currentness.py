"""Bounded professional document-version effects and currentness projection.

This module is deliberately smaller than the documented Proof Register. It
records append-only version posture and resolves only purposes whose authority
can be established from currently executable owners. Consequential professional
currentness remains unresolved until a separately governed authority basis is
implemented.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
import yaml
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import pantheon_contracts, project_document_admission, project_documents

MIGRATION = Path(__file__).resolve().parent / "sql" / "027_project_document_version_effect_events.sql"
VERSION_EVENT_SCHEMA = pantheon_contracts.schema_path("document_version_event")
CURRENTNESS_SCHEMA = pantheon_contracts.schema_path("document_currentness_projection")

CONSEQUENTIAL_AUTHORITIES = {
    "phase_approval_authority",
    "consultation_authority",
    "execution_authority",
    "site_record_authority",
    "contractual_authority",
    "as_built_authority",
}
INTERNAL_AUTHORITIES = {
    "internal_working_authority",
    "internal_review_authority",
}
TERMINAL_STATUSES = {"superseded", "obsolete", "rejected", "withdrawn"}
WORKING_EFFECTS = {"working_revision", "minor_correction", "coordination_update"}

AUTHORITY = {
    "is_evidence": False,
    "is_decision": False,
    "is_approval": False,
    "is_proof": False,
    "is_contractual_authority": False,
    "is_execution_authority": False,
    "changes_project_truth": False,
}


class ProjectDocumentCurrentnessError(ValueError):
    pass


class ProjectDocumentVersionNotFound(ProjectDocumentCurrentnessError):
    pass


class VocabularyError(ProjectDocumentCurrentnessError):
    pass


class IdempotencyConflict(ProjectDocumentCurrentnessError):
    pass


class GovernanceGateRequired(ProjectDocumentCurrentnessError):
    pass


def _schema() -> tuple[dict[str, Any], dict[str, Any]]:
    with VERSION_EVENT_SCHEMA.open("r", encoding="utf-8") as handle:
        event_schema = yaml.safe_load(handle)
    with CURRENTNESS_SCHEMA.open("r", encoding="utf-8") as handle:
        currentness_schema = yaml.safe_load(handle)
    return event_schema, currentness_schema


_EVENT_SCHEMA, _CURRENTNESS_SCHEMA = _schema()
EVENT_TYPES = set(_EVENT_SCHEMA["properties"]["event_type"]["enum"])
VERSION_STATUSES = set(_EVENT_SCHEMA["$defs"]["version_status"]["enum"])
EFFECT_CLASSES = set(_EVENT_SCHEMA["$defs"]["effect_class"]["enum"])
AUTHORITY_STATUSES = set(_EVENT_SCHEMA["$defs"]["authority_status"]["enum"])
PURPOSES = set(_CURRENTNESS_SCHEMA["properties"]["purpose"]["enum"])


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = project_document_admission.connect(dsn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    project_document_admission.ensure_schema(conn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProjectDocumentCurrentnessError(f"{field} is required")
    return text


def _optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _payload_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_vocabulary(value: str, allowed: set[str], field: str) -> str:
    value = _required(value, field)
    if value not in allowed:
        raise VocabularyError(f"unknown {field}: {value}")
    return value


def _validate_basis_refs(value: list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    normalized: list[str] = []
    for item in value:
        ref = _required(item, "basis_ref")
        if ref not in normalized:
            normalized.append(ref)
    return normalized


def _version_for_update(conn: psycopg.Connection, version_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM doc_document_versions WHERE version_id = %s FOR UPDATE",
            (version_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ProjectDocumentVersionNotFound(f"unknown Project Document revision: {version_id}")
    return dict(row)


def _latest_event(conn: psycopg.Connection, version_id: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM doc_document_version_effect_events
             WHERE document_version_id = %s
             ORDER BY event_seq DESC
             LIMIT 1
            """,
            (version_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else None


def _event_replay(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    payload_digest: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT payload_digest, result_snapshot
              FROM doc_document_version_effect_events
             WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["payload_digest"] != payload_digest:
        raise IdempotencyConflict(
            "idempotency key already belongs to another document-version event"
        )
    return dict(row["result_snapshot"])


def record_version_event(
    conn: psycopg.Connection,
    *,
    document_version_id: str,
    event_type: str,
    new_status: str,
    new_effect_class: str,
    new_authority_status: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    reason: str | None = None,
    basis_refs: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Record one reviewed posture transition without admitting Proof/authority."""
    document_version_id = _required(document_version_id, "document_version_id")
    event_type = _validate_vocabulary(event_type, EVENT_TYPES, "event_type")
    new_status = _validate_vocabulary(new_status, VERSION_STATUSES, "new_status")
    new_effect_class = _validate_vocabulary(
        new_effect_class, EFFECT_CLASSES, "new_effect_class"
    )
    new_authority_status = _validate_vocabulary(
        new_authority_status, AUTHORITY_STATUSES, "new_authority_status"
    )
    actor = _required(actor, "actor")
    actor_kind = _required(actor_kind, "actor_kind")
    idempotency_key = _required(idempotency_key, "idempotency_key")
    reason = _optional(reason)
    basis_refs = _validate_basis_refs(basis_refs)

    if actor_kind not in {"human", "system", "hermes"}:
        raise ProjectDocumentCurrentnessError("actor_kind must be human, system or hermes")
    if actor_kind == "hermes":
        raise GovernanceGateRequired("Hermes cannot record professional version-effect events directly")
    if new_authority_status in CONSEQUENTIAL_AUTHORITIES:
        raise GovernanceGateRequired(
            "consequential document authority requires a separately executable governed basis"
        )
    if actor_kind == "system" and new_authority_status != "not_authoritative":
        raise GovernanceGateRequired(
            "system events may observe/classify a version but cannot assign human authority posture"
        )

    payload = {
        "operation": "record_project_document_version_event",
        "document_version_id": document_version_id,
        "event_type": event_type,
        "new_status": new_status,
        "new_effect_class": new_effect_class,
        "new_authority_status": new_authority_status,
        "reason": reason,
        "basis_refs": basis_refs,
        "actor": actor,
        "actor_kind": actor_kind,
    }
    digest = _payload_digest(payload)

    with conn.transaction():
        replay = _event_replay(
            conn, idempotency_key=idempotency_key, payload_digest=digest
        )
        if replay is not None:
            return replay

        version = _version_for_update(conn, document_version_id)
        previous = _latest_event(conn, document_version_id)
        previous_status = previous["new_status"] if previous else None
        previous_effect = previous["new_effect_class"] if previous else None
        previous_authority = previous["new_authority_status"] if previous else None
        next_seq = int(previous["event_seq"]) + 1 if previous else 1
        event_id = f"document-version-event-{uuid.uuid4().hex}"

        snapshot = {
            "event_id": event_id,
            "document_id": version["document_id"],
            "document_version_id": document_version_id,
            "event_seq": next_seq,
            "event_type": event_type,
            "previous_status": previous_status,
            "new_status": new_status,
            "previous_effect_class": previous_effect,
            "new_effect_class": new_effect_class,
            "previous_authority_status": previous_authority,
            "new_authority_status": new_authority_status,
            "reason": reason,
            "basis_refs": basis_refs,
            "actor": actor,
            "actor_kind": actor_kind,
            "authority": dict(AUTHORITY),
        }
        conn.execute(
            """
            INSERT INTO doc_document_version_effect_events (
                event_id, document_version_id, event_seq, event_type,
                previous_status, new_status,
                previous_effect_class, new_effect_class,
                previous_authority_status, new_authority_status,
                reason, basis_refs, actor, actor_kind,
                idempotency_key, payload_digest, result_snapshot
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event_id,
                document_version_id,
                next_seq,
                event_type,
                previous_status,
                new_status,
                previous_effect,
                new_effect_class,
                previous_authority,
                new_authority_status,
                reason,
                Jsonb(basis_refs),
                actor,
                actor_kind,
                idempotency_key,
                digest,
                Jsonb(snapshot),
            ),
        )
        return snapshot


def list_version_events(
    conn: psycopg.Connection, document_version_id: str
) -> list[dict[str, Any]]:
    project_documents.get_revision(conn, document_version_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM doc_document_version_effect_events
             WHERE document_version_id = %s
             ORDER BY event_seq
            """,
            (document_version_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _evaluated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unresolved(document_id: str, purpose: str, missing: list[str]) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "purpose": purpose,
        "resolution_status": "unresolved",
        "document_version_id": None,
        "index_label": None,
        "effect_class": None,
        "version_status": None,
        "authority_status": None,
        "basis": {
            "basis_type": "insufficient_inputs",
            "basis_refs": [],
            "missing_requirements": missing,
            "conflict_refs": [],
        },
        "evaluated_at": _evaluated_at(),
        "authority": dict(AUTHORITY),
    }


def _latest_states(conn: psycopg.Connection, document_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT v.version_id, v.version_seq, v.revision_label, v.received_at,
                   e.event_id, e.event_seq, e.event_type,
                   e.new_status, e.new_effect_class, e.new_authority_status,
                   e.basis_refs
              FROM doc_document_versions v
              JOIN LATERAL (
                    SELECT *
                      FROM doc_document_version_effect_events evt
                     WHERE evt.document_version_id = v.version_id
                     ORDER BY evt.event_seq DESC
                     LIMIT 1
              ) e ON TRUE
             WHERE v.document_id = %s
             ORDER BY v.version_seq, v.version_id
            """,
            (document_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _resolved_from_state(
    document_id: str,
    purpose: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "purpose": purpose,
        "resolution_status": "resolved",
        "document_version_id": state["version_id"],
        "index_label": state.get("revision_label"),
        "effect_class": state["new_effect_class"],
        "version_status": state["new_status"],
        "authority_status": state["new_authority_status"],
        "basis": {
            "basis_type": "version_effect_event",
            "basis_refs": [f"version-event:{state['event_id']}"]
            + list(state.get("basis_refs") or []),
            "missing_requirements": [],
            "conflict_refs": [],
        },
        "evaluated_at": _evaluated_at(),
        "authority": dict(AUTHORITY),
    }


def _resolve_internal(
    conn: psycopg.Connection,
    *,
    document_id: str,
    purpose: str,
) -> dict[str, Any]:
    states = _latest_states(conn, document_id)
    if purpose == "current_working":
        qualifying = [
            row
            for row in states
            if row["new_status"] not in TERMINAL_STATUSES
            and row["new_effect_class"] in WORKING_EFFECTS
            and row["new_authority_status"] in INTERNAL_AUTHORITIES
        ]
        missing = ["explicit working-compatible version effect with bounded internal authority posture"]
    else:
        qualifying = [
            row
            for row in states
            if row["new_status"] not in TERMINAL_STATUSES
            and row["new_effect_class"] == "coordination_update"
            and row["new_authority_status"] in INTERNAL_AUTHORITIES
        ]
        missing = ["explicit coordination effect with bounded internal authority posture"]

    if not qualifying:
        return _unresolved(document_id, purpose, missing)
    if len(qualifying) > 1:
        return {
            "document_id": document_id,
            "purpose": purpose,
            "resolution_status": "conflicting",
            "document_version_id": None,
            "index_label": None,
            "effect_class": None,
            "version_status": None,
            "authority_status": None,
            "basis": {
                "basis_type": "conflicting_inputs",
                "basis_refs": [],
                "missing_requirements": [],
                "conflict_refs": [
                    f"version-event:{row['event_id']}" for row in qualifying
                ],
            },
            "evaluated_at": _evaluated_at(),
            "authority": dict(AUTHORITY),
        }
    return _resolved_from_state(document_id, purpose, qualifying[0])


def resolve_currentness(
    conn: psycopg.Connection,
    *,
    document_id: str,
    purpose: str,
) -> dict[str, Any]:
    """Resolve one purpose without letting receipt/index order imply authority."""
    document_id = _required(document_id, "document_id")
    purpose = _validate_vocabulary(purpose, PURPOSES, "purpose")
    project_documents.get_document(conn, document_id)

    if purpose == "latest_received":
        latest = project_documents.resolve_latest_received(conn, document_id)
        if latest is None:
            return _unresolved(document_id, purpose, ["at least one received professional revision"])
        version = latest["version"]
        return {
            "document_id": document_id,
            "purpose": purpose,
            "resolution_status": "resolved",
            "document_version_id": version["version_id"],
            "index_label": version.get("revision_label"),
            "effect_class": None,
            "version_status": None,
            "authority_status": None,
            "basis": {
                "basis_type": "receipt_chronology",
                "basis_refs": [f"professional-revision:{version['version_id']}"],
                "missing_requirements": [],
                "conflict_refs": [],
            },
            "evaluated_at": _evaluated_at(),
            "authority": dict(AUTHORITY),
        }

    if purpose in {"current_working", "current_for_coordination"}:
        return _resolve_internal(conn, document_id=document_id, purpose=purpose)

    missing_by_purpose = {
        "latest_reviewed": ["executable reviewed-version admission"],
        "current_for_consultation": ["governed consultation issue/package authority basis"],
        "current_contractual": ["governed contractual signature and Proof/Evidence basis"],
        "current_for_execution": ["governed execution approval/visa/instruction basis"],
        "current_for_site": ["governed site issue/instruction basis"],
        "latest_as_built_candidate": ["governed as-built review/acceptance basis"],
    }
    return _unresolved(document_id, purpose, missing_by_purpose[purpose])
