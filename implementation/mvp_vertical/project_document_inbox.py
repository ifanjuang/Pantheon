"""Read-only governed reconciliation for imported document Sources.

This is a projection over existing Source, technical capture and professional
revision owners. Exact deterministic identity signals always win. Optional
semantic candidates may be projected for human review only; they never bind a
professional identity, create a revision or route a provider.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import project_document_currentness, project_documents, source_intake

AUTHORITY = {
    "project_link_confirmed": False,
    "technical_capture_selected": False,
    "professional_identity_confirmed": False,
    "revision_admitted": False,
    "is_evidence": False,
    "changes_project_truth": False,
}

SEMANTIC_CANDIDATE_FIELDS = {"document_id", "score", "basis", "producer", "created_at"}


class ProjectDocumentInboxError(ValueError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    return project_document_currentness.connect(dsn)


def _capture_projection(row: dict[str, Any], basis: str) -> dict[str, Any]:
    return {
        "source_document_id": row["document_id"],
        "source_version": int(row["version"]),
        "source_ref": row["source_ref"],
        "source_digest": row["source_digest"],
        "media_type": row["media_type"],
        "byte_size": int(row["byte_size"]),
        "basis": basis,
    }


def _admitted_binding(conn: psycopg.Connection, source_id: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT b.source_id, b.document_version_id, b.reconciliation_basis,
                   v.document_id, v.version_seq, v.revision_label,
                   v.source_document_id, v.source_version, v.source_digest,
                   d.parent_project_id, d.document_type, d.title
              FROM doc_document_version_sources b
              JOIN doc_document_versions v ON v.version_id = b.document_version_id
              JOIN doc_documents d ON d.document_id = v.document_id
             WHERE b.source_id = %s
            """,
            (source_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else None


def _technical_candidates(
    conn: psycopg.Connection,
    source: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    project_id = source["project_id"]
    checksum = str(source.get("checksum") or "").strip().lower()
    with conn.cursor(row_factory=dict_row) as cur:
        if checksum:
            cur.execute(
                """
                SELECT dv.document_id, dv.version, dv.source_ref, dv.source_digest,
                       dv.media_type, dv.byte_size
                  FROM document_versions dv
                  JOIN source_documents sd ON sd.document_id = dv.document_id
                 WHERE sd.parent_project_id = %s
                   AND lower(dv.source_digest) = %s
                 ORDER BY dv.document_id, dv.version
                """,
                (project_id, checksum),
            )
            return "checksum", [dict(row) for row in cur.fetchall()]

        refs = sorted(
            {
                value
                for value in (
                    str(source.get("raw_source_ref") or "").strip(),
                    str(source.get("origin_external_ref") or "").strip(),
                )
                if value
            }
        )
        if not refs:
            return "exact_reference", []
        cur.execute(
            """
            SELECT dv.document_id, dv.version, dv.source_ref, dv.source_digest,
                   dv.media_type, dv.byte_size
              FROM document_versions dv
              JOIN source_documents sd ON sd.document_id = dv.document_id
             WHERE sd.parent_project_id = %s
               AND dv.source_ref = ANY(%s)
             ORDER BY dv.document_id, dv.version
            """,
            (project_id, refs),
        )
        return "exact_reference", [dict(row) for row in cur.fetchall()]


def _professional_digest_matches(
    conn: psycopg.Connection,
    *,
    project_id: str,
    digest: str,
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT v.version_id, v.document_id, v.version_seq, v.revision_label,
                   v.source_document_id, v.source_version, v.source_digest,
                   d.document_type, d.title, d.lot_id, d.discipline_code
              FROM doc_document_versions v
              JOIN doc_documents d ON d.document_id = v.document_id
             WHERE d.parent_project_id = %s
               AND lower(v.source_digest) = lower(%s)
             ORDER BY v.document_id, v.version_seq, v.version_id
            """,
            (project_id, digest),
        )
        return [dict(row) for row in cur.fetchall()]


def _professional_lineage(
    conn: psycopg.Connection,
    *,
    project_id: str,
    source_document_id: str,
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT v.version_id, v.document_id, v.version_seq, v.revision_label,
                   v.source_document_id, v.source_version, v.source_digest,
                   d.document_type, d.title, d.lot_id, d.discipline_code
              FROM doc_document_versions v
              JOIN doc_documents d ON d.document_id = v.document_id
             WHERE d.parent_project_id = %s
               AND v.source_document_id = %s
             ORDER BY v.document_id, v.version_seq DESC, v.version_id
            """,
            (project_id, source_document_id),
        )
        return [dict(row) for row in cur.fetchall()]


def _normalize_semantic_candidates(
    conn: psycopg.Connection,
    *,
    project_id: str,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate advisory document candidates without selecting or persisting one."""
    if len(candidates) > 50:
        raise ProjectDocumentInboxError("at most 50 semantic document candidates are supported")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            raise ProjectDocumentInboxError(f"semantic candidate {index + 1} must be an object")
        missing = SEMANTIC_CANDIDATE_FIELDS - set(item)
        unknown = set(item) - SEMANTIC_CANDIDATE_FIELDS
        if missing:
            raise ProjectDocumentInboxError(
                f"semantic candidate {index + 1} missing: {', '.join(sorted(missing))}"
            )
        if unknown:
            raise ProjectDocumentInboxError(
                f"semantic candidate {index + 1} unsupported fields: {', '.join(sorted(unknown))}"
            )

        document_id = str(item["document_id"]).strip()
        if not document_id or document_id in seen:
            raise ProjectDocumentInboxError("semantic candidate document_id must be non-empty and unique")
        seen.add(document_id)

        try:
            score = float(item["score"])
        except (TypeError, ValueError) as exc:
            raise ProjectDocumentInboxError("semantic candidate score must be numeric") from exc
        if not 0 <= score <= 1:
            raise ProjectDocumentInboxError("semantic candidate score must be between 0 and 1")

        if not isinstance(item["basis"], list):
            raise ProjectDocumentInboxError("semantic candidate basis must be a list")
        basis = [str(value).strip() for value in item["basis"] if str(value).strip()]
        producer = str(item["producer"]).strip()
        created_at = str(item["created_at"]).strip()
        if not basis or not producer or not created_at:
            raise ProjectDocumentInboxError(
                "semantic candidate basis, producer and created_at are required"
            )

        try:
            document = project_documents.get_document(conn, document_id)
        except project_documents.ProjectDocumentNotFound as exc:
            raise ProjectDocumentInboxError(f"unknown semantic candidate Document: {document_id}") from exc
        if document["parent_project_id"] != project_id:
            raise ProjectDocumentInboxError(
                f"semantic candidate Document belongs to another Project: {document_id}"
            )

        normalized.append(
            {
                "document_id": document_id,
                "document_type": document["document_type"],
                "title": document["title"],
                "lot_id": document.get("lot_id"),
                "discipline_code": document.get("discipline_code"),
                "score": score,
                "basis": basis,
                "producer": producer,
                "created_at": created_at,
            }
        )

    return sorted(normalized, key=lambda item: (-item["score"], item["document_id"]))


def _base(source: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "source_project_status": source["project_link_status"],
        "project_id": source.get("project_id"),
        "status": status,
        "authority": dict(AUTHORITY),
    }


def reconcile_source(
    conn: psycopg.Connection,
    *,
    source_id: str,
    semantic_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Calculate the next safe intake posture for one preserved Source."""
    source = source_intake.get_source(conn, source_id)

    admitted = _admitted_binding(conn, source_id)
    if admitted is not None:
        result = _base(source, "already_admitted")
        result["admitted"] = admitted
        result["authority"] = {
            **AUTHORITY,
            "project_link_confirmed": source["project_link_status"] == "linked",
            "technical_capture_selected": True,
            "professional_identity_confirmed": True,
            "revision_admitted": True,
        }
        return result

    if source["project_link_status"] == "excluded":
        result = _base(source, "excluded")
        result["reason"] = "Source is excluded from intake"
        return result

    if source["project_link_status"] != "linked" or source.get("project_id") is None:
        result = _base(source, "needs_project_link")
        result["project_candidates"] = list(source.get("candidate_project_refs") or [])
        result["reason"] = "reuse Source Intake project-link resolution before document reconciliation"
        return result

    basis, captures = _technical_candidates(conn, source)
    capture_projections = [_capture_projection(row, basis) for row in captures]
    if not captures:
        result = _base(source, "needs_technical_capture")
        result["reconciliation_basis"] = basis
        result["technical_candidates"] = []
        result["reason"] = "no exact technical capture matches the preserved Source"
        return result

    if len(captures) > 1:
        result = _base(source, "technical_capture_ambiguous")
        result["reconciliation_basis"] = basis
        result["technical_candidates"] = capture_projections
        result["reason"] = "multiple exact technical captures match; no newest-wins rule is permitted"
        return result

    capture = captures[0]
    capture_projection = capture_projections[0]
    digest_matches = _professional_digest_matches(
        conn,
        project_id=source["project_id"],
        digest=capture["source_digest"],
    )
    if len(digest_matches) == 1:
        result = _base(source, "probable_duplicate_receipt")
        result["technical_capture"] = capture_projection
        result["professional_candidate"] = digest_matches[0]
        result["candidate_basis"] = "exact_professional_content_digest"
        result["reason"] = "same bytes already belong to one exact professional revision"
        return result
    if len(digest_matches) > 1:
        result = _base(source, "document_identity_ambiguous")
        result["technical_capture"] = capture_projection
        result["professional_candidates"] = digest_matches
        result["candidate_basis"] = "exact_digest_used_by_multiple_logical_documents"
        result["reason"] = "identical bytes are already attached to more than one logical document"
        return result

    lineage = _professional_lineage(
        conn,
        project_id=source["project_id"],
        source_document_id=capture["document_id"],
    )
    document_ids = sorted({item["document_id"] for item in lineage})
    if len(document_ids) == 1:
        predecessor = lineage[0]
        result = _base(source, "probable_new_revision")
        result["technical_capture"] = capture_projection
        result["professional_candidate"] = {
            "document_id": predecessor["document_id"],
            "document_type": predecessor["document_type"],
            "title": predecessor["title"],
            "lot_id": predecessor.get("lot_id"),
            "discipline_code": predecessor.get("discipline_code"),
            "suggested_predecessor_version_id": predecessor["version_id"],
            "suggested_predecessor_revision_label": predecessor.get("revision_label"),
        }
        result["candidate_basis"] = "same_technical_source_identity_existing_professional_lineage"
        result["reason"] = "new bytes come from one technical source identity already owned by one logical document"
        return result
    if len(document_ids) > 1:
        result = _base(source, "document_identity_ambiguous")
        result["technical_capture"] = capture_projection
        result["professional_candidates"] = lineage
        result["candidate_basis"] = "technical_source_identity_used_by_multiple_logical_documents"
        result["reason"] = "technical source identity is not uniquely owned by one logical document"
        return result

    if semantic_candidates:
        candidates = _normalize_semantic_candidates(
            conn,
            project_id=source["project_id"],
            candidates=semantic_candidates,
        )
        result = _base(source, "document_identity_candidates")
        result["technical_capture"] = capture_projection
        result["professional_candidates"] = candidates
        result["candidate_basis"] = "semantic_candidate_projection"
        result["reason"] = (
            "advisory semantic candidates require explicit human selection or explicit new-identity creation "
            "through the existing governed admission path"
        )
        result["limitations"] = [
            "candidate score does not bind professional identity",
            "candidate producer output is not Evidence or professional approval",
            "no candidate can create, merge or mutate a Document identity",
        ]
        return result

    result = _base(source, "needs_document_identity")
    result["technical_capture"] = capture_projection
    result["candidate_basis"] = "no_deterministic_professional_lineage"
    result["reason"] = (
        "new content has no exact professional duplicate and no unique prior professional lineage; "
        "explicit user context or an advisory semantic candidate projection is required"
    )
    return result
