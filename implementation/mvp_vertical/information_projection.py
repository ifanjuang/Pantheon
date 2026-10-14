"""Bounded projection metadata and Document links for Agency Information.

This module extends the existing Information owner. It does not duplicate
Document authority, bytes, extraction, archive state or professional truth.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import pantheon_contracts

MIGRATION = Path(__file__).resolve().parent / "sql" / "013_information_card_projection.sql"
MEDIA_TYPES = {"email", "pdf", "text", "table", "image", "photo", "audio", "video", "docx", "xlsx", "ifc", "link", "other"}
LINK_ROLES = {"primary", "supporting", "attachment"}


class InformationProjectionError(ValueError):
    pass


class InformationProjectionNotFound(InformationProjectionError):
    pass


class StaleInformationProjectionWrite(InformationProjectionError):
    pass


class InformationProjectionIdempotencyConflict(InformationProjectionError):
    pass


class InformationProjectionGateRequired(InformationProjectionError):
    pass


def initialize(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ensure_information(conn: psycopg.Connection, information_id: str) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM agency_information_cards WHERE information_id = %s", (information_id,))
        row = cur.fetchone()
    if row is None:
        raise InformationProjectionNotFound(f"unknown Agency Information: {information_id}")
    return _jsonable(dict(row))


def _normalize_media_types(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values or ["text"]:
        value = str(raw).strip().lower()
        if value not in MEDIA_TYPES:
            raise InformationProjectionError(f"unsupported media type: {value}")
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    if not normalized:
        raise InformationProjectionError("at least one media type is required")
    return normalized


def _identity_exists(conn: psycopg.Connection, table: str, key: str, value: str) -> bool:
    return conn.execute(f"SELECT 1 FROM {table} WHERE {key} = %s", (value,)).fetchone() is not None


def _normalize_contacts(conn: psycopg.Connection, values: list[dict] | None) -> list[dict]:
    output: list[dict] = []
    for index, raw in enumerate(values or []):
        if not isinstance(raw, dict):
            raise InformationProjectionError(f"contact ref {index + 1} must be an object")
        unknown = set(raw) - {"label", "person_id", "organization_id", "role"}
        if unknown:
            raise InformationProjectionError(f"unsupported contact ref field(s): {', '.join(sorted(unknown))}")
        label = str(raw.get("label") or "").strip()
        if not label:
            raise InformationProjectionError(f"contact ref {index + 1} requires label")
        item: dict[str, str] = {"label": label}
        person_id = str(raw.get("person_id") or "").strip()
        organization_id = str(raw.get("organization_id") or "").strip()
        role = str(raw.get("role") or "").strip()
        if person_id:
            if not _identity_exists(conn, "agency_people", "person_id", person_id):
                raise InformationProjectionNotFound(f"unknown Person: {person_id}")
            item["person_id"] = person_id
        if organization_id:
            if not _identity_exists(conn, "agency_organizations", "organization_id", organization_id):
                raise InformationProjectionNotFound(f"unknown Organization: {organization_id}")
            item["organization_id"] = organization_id
        if role:
            item["role"] = role
        output.append(item)
    return output


def _metadata_row(conn: psycopg.Connection, information_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM agency_information_projection_metadata WHERE information_id = %s{suffix}", (information_id,))
        row = cur.fetchone()
    if row is None:
        return {"information_id": information_id, "source_date": None, "received_at": None, "issued_at": None, "media_types": ["text"], "contact_refs": [], "revision": 0, "updated_at": None}
    return _jsonable(dict(row))


def _document_links(conn: psycopg.Connection, information_id: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT information_id, document_id, role, observed_version, observed_digest, created_at
              FROM agency_information_document_links
             WHERE information_id = %s
             ORDER BY CASE role WHEN 'primary' THEN 0 WHEN 'supporting' THEN 1 ELSE 2 END, document_id
            """, (information_id,))
        rows = cur.fetchall()
    return [_jsonable(dict(row)) for row in rows]


def _backing_mode(links: list[dict]) -> str:
    if not links:
        return "native"
    return "single_document" if len(links) == 1 else "multiple_documents"


def get_projection(conn: psycopg.Connection, information_id: str) -> dict:
    information = _ensure_information(conn, information_id)
    metadata = _metadata_row(conn, information_id)
    links = _document_links(conn, information_id)
    return {
        "information": information,
        "projection": {**metadata, "backing_mode": _backing_mode(links), "document_refs": links},
        "business_kind": information["category"],
        "professional_index": information["index_label"],
        "business_date": information.get("information_date"),
        "lifecycle_status": information["status"],
        "document_authority_transferred": False,
        "authorization_inferred": False,
    }


def list_project_projections(conn: psycopg.Connection, project_id: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT information_id FROM agency_information_cards WHERE project_id = %s AND status <> 'superseded' ORDER BY lower(title), series_id, created_at DESC", (project_id,))
        ids = [row[0] for row in cur.fetchall()]
    return [get_projection(conn, information_id) for information_id in ids]


def _replayed(conn: psycopg.Connection, *, information_id: str, idempotency_key: str, payload_digest: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT information_id, payload_digest, result_snapshot FROM agency_information_projection_events WHERE idempotency_key = %s", (idempotency_key,))
        row = cur.fetchone()
    if row is None:
        return None
    if row["information_id"] != information_id or row["payload_digest"] != payload_digest:
        raise InformationProjectionIdempotencyConflict("idempotency key already belongs to another projection mutation")
    return _jsonable(dict(row["result_snapshot"]))


def _record_event(conn: psycopg.Connection, *, information_id: str, event_type: str, actor: str, actor_kind: str, expected_revision: int, resulting_revision: int, idempotency_key: str, payload_digest: str, payload: dict, snapshot: dict) -> None:
    conn.execute("""
        INSERT INTO agency_information_projection_events (
            event_id, information_id, event_type, actor, actor_kind,
            expected_revision, resulting_revision, idempotency_key,
            payload_digest, payload, result_snapshot
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (f"info-projection-event-{uuid.uuid4().hex}", information_id, event_type, actor, actor_kind, expected_revision, resulting_revision, idempotency_key, payload_digest, Jsonb(payload), Jsonb(snapshot)))


def _validate_actor(actor: str, actor_kind: str) -> None:
    if not actor or not actor.strip():
        raise InformationProjectionError("actor is required")
    if actor_kind not in {"human", "system"}:
        raise InformationProjectionGateRequired("Hermes cannot mutate canonical Information projection data directly")


def _advance_metadata_revision(conn: psycopg.Connection, information_id: str, expected_revision: int) -> int:
    resulting_revision = expected_revision + 1
    result = conn.execute(
        """
        INSERT INTO agency_information_projection_metadata (information_id, revision)
        VALUES (%s,%s)
        ON CONFLICT (information_id) DO UPDATE
            SET revision = EXCLUDED.revision, updated_at = CURRENT_TIMESTAMP
          WHERE agency_information_projection_metadata.revision = %s
        """,
        (information_id, resulting_revision, expected_revision),
    )
    if result.rowcount != 1:
        raise StaleInformationProjectionWrite("Information projection changed during mutation")
    return resulting_revision


def update_projection_metadata(conn: psycopg.Connection, *, information_id: str, source_date: date | None, received_at: datetime | None, issued_at: datetime | None, media_types: list[str] | None, contact_refs: list[dict] | None, expected_revision: int, actor: str, actor_kind: Literal["human", "system"], idempotency_key: str) -> dict:
    _validate_actor(actor, actor_kind)
    payload = {"operation": "update_projection_metadata", "information_id": information_id, "source_date": source_date.isoformat() if source_date else None, "received_at": received_at.isoformat() if received_at else None, "issued_at": issued_at.isoformat() if issued_at else None, "media_types": _normalize_media_types(media_types), "contact_refs": contact_refs or [], "actor": actor, "actor_kind": actor_kind}
    digest = _digest(payload)
    with conn.transaction():
        _ensure_information(conn, information_id)
        replay = _replayed(conn, information_id=information_id, idempotency_key=idempotency_key, payload_digest=digest)
        if replay is not None:
            return replay
        normalized_contacts = _normalize_contacts(conn, contact_refs)
        current = _metadata_row(conn, information_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleInformationProjectionWrite(f"stale Information projection revision: expected {expected_revision}, current {current['revision']}")
        resulting_revision = expected_revision + 1
        result = conn.execute("""
            INSERT INTO agency_information_projection_metadata (information_id, source_date, received_at, issued_at, media_types, contact_refs, revision, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
            ON CONFLICT (information_id) DO UPDATE
                SET source_date = EXCLUDED.source_date,
                    received_at = EXCLUDED.received_at,
                    issued_at = EXCLUDED.issued_at,
                    media_types = EXCLUDED.media_types,
                    contact_refs = EXCLUDED.contact_refs,
                    revision = EXCLUDED.revision,
                    updated_at = CURRENT_TIMESTAMP
              WHERE agency_information_projection_metadata.revision = %s
            """, (information_id, source_date, received_at, issued_at, Jsonb(payload["media_types"]), Jsonb(normalized_contacts), resulting_revision, expected_revision))
        if result.rowcount != 1:
            raise StaleInformationProjectionWrite("Information projection changed during mutation")
        snapshot = get_projection(conn, information_id)
        _record_event(conn, information_id=information_id, event_type="projection_metadata_updated", actor=actor, actor_kind=actor_kind, expected_revision=expected_revision, resulting_revision=resulting_revision, idempotency_key=idempotency_key, payload_digest=digest, payload={**payload, "contact_refs": normalized_contacts}, snapshot=snapshot)
        return snapshot


def add_document_link(conn: psycopg.Connection, *, information_id: str, document_id: str, role: Literal["primary", "supporting", "attachment"], observed_version: int | None, observed_digest: str | None, expected_revision: int, actor: str, actor_kind: Literal["human", "system"], idempotency_key: str) -> dict:
    _validate_actor(actor, actor_kind)
    if role not in LINK_ROLES:
        raise InformationProjectionError("unsupported Document link role")
    payload = {"operation": "add_document_link", "information_id": information_id, "document_id": document_id, "role": role, "observed_version": observed_version, "observed_digest": observed_digest, "actor": actor, "actor_kind": actor_kind}
    digest = _digest(payload)
    with conn.transaction():
        _ensure_information(conn, information_id)
        if conn.execute("SELECT 1 FROM source_documents WHERE document_id = %s", (document_id,)).fetchone() is None:
            raise InformationProjectionNotFound(f"unknown Document: {document_id}")
        replay = _replayed(conn, information_id=information_id, idempotency_key=idempotency_key, payload_digest=digest)
        if replay is not None:
            return replay
        current = _metadata_row(conn, information_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleInformationProjectionWrite(f"stale Information projection revision: expected {expected_revision}, current {current['revision']}")
        inserted = conn.execute("""
            INSERT INTO agency_information_document_links (information_id, document_id, role, observed_version, observed_digest)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (information_id, document_id) DO UPDATE SET role = EXCLUDED.role, observed_version = EXCLUDED.observed_version, observed_digest = EXCLUDED.observed_digest
            RETURNING (xmax = 0)
            """, (information_id, document_id, role, observed_version, observed_digest)).fetchone()[0]
        resulting_revision = _advance_metadata_revision(conn, information_id, expected_revision)
        snapshot = get_projection(conn, information_id)
        event_type = "document_link_added" if inserted else "document_link_updated"
        mutation_result = {
            **snapshot,
            "document_link_operation": "created" if inserted else "updated",
        }
        _record_event(conn, information_id=information_id, event_type=event_type, actor=actor, actor_kind=actor_kind, expected_revision=expected_revision, resulting_revision=resulting_revision, idempotency_key=idempotency_key, payload_digest=digest, payload=payload, snapshot=mutation_result)
        return mutation_result


def remove_document_link(conn: psycopg.Connection, *, information_id: str, document_id: str, expected_revision: int, actor: str, actor_kind: Literal["human", "system"], idempotency_key: str) -> dict:
    _validate_actor(actor, actor_kind)
    payload = {"operation": "remove_document_link", "information_id": information_id, "document_id": document_id, "actor": actor, "actor_kind": actor_kind}
    digest = _digest(payload)
    with conn.transaction():
        _ensure_information(conn, information_id)
        replay = _replayed(conn, information_id=information_id, idempotency_key=idempotency_key, payload_digest=digest)
        if replay is not None:
            return replay
        current = _metadata_row(conn, information_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleInformationProjectionWrite(f"stale Information projection revision: expected {expected_revision}, current {current['revision']}")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM agency_information_document_links WHERE information_id = %s AND document_id = %s", (information_id, document_id))
            if cur.rowcount != 1:
                raise InformationProjectionNotFound(f"Document {document_id} is not linked to Information {information_id}")
        resulting_revision = _advance_metadata_revision(conn, information_id, expected_revision)
        snapshot = get_projection(conn, information_id)
        _record_event(conn, information_id=information_id, event_type="document_link_removed", actor=actor, actor_kind=actor_kind, expected_revision=expected_revision, resulting_revision=resulting_revision, idempotency_key=idempotency_key, payload_digest=digest, payload=payload, snapshot=snapshot)
        return snapshot


def contract_projection(conn: psycopg.Connection, information_id: str) -> dict[str, Any]:
    """Project one Information onto the vendored Information Card Projection contract.

    `get_projection` returns this repository's working shape: the Information row,
    a nested `projection` block and derived fields. The contract is flat and names
    some fields differently. Mapping here keeps the two free to move independently
    and makes conformance checkable rather than asserted by a matching filename.

    Read-only. Projecting transfers no Document authority and infers no
    authorization; both are reported as false by `get_projection` and neither is
    part of the contract payload.
    """
    projected = get_projection(conn, information_id)
    information = projected["information"]
    block = projected["projection"]

    document_refs = [
        {
            key: link[key]
            for key in ("document_id", "role", "observed_version", "observed_digest")
            if link.get(key) is not None or key == "document_id"
        }
        for link in block.get("document_refs") or []
    ]

    revision = block.get("revision", 0)
    optional_revision = {"revision": revision} if revision >= 1 else {}

    return pantheon_contracts.validate(
        "information_card_projection",
        {
            **optional_revision,
            "information_id": information["information_id"],
            "project_id": information["project_id"],
            "series_id": information.get("series_id"),
            "title": information["title"],
            "business_kind": projected["business_kind"],
            "summary": information.get("summary") or "",
            "details": information.get("details") or "",
            "author_or_origin": information.get("source_note"),
            "lifecycle_status": projected["lifecycle_status"],
            "professional_index": projected["professional_index"],
            "business_date": projected["business_date"],
            "dates": {
                "source_date": block.get("source_date"),
                "received_at": block.get("received_at"),
                "issued_at": block.get("issued_at"),
            },
            "backing_mode": block["backing_mode"],
            "document_refs": document_refs,
            "media_types": block.get("media_types") or ["text"],
            "contact_refs": block.get("contact_refs") or [],
        },
    )
