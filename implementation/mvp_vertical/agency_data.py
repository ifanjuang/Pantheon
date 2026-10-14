"""Bounded PostgreSQL adapter for native Agency Data records.

PostgreSQL is the system of record for these native agency records, but this
module is not a governance authority. Hermes and humans act through explicit,
revision-checked operations; neither receives arbitrary SQL through this API.
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

from . import agency_schema, project_claim_conflicts
from .store import dsn_from_env

MIGRATION = Path(__file__).resolve().parent / "sql" / "002_agency_data.sql"
CLAIM_MIGRATION = Path(__file__).resolve().parent / "sql" / "019_project_claim_candidates.sql"
CLAIM_PROVENANCE_MIGRATION = (
    Path(__file__).resolve().parent / "sql" / "036_project_claim_provenance_basis.sql"
)
VARIANT_MIGRATION = Path(__file__).resolve().parent / "sql" / "020_project_change_variants.sql"

PROJECT_MUTABLE_FIELDS = {
    "code",
    "display_name",
    "description",
    "status",
    "phase",
    "location",
    "primary_client",
    "tags",
    "contacts",
    "attributes",
}
ACTOR_KINDS = {"human", "hermes", "system"}
CONTACT_FIELDS = {
    "group",
    "name",
    "organization",
    "role",
    "email",
    "phone",
    "address",
    "notes",
    "source_ref",
}


class AgencyDataError(ValueError):
    """Base refusal for the bounded Agency Data adapter."""


class ProjectNotFound(AgencyDataError):
    pass


class StaleProjectWrite(AgencyDataError):
    pass


class IdempotencyConflict(AgencyDataError):
    pass


class GovernanceGateRequired(AgencyDataError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = psycopg.connect(dsn or dsn_from_env())
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(CLAIM_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(CLAIM_PROVENANCE_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(project_claim_conflicts.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(VARIANT_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _project_row(conn: psycopg.Connection, project_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM agency_projects WHERE project_id = %s{suffix}", (project_id,))
        row = cur.fetchone()
    if row is None:
        raise ProjectNotFound(f"unknown Agency Project: {project_id}")
    return _jsonable(dict(row))


def _payload_digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_actor(actor: str, actor_kind: str) -> None:
    if not actor or not actor.strip():
        raise AgencyDataError("actor is required")
    if actor_kind not in ACTOR_KINDS:
        raise AgencyDataError("actor_kind must be human, hermes or system")


def _normalize_tags(tags: list[str] | None) -> list[str]:
    if tags is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in tags:
        tag = str(value).strip()
        if not tag:
            continue
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    return normalized


def _normalize_contacts(contacts: list[dict] | None) -> list[dict]:
    """Normalize the project-owned contacts snapshot without creating relations."""
    if contacts is None:
        return []
    if not isinstance(contacts, list):
        raise AgencyDataError("contacts must be a list")
    if len(contacts) > 500:
        raise AgencyDataError("contacts cannot contain more than 500 entries")

    normalized: list[dict] = []
    for index, raw in enumerate(contacts):
        if not isinstance(raw, dict):
            raise AgencyDataError(f"contact {index + 1} must be an object")
        unknown = set(raw) - CONTACT_FIELDS
        if unknown:
            raise AgencyDataError(
                f"unsupported contact field(s): {', '.join(sorted(unknown))}"
            )
        item: dict[str, str] = {}
        for key in CONTACT_FIELDS:
            value = raw.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                item[key] = text
        if not item.get("name") and not item.get("organization"):
            raise AgencyDataError(
                f"contact {index + 1} requires at least a name or organization"
            )
        item.setdefault("group", "Autres intervenants")
        normalized.append(item)
    return normalized


def _normalize_attributes(attributes: dict[str, Any] | None) -> dict[str, Any]:
    try:
        return agency_schema.normalize_project_attributes(attributes)
    except agency_schema.AgencySchemaError as exc:
        raise AgencyDataError(str(exc)) from exc


def _replayed_snapshot(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    project_id: str,
    payload_digest: str,
) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT project_id, payload_digest, result_snapshot
              FROM agency_project_events
             WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["project_id"] != project_id or row["payload_digest"] != payload_digest:
        raise IdempotencyConflict("idempotency key already belongs to another Agency Data mutation")
    return _jsonable(dict(row["result_snapshot"]))


def _insert_event(
    conn: psycopg.Connection,
    *,
    project_id: str,
    event_type: Literal["project_created", "project_updated"],
    actor: str,
    actor_kind: str,
    expected_revision: int,
    idempotency_key: str,
    payload: dict,
    result_snapshot: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO agency_project_events (
            event_id, project_id, event_type, actor, actor_kind,
            expected_revision, resulting_revision, idempotency_key,
            payload_digest, payload, result_snapshot
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            f"agency-event-{uuid.uuid4().hex}",
            project_id,
            event_type,
            actor,
            actor_kind,
            expected_revision,
            expected_revision + 1,
            idempotency_key,
            _payload_digest(payload),
            Jsonb(payload),
            Jsonb(result_snapshot),
        ),
    )


def list_projects(
    conn: psycopg.Connection,
    *,
    query: str | None = None,
    limit: int = 100,
) -> list[dict]:
    if limit < 1 or limit > 500:
        raise AgencyDataError("project list limit must be between 1 and 500")
    params: list[Any] = []
    where = ""
    if query and query.strip():
        needle = f"%{query.strip()}%"
        where = "WHERE code ILIKE %s OR display_name ILIKE %s OR location ILIKE %s"
        params.extend([needle, needle, needle])
    params.append(limit)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT *
              FROM agency_projects
              {where}
             ORDER BY lower(display_name), lower(code), project_id
             LIMIT %s
            """,
            params,
        )
        rows = cur.fetchall()
    return [_jsonable(dict(row)) for row in rows]


def get_project(conn: psycopg.Connection, project_id: str) -> dict:
    return _project_row(conn, project_id)


def create_project(
    conn: psycopg.Connection,
    *,
    project_id: str,
    code: str,
    display_name: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    description: str = "",
    status: str | None = None,
    phase: str | None = None,
    location: str | None = None,
    primary_client: str | None = None,
    tags: list[str] | None = None,
    contacts: list[dict] | None = None,
    attributes: dict[str, Any] | None = None,
) -> dict:
    _validate_actor(actor, actor_kind)
    if actor_kind == "hermes":
        raise GovernanceGateRequired(
            "Hermes project creation requires an admitted bounded capability; direct creation is not admitted"
        )
    project_id = project_id.strip()
    code = code.strip()
    display_name = display_name.strip()
    if not project_id or not code or not display_name:
        raise AgencyDataError("project_id, code and display_name are required")

    payload = {
        "operation": "create_project",
        "project_id": project_id,
        "code": code,
        "display_name": display_name,
        "description": description,
        "status": status,
        "phase": phase,
        "location": location,
        "primary_client": primary_client,
        "tags": _normalize_tags(tags),
        "contacts": _normalize_contacts(contacts),
        "attributes": _normalize_attributes(attributes),
        "actor": actor,
        "actor_kind": actor_kind,
    }
    digest = _payload_digest(payload)

    with conn.transaction():
        replayed = _replayed_snapshot(
            conn,
            idempotency_key=idempotency_key,
            project_id=project_id,
            payload_digest=digest,
        )
        if replayed is not None:
            return replayed

        with conn.cursor() as cur:
            cur.execute("SELECT project_id FROM agency_projects WHERE project_id = %s", (project_id,))
            if cur.fetchone() is not None:
                raise AgencyDataError(f"Agency Project already exists: {project_id}")
            cur.execute(
                """
                INSERT INTO agency_projects (
                    project_id, code, display_name, description, status, phase,
                    location, primary_client, tags, contacts, attributes, created_by, updated_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    code,
                    display_name,
                    description,
                    status,
                    phase,
                    location,
                    primary_client,
                    Jsonb(payload["tags"]),
                    Jsonb(payload["contacts"]),
                    Jsonb(payload["attributes"]),
                    actor,
                    actor,
                ),
            )

        snapshot = _project_row(conn, project_id)
        _insert_event(
            conn,
            project_id=project_id,
            event_type="project_created",
            actor=actor,
            actor_kind=actor_kind,
            expected_revision=0,
            idempotency_key=idempotency_key,
            payload=payload,
            result_snapshot=snapshot,
        )
        return snapshot


def update_project(
    conn: psycopg.Connection,
    *,
    project_id: str,
    changes: dict,
    actor: str,
    actor_kind: str,
    expected_revision: int,
    idempotency_key: str,
) -> dict:
    _validate_actor(actor, actor_kind)
    if expected_revision < 1:
        raise AgencyDataError("expected_revision must be at least 1")
    unknown = set(changes) - PROJECT_MUTABLE_FIELDS
    if unknown:
        raise AgencyDataError(f"unsupported Agency Project field(s): {', '.join(sorted(unknown))}")
    if not changes:
        raise AgencyDataError("at least one project field must change")

    normalized = dict(changes)
    if "tags" in normalized:
        normalized["tags"] = _normalize_tags(normalized["tags"])
    if "contacts" in normalized:
        normalized["contacts"] = _normalize_contacts(normalized["contacts"])
    if "attributes" in normalized:
        normalized["attributes"] = _normalize_attributes(normalized["attributes"])
    for key in {"code", "display_name"} & normalized.keys():
        normalized[key] = str(normalized[key]).strip()
        if not normalized[key]:
            raise AgencyDataError(f"{key} cannot be empty")

    if actor_kind == "hermes":
        raise GovernanceGateRequired(
            "Hermes direct Agency Data mutation is disabled; use an admitted bounded capability"
        )

    payload = {
        "operation": "update_project",
        "project_id": project_id,
        "expected_revision": expected_revision,
        "changes": normalized,
        "actor": actor,
        "actor_kind": actor_kind,
    }
    digest = _payload_digest(payload)

    with conn.transaction():
        replayed = _replayed_snapshot(
            conn,
            idempotency_key=idempotency_key,
            project_id=project_id,
            payload_digest=digest,
        )
        if replayed is not None:
            return replayed

        current = _project_row(conn, project_id, lock=True)
        if current["revision"] != expected_revision:
            raise StaleProjectWrite(
                f"stale Agency Project revision: expected {expected_revision}, current {current['revision']}"
            )

        assignments: list[str] = []
        values: list[Any] = []
        for field in sorted(normalized):
            assignments.append(f"{field} = %s")
            values.append(
                Jsonb(normalized[field])
                if field in {"tags", "contacts", "attributes"}
                else normalized[field]
            )
        assignments.extend([
            "revision = revision + 1",
            "updated_by = %s",
            "updated_at = CURRENT_TIMESTAMP",
        ])
        values.extend([actor, project_id, expected_revision])
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE agency_projects
                   SET {', '.join(assignments)}
                 WHERE project_id = %s AND revision = %s
                """,
                values,
            )
            if cur.rowcount != 1:
                raise StaleProjectWrite("Agency Project changed before the mutation was persisted")

        snapshot = _project_row(conn, project_id)
        _insert_event(
            conn,
            project_id=project_id,
            event_type="project_updated",
            actor=actor,
            actor_kind=actor_kind,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            payload=payload,
            result_snapshot=snapshot,
        )
        return snapshot
