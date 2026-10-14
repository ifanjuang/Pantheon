"""A2 admission seam from preserved Sources to professional document revisions.

This module composes existing owners. It does not upload bytes, parse documents,
classify an Inbox, create professional identity automatically, admit Evidence,
or decide which revision is current for consultation/contract/execution.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import agency_data, project_documents, source_intake

MIGRATION = Path(__file__).resolve().parent / "sql" / "026_project_document_source_admission.sql"
AUTHORITY = {
    "source_preserved": True,
    "revision_persisted": True,
    "is_evidence": False,
    "is_decision": False,
    "is_approval": False,
    "is_professional_validation": False,
    "changes_current_authority": False,
    "changes_project_truth": False,
}


class ProjectDocumentAdmissionError(ValueError):
    pass


class SourceNotAdmissible(ProjectDocumentAdmissionError):
    pass


class CaptureMismatch(ProjectDocumentAdmissionError):
    pass


class SourceAlreadyAdmitted(ProjectDocumentAdmissionError):
    pass


class AdmissionIdempotencyConflict(ProjectDocumentAdmissionError):
    pass


class GovernanceGateRequired(ProjectDocumentAdmissionError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = project_documents.connect(dsn)
    conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(source_intake.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(source_intake.MIGRATION.read_text(encoding="utf-8"))
    project_documents.ensure_schema(conn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProjectDocumentAdmissionError(f"{field} is required")
    return text


def _optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_actor(actor: str, actor_kind: str) -> tuple[str, str]:
    actor = _required(actor, "actor")
    actor_kind = _required(actor_kind, "actor_kind")
    if actor_kind not in {"human", "system", "hermes"}:
        raise ProjectDocumentAdmissionError("actor_kind must be human, system or hermes")
    if actor_kind == "hermes":
        raise GovernanceGateRequired(
            "Hermes direct Source-to-revision admission is disabled; use a separately admitted bounded capability"
        )
    return actor, actor_kind


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
                   dv.media_type, dv.byte_size, sd.parent_project_id
              FROM document_versions dv
              JOIN source_documents sd ON sd.document_id = dv.document_id
             WHERE dv.document_id = %s AND dv.version = %s
            """,
            (source_document_id, source_version),
        )
        row = cur.fetchone()
    if row is None:
        raise SourceNotAdmissible(
            f"unknown technical document version: {source_document_id}@{source_version}"
        )
    return dict(row)


def _source_row(conn: psycopg.Connection, source_id: str, *, lock: bool = False) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM agency_sources WHERE source_id = %s{suffix}", (source_id,))
        row = cur.fetchone()
    if row is None:
        raise SourceNotAdmissible(f"unknown Source: {source_id}")
    return dict(row)


def _binding_by_idempotency(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    payload_digest: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT payload_digest, result_snapshot FROM doc_document_version_sources WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["payload_digest"] != payload_digest:
        raise AdmissionIdempotencyConflict(
            "idempotency key already belongs to another Source-to-revision admission"
        )
    return dict(row["result_snapshot"])


def _binding_by_source(conn: psycopg.Connection, source_id: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT b.*, v.document_id
              FROM doc_document_version_sources b
              JOIN doc_document_versions v ON v.version_id = b.document_version_id
             WHERE b.source_id = %s
            """,
            (source_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else None


def _reconciliation_basis(source: dict[str, Any], technical: dict[str, Any]) -> str:
    checksum = _optional(source.get("checksum"))
    source_digest = str(technical["source_digest"]).strip().lower()
    if checksum is not None:
        if checksum.lower() != source_digest:
            raise CaptureMismatch("preserved Source checksum does not match the selected technical capture")
        return "checksum"

    exact_refs = {
        str(source.get("raw_source_ref") or "").strip(),
        str(source.get("origin_external_ref") or "").strip(),
    }
    exact_refs.discard("")
    if str(technical["source_ref"]).strip() not in exact_refs:
        raise CaptureMismatch(
            "Source has no checksum and neither raw_source_ref nor origin_external_ref exactly matches the selected technical capture"
        )
    return "exact_reference"


def list_revision_sources(conn: psycopg.Connection, document_version_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT source_id, document_version_id, source_revision, source_digest,
                   source_checksum, source_raw_ref, origin_system,
                   origin_external_ref, reconciliation_basis, admitted_by,
                   admitted_at
              FROM doc_document_version_sources
             WHERE document_version_id = %s
             ORDER BY admitted_at, source_id
            """,
            (document_version_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def admit_source_as_revision(
    conn: psycopg.Connection,
    *,
    source_id: str,
    document_id: str,
    source_document_id: str,
    source_version: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    revision_label: str | None = None,
    supersedes_version_id: str | None = None,
) -> dict[str, Any]:
    """Admit one already-preserved Source against one exact technical capture.

    The target logical document is explicit. No semantic matching or provider
    routing occurs here. Duplicate bytes may bind a new receipt Source to the
    existing professional revision without creating another revision.
    """
    actor, actor_kind = _validate_actor(actor, actor_kind)
    source_id = _required(source_id, "source_id")
    document_id = _required(document_id, "document_id")
    source_document_id = _required(source_document_id, "source_document_id")
    idempotency_key = _required(idempotency_key, "idempotency_key")
    if source_version < 1:
        raise ProjectDocumentAdmissionError("source_version must be at least 1")
    normalized_label = _optional(revision_label)
    normalized_supersedes = _optional(supersedes_version_id)

    payload = {
        "operation": "admit_source_as_project_document_revision",
        "source_id": source_id,
        "document_id": document_id,
        "source_document_id": source_document_id,
        "source_version": source_version,
        "revision_label": normalized_label,
        "supersedes_version_id": normalized_supersedes,
        "actor": actor,
        "actor_kind": actor_kind,
    }
    payload_digest = _digest(payload)

    with conn.transaction():
        replay = _binding_by_idempotency(
            conn,
            idempotency_key=idempotency_key,
            payload_digest=payload_digest,
        )
        if replay is not None:
            return replay

        existing_binding = _binding_by_source(conn, source_id)
        if existing_binding is not None:
            raise SourceAlreadyAdmitted(
                f"Source is already admitted to Project Document revision {existing_binding['document_version_id']}"
            )

        source = _source_row(conn, source_id, lock=True)
        if source["project_link_status"] != "linked" or source["project_id"] is None:
            raise SourceNotAdmissible("Source must be explicitly linked to one Project before revision admission")

        document = project_documents.get_document(conn, document_id)
        if source["project_id"] != document["parent_project_id"]:
            raise SourceNotAdmissible("Source and target Project Document belong to different Project scopes")

        technical = _technical_version(
            conn,
            source_document_id=source_document_id,
            source_version=source_version,
        )
        if technical["parent_project_id"] != document["parent_project_id"]:
            raise SourceNotAdmissible("selected technical capture belongs to another Project scope")

        basis = _reconciliation_basis(source, technical)

        revision = project_documents.link_revision(
            conn,
            document_id=document_id,
            source_document_id=source_document_id,
            source_version=source_version,
            revision_label=normalized_label,
            supersedes_version_id=normalized_supersedes,
            received_at=source["received_at"],
            actor=actor,
            actor_kind=actor_kind,
            idempotency_key=f"{idempotency_key}:revision",
        )

        result = {
            "source_id": source_id,
            "document_id": document_id,
            "document_version_id": revision["version_id"],
            "revision": revision,
            "reconciliation_basis": basis,
            "source_revision": int(source["revision"]),
            "source_digest": str(technical["source_digest"]),
            "duplicate_content_reused": bool(revision.get("duplicate_reused", False)),
            "authority": dict(AUTHORITY),
        }
        conn.execute(
            """
            INSERT INTO doc_document_version_sources (
                source_id, document_version_id, source_revision, source_digest,
                source_checksum, source_raw_ref, origin_system,
                origin_external_ref, reconciliation_basis, admitted_by,
                idempotency_key, payload_digest, result_snapshot
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                source_id,
                revision["version_id"],
                int(source["revision"]),
                str(technical["source_digest"]),
                source.get("checksum"),
                source["raw_source_ref"],
                source["origin_system"],
                source["origin_external_ref"],
                basis,
                actor,
                idempotency_key,
                payload_digest,
                Jsonb(result),
            ),
        )
        return result
