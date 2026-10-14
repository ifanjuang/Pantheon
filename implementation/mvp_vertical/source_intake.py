"""Bounded PostgreSQL owner for generic Source intake and Project linking.

A Source is preserved before documentary ingestion or semantic understanding.
This module does not parse content, create Information, create Projects, admit
Evidence or dispatch Hermes.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import pantheon_contracts

MIGRATION = Path(__file__).resolve().parent / "sql" / "009_source_intake_admission.sql"
SOURCE_KINDS = {"email", "document", "image", "audio", "video", "model", "url", "text", "archive", "event", "other"}
LINK_STATUSES = {"unassigned", "suggested", "linked", "excluded"}
ACTOR_KINDS = {"human", "hermes", "system"}
METADATA_FIELDS = {"declared_project_name", "source_date", "mime_type", "checksum", "confidentiality", "metadata"}


class SourceIntakeError(ValueError):
    pass


class SourceNotFound(SourceIntakeError):
    pass


class StaleSourceWrite(SourceIntakeError):
    pass


class SourceIdempotencyConflict(SourceIntakeError):
    pass


class SourceGovernanceGateRequired(SourceIntakeError):
    pass


def initialize(conn: psycopg.Connection) -> None:
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


def _digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_actor(actor: str, actor_kind: str) -> None:
    if not actor or not actor.strip():
        raise SourceIntakeError("actor is required")
    if actor_kind not in ACTOR_KINDS:
        raise SourceIntakeError("actor_kind must be human, hermes or system")
    if actor_kind == "hermes":
        raise SourceGovernanceGateRequired("Hermes direct Source writes require an admitted bounded capability")


def _source_row(conn: psycopg.Connection, source_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM agency_sources WHERE source_id = %s{suffix}", (source_id,))
        row = cur.fetchone()
    if row is None:
        raise SourceNotFound(f"unknown Source: {source_id}")
    return _jsonable(dict(row))


def _project_exists(conn: psycopg.Connection, project_id: str) -> bool:
    return conn.execute("SELECT 1 FROM agency_projects WHERE project_id = %s", (project_id,)).fetchone() is not None


def _normalize_candidates(candidates: list[dict] | None) -> list[dict]:
    normalized: list[dict] = []
    seen: set[str] = set()
    for index, item in enumerate(candidates or []):
        if not isinstance(item, dict):
            raise SourceIntakeError(f"candidate {index + 1} must be an object")
        required = {"project_ref", "score", "basis", "producer", "created_at"}
        missing = required - set(item)
        unknown = set(item) - required
        if missing:
            raise SourceIntakeError(f"candidate {index + 1} missing: {', '.join(sorted(missing))}")
        if unknown:
            raise SourceIntakeError(f"candidate {index + 1} unsupported fields: {', '.join(sorted(unknown))}")
        project_ref = str(item["project_ref"]).strip()
        if not project_ref or project_ref in seen:
            raise SourceIntakeError("candidate project_ref must be non-empty and unique")
        seen.add(project_ref)
        try:
            score = float(item["score"])
        except (TypeError, ValueError) as exc:
            raise SourceIntakeError("candidate score must be numeric") from exc
        if not 0 <= score <= 1:
            raise SourceIntakeError("candidate score must be between 0 and 1")
        basis = [str(value).strip() for value in item["basis"] if str(value).strip()]
        producer = str(item["producer"]).strip()
        created_at = str(item["created_at"]).strip()
        if not basis or not producer or not created_at:
            raise SourceIntakeError("candidate basis, producer and created_at are required")
        normalized.append({"project_ref": project_ref, "score": score, "basis": basis, "producer": producer, "created_at": created_at})
    return normalized


def _replayed(conn: psycopg.Connection, *, idempotency_key: str, source_id: str, payload_digest: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT source_id, payload_digest, result_snapshot FROM agency_source_events WHERE idempotency_key = %s", (idempotency_key,))
        row = cur.fetchone()
    if row is None:
        return None
    if row["source_id"] != source_id or row["payload_digest"] != payload_digest:
        raise SourceIdempotencyConflict("idempotency key already belongs to another Source mutation")
    return _jsonable(dict(row["result_snapshot"]))


def _record_event(conn: psycopg.Connection, *, source_id: str, event_type: str, actor: str, actor_kind: str, expected_revision: int, resulting_revision: int, idempotency_key: str, payload: dict, result_snapshot: dict) -> None:
    conn.execute(
        """INSERT INTO agency_source_events (
            event_id, source_id, event_type, actor, actor_kind,
            expected_revision, resulting_revision, idempotency_key,
            payload_digest, payload, result_snapshot
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (f"source-event-{uuid.uuid4().hex}", source_id, event_type, actor, actor_kind, expected_revision, resulting_revision, idempotency_key, _digest(payload), Jsonb(payload), Jsonb(result_snapshot)),
    )


def create_source(conn: psycopg.Connection, *, source_id: str, source_kind: str, origin_system: str, origin_external_ref: str, raw_source_ref: str, received_at: str | datetime, actor: str, actor_kind: str, idempotency_key: str, origin_producer: str | None = None, received_by: str | None = None, declared_project_name: str | None = None, source_date: str | datetime | None = None, mime_type: str | None = None, checksum: str | None = None, confidentiality: str | None = None, metadata: dict | None = None) -> dict:
    _validate_actor(actor, actor_kind)
    if source_kind not in SOURCE_KINDS:
        raise SourceIntakeError(f"unsupported source_kind: {source_kind}")
    for label, value in {"source_id": source_id, "origin_system": origin_system, "origin_external_ref": origin_external_ref, "raw_source_ref": raw_source_ref, "idempotency_key": idempotency_key}.items():
        if not value or not str(value).strip():
            raise SourceIntakeError(f"{label} is required")
    if checksum is not None:
        checksum = checksum.strip().lower()
        if len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
            raise SourceIntakeError("checksum must be a SHA-256 hexadecimal digest")
    payload = {"source_id": source_id, "source_kind": source_kind, "origin_system": origin_system, "origin_external_ref": origin_external_ref, "origin_producer": origin_producer, "received_by": received_by, "raw_source_ref": raw_source_ref, "received_at": _jsonable(received_at), "declared_project_name": declared_project_name, "source_date": _jsonable(source_date), "mime_type": mime_type, "checksum": checksum, "confidentiality": confidentiality, "metadata": metadata or {}}
    digest = _digest(payload)
    try:
        with conn.transaction():
            replay = _replayed(conn, idempotency_key=idempotency_key, source_id=source_id, payload_digest=digest)
            if replay is not None:
                return replay
            conn.execute(
                """INSERT INTO agency_sources (
                    source_id, source_kind, origin_system, origin_external_ref,
                    origin_producer, received_by, raw_source_ref, received_at,
                    project_link_status, declared_project_name, source_date,
                    mime_type, checksum, confidentiality, metadata, created_by, updated_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'unassigned', %s, %s, %s, %s, %s, %s, %s, %s)""",
                (source_id, source_kind, origin_system, origin_external_ref, origin_producer, received_by, raw_source_ref, received_at, declared_project_name, source_date, mime_type, checksum, confidentiality, Jsonb(metadata or {}), actor, actor),
            )
            snapshot = _source_row(conn, source_id)
            _record_event(conn, source_id=source_id, event_type="source_created", actor=actor, actor_kind=actor_kind, expected_revision=0, resulting_revision=1, idempotency_key=idempotency_key, payload=payload, result_snapshot=snapshot)
            return snapshot
    except psycopg.errors.UniqueViolation as exc:
        raise SourceIntakeError("source_id or origin identity already exists") from exc


def get_source(conn: psycopg.Connection, source_id: str) -> dict:
    return _source_row(conn, source_id)


def list_sources(conn: psycopg.Connection, *, project_link_status: str | None = None, project_id: str | None = None, limit: int = 100) -> list[dict]:
    if not 1 <= limit <= 500:
        raise SourceIntakeError("limit must be between 1 and 500")
    clauses: list[str] = []
    params: list[Any] = []
    if project_link_status is not None:
        if project_link_status not in LINK_STATUSES:
            raise SourceIntakeError("unsupported project_link_status")
        clauses.append("project_link_status = %s")
        params.append(project_link_status)
    if project_id is not None:
        clauses.append("project_id = %s")
        params.append(project_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM agency_sources {where} ORDER BY received_at DESC, source_id LIMIT %s", params)
        rows = cur.fetchall()
    return [_jsonable(dict(row)) for row in rows]


def _mutate(conn: psycopg.Connection, *, source_id: str, expected_revision: int, actor: str, actor_kind: str, idempotency_key: str, event_type: str, payload: dict, assignments: dict[str, Any]) -> dict:
    _validate_actor(actor, actor_kind)
    digest = _digest(payload)
    with conn.transaction():
        replay = _replayed(conn, idempotency_key=idempotency_key, source_id=source_id, payload_digest=digest)
        if replay is not None:
            return replay
        current = _source_row(conn, source_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleSourceWrite(f"expected Source revision {expected_revision}, current is {current['revision']}")
        columns = [f"{key} = %s" for key in assignments]
        values = [Jsonb(value) if isinstance(value, (dict, list)) else value for value in assignments.values()]
        values.extend([actor, source_id, expected_revision])
        result = conn.execute(f"UPDATE agency_sources SET {', '.join(columns)}, updated_by = %s, revision = revision + 1, updated_at = CURRENT_TIMESTAMP WHERE source_id = %s AND revision = %s", values)
        if result.rowcount != 1:
            raise StaleSourceWrite("Source changed during mutation")
        snapshot = _source_row(conn, source_id)
        _record_event(conn, source_id=source_id, event_type=event_type, actor=actor, actor_kind=actor_kind, expected_revision=expected_revision, resulting_revision=expected_revision + 1, idempotency_key=idempotency_key, payload=payload, result_snapshot=snapshot)
        return snapshot


def update_metadata(conn: psycopg.Connection, *, source_id: str, changes: dict[str, Any], expected_revision: int, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    unknown = set(changes) - METADATA_FIELDS
    if unknown:
        raise SourceIntakeError(f"unsupported metadata fields: {', '.join(sorted(unknown))}")
    if not changes:
        raise SourceIntakeError("at least one metadata field is required")
    if "checksum" in changes and changes["checksum"] is not None:
        checksum = str(changes["checksum"]).strip().lower()
        if len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
            raise SourceIntakeError("checksum must be a SHA-256 hexadecimal digest")
        changes = {**changes, "checksum": checksum}
    return _mutate(conn, source_id=source_id, expected_revision=expected_revision, actor=actor, actor_kind=actor_kind, idempotency_key=idempotency_key, event_type="metadata_updated", payload={"changes": changes}, assignments=changes)


def suggest_projects(conn: psycopg.Connection, *, source_id: str, candidates: list[dict], expected_revision: int, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    normalized = _normalize_candidates(candidates)
    if not normalized:
        raise SourceIntakeError("at least one Project candidate is required")
    current = _source_row(conn, source_id)
    if current["project_link_status"] == "linked" or current.get("project_id") is not None:
        raise SourceIntakeError("linked Source must be explicitly unlinked before project suggestions")
    for candidate in normalized:
        if not _project_exists(conn, candidate["project_ref"]):
            raise SourceIntakeError(f"unknown candidate Project: {candidate['project_ref']}")
    return _mutate(conn, source_id=source_id, expected_revision=expected_revision, actor=actor, actor_kind=actor_kind, idempotency_key=idempotency_key, event_type="project_links_suggested", payload={"candidates": normalized}, assignments={"candidate_project_refs": normalized, "project_link_status": "suggested", "project_id": None})


def link_project(conn: psycopg.Connection, *, source_id: str, project_id: str, expected_revision: int, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    if not _project_exists(conn, project_id):
        raise SourceIntakeError(f"unknown Project: {project_id}")
    return _mutate(conn, source_id=source_id, expected_revision=expected_revision, actor=actor, actor_kind=actor_kind, idempotency_key=idempotency_key, event_type="project_linked", payload={"project_id": project_id}, assignments={"project_id": project_id, "project_link_status": "linked"})


def unlink_project(conn: psycopg.Connection, *, source_id: str, expected_revision: int, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    return _mutate(conn, source_id=source_id, expected_revision=expected_revision, actor=actor, actor_kind=actor_kind, idempotency_key=idempotency_key, event_type="project_unlinked", payload={}, assignments={"project_id": None, "project_link_status": "unassigned"})


def exclude_source(conn: psycopg.Connection, *, source_id: str, expected_revision: int, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    return _mutate(conn, source_id=source_id, expected_revision=expected_revision, actor=actor, actor_kind=actor_kind, idempotency_key=idempotency_key, event_type="source_excluded", payload={}, assignments={"project_id": None, "project_link_status": "excluded"})


def restore_source(conn: psycopg.Connection, *, source_id: str, expected_revision: int, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    if _source_row(conn, source_id)["project_link_status"] != "excluded":
        raise SourceIntakeError("only an excluded Source can be restored")
    return _mutate(conn, source_id=source_id, expected_revision=expected_revision, actor=actor, actor_kind=actor_kind, idempotency_key=idempotency_key, event_type="source_restored", payload={}, assignments={"project_id": None, "project_link_status": "unassigned"})


def relate_contained_source(conn: psycopg.Connection, *, source_id: str, target_source_id: str, actor: str, actor_kind: str, idempotency_key: str) -> dict:
    _validate_actor(actor, actor_kind)
    if source_id == target_source_id:
        raise SourceIntakeError("a Source cannot contain itself")
    payload = {"target_source_id": target_source_id, "relation_type": "contains"}
    digest = _digest(payload)
    try:
        with conn.transaction():
            replay = _replayed(conn, idempotency_key=idempotency_key, source_id=source_id, payload_digest=digest)
            if replay is not None:
                return replay
            _source_row(conn, source_id)
            _source_row(conn, target_source_id)
            relation = {"relation_id": f"source-relation-{uuid.uuid4().hex}", "source_id": source_id, "target_source_id": target_source_id, "relation_type": "contains", "created_by": actor}
            conn.execute("INSERT INTO agency_source_relations (relation_id, source_id, target_source_id, relation_type, created_by) VALUES (%s, %s, %s, 'contains', %s)", (relation["relation_id"], source_id, target_source_id, actor))
            _record_event(conn, source_id=source_id, event_type="source_relation_created", actor=actor, actor_kind=actor_kind, expected_revision=0, resulting_revision=0, idempotency_key=idempotency_key, payload=payload, result_snapshot=relation)
            return relation
    except psycopg.errors.UniqueViolation as exc:
        raise SourceIntakeError("Source relation already exists") from exc


def contract_projection(record: dict[str, Any]) -> dict[str, Any]:
    """Project one Source record onto the vendored Source Intake Admission contract.

    The stored row and the contract differ in shape: origin fields are flat in the
    table and nested in the contract, and `project_id` is named `project_ref`.
    Mapping them here keeps the persistence free to change without breaking the
    contract, and makes conformance checkable instead of asserted by name.

    Read-only. Projecting admits nothing and links no project.
    """
    return pantheon_contracts.validate(
        "source_intake_admission",
        {
            "source_id": record["source_id"],
            "source_kind": record["source_kind"],
            "origin": {
                "system": record["origin_system"],
                "external_ref": record["origin_external_ref"],
                "producer": record.get("origin_producer"),
                "received_by": record.get("received_by"),
            },
            "raw_source_ref": record["raw_source_ref"],
            "received_at": record["received_at"],
            "project_link_status": record["project_link_status"],
            "project_ref": record.get("project_id"),
            "declared_project_name": record.get("declared_project_name"),
            "candidate_project_refs": record.get("candidate_project_refs") or [],
            "source_date": record.get("source_date"),
            "mime_type": record.get("mime_type"),
            "checksum": record.get("checksum"),
            "confidentiality": record.get("confidentiality"),
            "metadata": record.get("metadata") or {},
        },
    )
