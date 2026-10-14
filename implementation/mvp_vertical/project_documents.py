"""Additive professional Project Document identity and revision owner.

The existing ``source_documents`` / ``document_versions`` tables remain the
technical source-history owner used by ingestion and extraction. This module
adds a bounded professional grouping layer above exact technical versions.
Persisting or linking a revision does not make it Evidence, approved,
contractual, current for execution, or otherwise professionally authoritative.

Opaque external issuer references belong to this same professional revision
responsibility. They are retained as append-only observations so late or
conflicting readings never rewrite revision history silently.
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

from . import store


MIGRATION = Path(__file__).resolve().parent / "sql" / "025_project_document_revisions.sql"
REFERENCE_MIGRATION = (
    Path(__file__).resolve().parent
    / "sql"
    / "028_project_document_issuer_reference_observations.sql"
)
ACTOR_KINDS = {"human", "system", "hermes"}
REFERENCE_BASIS_KINDS = {"human_declared", "source_observed", "import_metadata"}
AUTHORITY = {
    "is_evidence": False,
    "is_decision": False,
    "is_approval": False,
    "is_professional_validation": False,
    "is_contractual_authority": False,
    "is_execution_authority": False,
    "changes_project_truth": False,
    "changes_current_authority": False,
}
REFERENCE_AUTHORITY = {
    "is_evidence": False,
    "is_decision": False,
    "is_approval": False,
    "is_professional_validation": False,
    "changes_revision_order": False,
    "changes_current_authority": False,
    "changes_project_truth": False,
}


class ProjectDocumentError(ValueError):
    """Base refusal for the bounded Project Document owner."""


class ProjectDocumentNotFound(ProjectDocumentError):
    pass


class SourceVersionNotFound(ProjectDocumentError):
    pass


class CrossProjectSource(ProjectDocumentError):
    pass


class DuplicateCaptureConflict(ProjectDocumentError):
    pass


class SupersessionConflict(ProjectDocumentError):
    pass


class IdempotencyConflict(ProjectDocumentError):
    pass


class ReferenceIdempotencyConflict(ProjectDocumentError):
    pass


class GovernanceGateRequired(ProjectDocumentError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    """Connect through the existing document store and add this owner schema."""
    conn = store.connect(dsn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(REFERENCE_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(REFERENCE_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _payload_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProjectDocumentError(f"{field} is required")
    return text


def _optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _opaque_reference(value: Any) -> str:
    if not isinstance(value, str):
        raise ProjectDocumentError("reference_value must be a string")
    if not value.strip():
        raise ProjectDocumentError("reference_value must be non-empty")
    return value


def _optional_strict_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProjectDocumentError(f"{field} must be a string when provided")
    text = value.strip()
    return text or None


def _validate_actor(actor: str, actor_kind: str) -> tuple[str, str]:
    actor = _required(actor, "actor")
    actor_kind = _required(actor_kind, "actor_kind")
    if actor_kind not in ACTOR_KINDS:
        raise ProjectDocumentError("actor_kind must be human, system or hermes")
    if actor_kind == "hermes":
        raise GovernanceGateRequired(
            "Hermes direct Project Document mutation is disabled; "
            "use a separately admitted bounded capability"
        )
    return actor, actor_kind


def _with_boundary(snapshot: dict[str, Any]) -> dict[str, Any]:
    result = _jsonable(dict(snapshot))
    result["owner_system"] = "postgres"
    result["authority"] = dict(AUTHORITY)
    return result


def _replayed_snapshot(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    payload_digest: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT payload_digest, result_snapshot
              FROM doc_document_events
             WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["payload_digest"] != payload_digest:
        raise IdempotencyConflict(
            "idempotency key already belongs to another Project Document mutation"
        )
    return _jsonable(dict(row["result_snapshot"]))


def _replayed_reference_snapshot(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    payload_digest: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT payload_digest, result_snapshot
              FROM doc_document_version_reference_observations
             WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["payload_digest"] != payload_digest:
        raise ReferenceIdempotencyConflict(
            "idempotency key already belongs to another issuer-reference observation"
        )
    return _jsonable(dict(row["result_snapshot"]))


def _insert_event(
    conn: psycopg.Connection,
    *,
    document_id: str,
    event_type: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    payload_digest: str,
    result_snapshot: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO doc_document_events (
            event_id, document_id, event_type, actor, actor_kind,
            idempotency_key, payload_digest, result_snapshot
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            f"doc-event-{uuid.uuid4().hex}",
            document_id,
            event_type,
            actor,
            actor_kind,
            idempotency_key,
            payload_digest,
            Jsonb(result_snapshot),
        ),
    )


def _document_row(
    conn: psycopg.Connection,
    document_id: str,
    *,
    lock: bool = False,
) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT d.*,
                   (SELECT count(*) FROM doc_document_versions v
                     WHERE v.document_id = d.document_id) AS revision_count
              FROM doc_documents d
             WHERE d.document_id = %s{suffix}
            """,
            (document_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ProjectDocumentNotFound(f"unknown Project Document: {document_id}")
    return _with_boundary(dict(row))


def _version_row(conn: psycopg.Connection, version_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM doc_document_versions WHERE version_id = %s",
            (version_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ProjectDocumentNotFound(f"unknown Project Document revision: {version_id}")
    return _with_boundary(dict(row))


def _technical_version(
    conn: psycopg.Connection,
    *,
    source_document_id: str,
    source_version: int,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT dv.document_id, dv.version, dv.source_ref, dv.source_digest,
                   dv.media_type, dv.byte_size, dv.created_at,
                   sd.parent_project_id
              FROM document_versions dv
              JOIN source_documents sd ON sd.document_id = dv.document_id
             WHERE dv.document_id = %s AND dv.version = %s
            """,
            (source_document_id, source_version),
        )
        row = cur.fetchone()
    if row is None:
        raise SourceVersionNotFound(
            f"unknown technical document version: {source_document_id}@{source_version}"
        )
    return _jsonable(dict(row))


def get_document(conn: psycopg.Connection, document_id: str) -> dict[str, Any]:
    return _document_row(conn, document_id)


def get_revision(conn: psycopg.Connection, version_id: str) -> dict[str, Any]:
    return _version_row(conn, version_id)


def list_revisions(conn: psycopg.Connection, document_id: str) -> list[dict[str, Any]]:
    _document_row(conn, document_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM doc_document_versions
             WHERE document_id = %s
             ORDER BY version_seq, version_id
            """,
            (document_id,),
        )
        rows = cur.fetchall()
    return [_with_boundary(dict(row)) for row in rows]


def create_document(
    conn: psycopg.Connection,
    *,
    parent_project_id: str,
    document_type: str,
    title: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    document_id: str | None = None,
    lot_id: str | None = None,
    discipline_code: str | None = None,
) -> dict[str, Any]:
    actor, actor_kind = _validate_actor(actor, actor_kind)
    parent_project_id = _required(parent_project_id, "parent_project_id")
    document_type = _required(document_type, "document_type")
    title = _required(title, "title")
    idempotency_key = _required(idempotency_key, "idempotency_key")
    requested_document_id = _optional(document_id)
    normalized_lot = _optional(lot_id)
    normalized_discipline = _optional(discipline_code)

    payload = {
        "operation": "create_project_document",
        "document_id": requested_document_id,
        "parent_project_id": parent_project_id,
        "document_type": document_type,
        "title": title,
        "lot_id": normalized_lot,
        "discipline_code": normalized_discipline,
        "actor": actor,
        "actor_kind": actor_kind,
    }
    digest = _payload_digest(payload)

    with conn.transaction():
        replayed = _replayed_snapshot(
            conn,
            idempotency_key=idempotency_key,
            payload_digest=digest,
        )
        if replayed is not None:
            return replayed

        stable_id = requested_document_id or f"project-document-{uuid.uuid4().hex}"
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM doc_documents WHERE document_id = %s", (stable_id,))
            if cur.fetchone() is not None:
                raise ProjectDocumentError(f"Project Document already exists: {stable_id}")
            cur.execute(
                """
                INSERT INTO doc_documents (
                    document_id, parent_project_id, document_type, title,
                    lot_id, discipline_code, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    stable_id,
                    parent_project_id,
                    document_type,
                    title,
                    normalized_lot,
                    normalized_discipline,
                    actor,
                ),
            )

        snapshot = _document_row(conn, stable_id)
        _insert_event(
            conn,
            document_id=stable_id,
            event_type="document_created",
            actor=actor,
            actor_kind=actor_kind,
            idempotency_key=idempotency_key,
            payload_digest=digest,
            result_snapshot=snapshot,
        )
        return snapshot


def link_revision(
    conn: psycopg.Connection,
    *,
    document_id: str,
    source_document_id: str,
    source_version: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    revision_label: str | None = None,
    supersedes_version_id: str | None = None,
    received_at: datetime | None = None,
) -> dict[str, Any]:
    actor, actor_kind = _validate_actor(actor, actor_kind)
    document_id = _required(document_id, "document_id")
    source_document_id = _required(source_document_id, "source_document_id")
    idempotency_key = _required(idempotency_key, "idempotency_key")
    if source_version < 1:
        raise ProjectDocumentError("source_version must be at least 1")
    normalized_label = _optional(revision_label)
    normalized_supersedes = _optional(supersedes_version_id)
    normalized_received_at = received_at.isoformat() if received_at is not None else None

    payload = {
        "operation": "link_project_document_revision",
        "document_id": document_id,
        "source_document_id": source_document_id,
        "source_version": source_version,
        "revision_label": normalized_label,
        "supersedes_version_id": normalized_supersedes,
        "received_at": normalized_received_at,
        "actor": actor,
        "actor_kind": actor_kind,
    }
    digest = _payload_digest(payload)

    with conn.transaction():
        replayed = _replayed_snapshot(
            conn,
            idempotency_key=idempotency_key,
            payload_digest=digest,
        )
        if replayed is not None:
            return replayed

        document = _document_row(conn, document_id, lock=True)
        technical = _technical_version(
            conn,
            source_document_id=source_document_id,
            source_version=source_version,
        )
        if technical["parent_project_id"] != document["parent_project_id"]:
            raise CrossProjectSource(
                "technical source version belongs to another project scope"
            )

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM doc_document_versions
                 WHERE document_id = %s AND source_digest = %s
                """,
                (document_id, technical["source_digest"]),
            )
            duplicate = cur.fetchone()
        if duplicate is not None:
            existing = _with_boundary(dict(duplicate))
            if (
                existing.get("revision_label") != normalized_label
                or existing.get("supersedes_version_id") != normalized_supersedes
            ):
                raise DuplicateCaptureConflict(
                    "exact source content is already linked with different professional metadata"
                )
            existing["duplicate_reused"] = True
            return existing

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(version_seq), 0) AS max_seq
                  FROM doc_document_versions
                 WHERE document_id = %s
                """,
                (document_id,),
            )
            next_seq = int(cur.fetchone()["max_seq"]) + 1

        if normalized_supersedes is not None:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT document_id, version_seq FROM doc_document_versions WHERE version_id = %s",
                    (normalized_supersedes,),
                )
                superseded = cur.fetchone()
            if superseded is None:
                raise SupersessionConflict("superseded Project Document revision does not exist")
            if superseded["document_id"] != document_id:
                raise SupersessionConflict(
                    "a Project Document revision may supersede only a revision of the same document"
                )
            if int(superseded["version_seq"]) >= next_seq:
                raise SupersessionConflict("superseded revision must precede the new revision")
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM doc_document_versions WHERE supersedes_version_id = %s",
                    (normalized_supersedes,),
                )
                if cur.fetchone() is not None:
                    raise SupersessionConflict(
                        "superseded revision already has a successor in this logical document"
                    )

        version_id = f"project-document-version-{uuid.uuid4().hex}"
        persisted_received_at = received_at or datetime.fromisoformat(technical["created_at"])
        conn.execute(
            """
            INSERT INTO doc_document_versions (
                version_id, document_id, version_seq, revision_label,
                source_document_id, source_version, source_ref, source_digest,
                media_type, byte_size, received_at, supersedes_version_id, linked_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                version_id,
                document_id,
                next_seq,
                normalized_label,
                source_document_id,
                source_version,
                technical["source_ref"],
                technical["source_digest"],
                technical["media_type"],
                technical["byte_size"],
                persisted_received_at,
                normalized_supersedes,
                actor,
            ),
        )

        snapshot = _version_row(conn, version_id)
        _insert_event(
            conn,
            document_id=document_id,
            event_type="revision_linked",
            actor=actor,
            actor_kind=actor_kind,
            idempotency_key=idempotency_key,
            payload_digest=digest,
            result_snapshot=snapshot,
        )
        return snapshot


def resolve_latest_received(
    conn: psycopg.Connection,
    document_id: str,
) -> dict[str, Any] | None:
    """Read-only currentness projection based solely on receipt chronology."""
    _document_row(conn, document_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM doc_document_versions
             WHERE document_id = %s
             ORDER BY received_at DESC, version_seq DESC, version_id DESC
             LIMIT 1
            """,
            (document_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "purpose": "latest_received",
        "status": "resolved",
        "document_id": document_id,
        "version": _with_boundary(dict(row)),
        "basis": {
            "kind": "receipt_chronology",
            "received_at": _jsonable(row["received_at"]),
            "version_seq_tiebreaker": int(row["version_seq"]),
        },
        "authority": dict(AUTHORITY),
    }


def record_issuer_reference(
    conn: psycopg.Connection,
    *,
    document_version_id: str,
    reference_value: str,
    basis_kind: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    basis_ref: str | None = None,
) -> dict[str, Any]:
    """Record one exact opaque issuer-reference observation for a revision."""
    actor, actor_kind = _validate_actor(actor, actor_kind)
    document_version_id = _required(document_version_id, "document_version_id")
    reference_value = _opaque_reference(reference_value)
    basis_kind = _required(basis_kind, "basis_kind")
    if basis_kind not in REFERENCE_BASIS_KINDS:
        raise ProjectDocumentError(f"unsupported basis_kind: {basis_kind}")
    basis_ref = _optional_strict_string(basis_ref, "basis_ref")
    idempotency_key = _required(idempotency_key, "idempotency_key")

    get_revision(conn, document_version_id)
    payload = {
        "operation": "record_issuer_document_reference",
        "document_version_id": document_version_id,
        "reference_value": reference_value,
        "basis_kind": basis_kind,
        "basis_ref": basis_ref,
        "actor": actor,
        "actor_kind": actor_kind,
    }
    payload_digest = _payload_digest(payload)

    with conn.transaction():
        replay = _replayed_reference_snapshot(
            conn,
            idempotency_key=idempotency_key,
            payload_digest=payload_digest,
        )
        if replay is not None:
            return replay

        observation_id = f"doc-reference-observation-{uuid.uuid4().hex}"
        observed_at = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        snapshot = {
            "observation_id": observation_id,
            "document_version_id": document_version_id,
            "reference_value": reference_value,
            "basis_kind": basis_kind,
            "basis_ref": basis_ref,
            "observed_by": actor,
            "actor_kind": actor_kind,
            "observed_at": _jsonable(observed_at),
            "authority": dict(REFERENCE_AUTHORITY),
        }
        conn.execute(
            """
            INSERT INTO doc_document_version_reference_observations (
                observation_id, document_version_id, reference_value,
                basis_kind, basis_ref, observed_by, actor_kind,
                idempotency_key, payload_digest, result_snapshot, observed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                observation_id,
                document_version_id,
                reference_value,
                basis_kind,
                basis_ref,
                actor,
                actor_kind,
                idempotency_key,
                payload_digest,
                Jsonb(snapshot),
                observed_at,
            ),
        )
        return snapshot


def list_issuer_reference_observations(
    conn: psycopg.Connection,
    document_version_id: str,
) -> list[dict[str, Any]]:
    get_revision(conn, document_version_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT observation_id, document_version_id, reference_value,
                   basis_kind, basis_ref, observed_by, actor_kind, observed_at
              FROM doc_document_version_reference_observations
             WHERE document_version_id = %s
             ORDER BY observed_at, observation_id
            """,
            (document_version_id,),
        )
        rows = cur.fetchall()
    observations: list[dict[str, Any]] = []
    for row in rows:
        item = _jsonable(dict(row))
        item["authority"] = dict(REFERENCE_AUTHORITY)
        observations.append(item)
    return observations


def resolve_issuer_document_reference(
    conn: psycopg.Connection,
    document_version_id: str,
) -> dict[str, Any]:
    """Calculate issuer-reference posture without choosing through conflict."""
    revision = get_revision(conn, document_version_id)
    observations = list_issuer_reference_observations(conn, document_version_id)

    distinct: list[str] = []
    for observation in observations:
        value = observation["reference_value"]
        if value not in distinct:
            distinct.append(value)

    if not distinct:
        status = "unresolved"
        selected = None
    elif len(distinct) == 1:
        status = "resolved"
        selected = distinct[0]
    else:
        status = "conflicting"
        selected = None

    return {
        "document_id": revision["document_id"],
        "document_version_id": document_version_id,
        "resolution_status": status,
        "issuer_document_reference": selected,
        "observed_values": distinct,
        "observation_count": len(observations),
        "observations": observations,
        "limitations": [
            "reference values are opaque and case/punctuation sensitive",
            "observation chronology does not establish revision chronology or authority",
            "conflicting observations are not resolved by newest-wins",
        ],
        "authority": dict(REFERENCE_AUTHORITY),
    }
