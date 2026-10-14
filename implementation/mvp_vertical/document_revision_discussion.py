"""Append-only human discussion on exact professional document revisions.

Discussion is collaboration context only. It does not review, approve, validate,
accept, supersede or otherwise change the professional authority of a document
revision. Technical authorization remains owned by ``human_access``.
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

from . import human_access, project_documents


MIGRATION = (
    Path(__file__).resolve().parent
    / "sql"
    / "032_document_revision_discussion.sql"
)
MAX_BODY_LENGTH = 20000
MAX_ANCHOR_LENGTH = 2000
AUTHORITY = {
    "is_discussion": True,
    "is_professional_review": False,
    "is_approval": False,
    "is_decision": False,
    "is_evidence": False,
    "changes_current_authority": False,
    "changes_project_truth": False,
}


class RevisionDiscussionError(ValueError):
    """Base refusal for revision discussion."""


class RevisionDiscussionNotFound(RevisionDiscussionError):
    pass


class RevisionDiscussionScopeError(RevisionDiscussionError):
    pass


class CrossRevisionReply(RevisionDiscussionError):
    pass


class RevisionDiscussionIdempotencyConflict(RevisionDiscussionError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = human_access.connect(dsn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    human_access.ensure_schema(conn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
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
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RevisionDiscussionError(f"{field} is required")
    return text


def _body(value: Any) -> str:
    if not isinstance(value, str):
        raise RevisionDiscussionError("body must be a string")
    if not value.strip():
        raise RevisionDiscussionError("body must be non-empty")
    if len(value) > MAX_BODY_LENGTH:
        raise RevisionDiscussionError(
            f"body must contain at most {MAX_BODY_LENGTH} characters"
        )
    return value


def _anchor(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RevisionDiscussionError("anchor_ref must be a string when provided")
    if not value.strip():
        raise RevisionDiscussionError("anchor_ref must be non-empty when provided")
    if len(value) > MAX_ANCHOR_LENGTH:
        raise RevisionDiscussionError(
            f"anchor_ref must contain at most {MAX_ANCHOR_LENGTH} characters"
        )
    return value


def _with_boundary(row: dict[str, Any]) -> dict[str, Any]:
    result = _jsonable(dict(row))
    result["authority"] = dict(AUTHORITY)
    return result


def _comment_row(conn: psycopg.Connection, comment_id: str) -> dict[str, Any]:
    comment_id = _required(comment_id, "comment_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM doc_document_revision_comments WHERE comment_id = %s",
            (comment_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise RevisionDiscussionNotFound(f"unknown revision comment: {comment_id}")
    return _with_boundary(dict(row))


def require_revision_scope(
    conn: psycopg.Connection,
    *,
    project_id: str,
    document_id: str,
    document_version_id: str,
) -> dict[str, Any]:
    """Prove exact Project -> Document -> revision identity without authorizing it."""
    project_id = _required(project_id, "project_id")
    document_id = _required(document_id, "document_id")
    document_version_id = _required(document_version_id, "document_version_id")
    document = project_documents.get_document(conn, document_id)
    if document["parent_project_id"] != project_id:
        raise RevisionDiscussionScopeError(
            "Project Document is outside the requested Project scope"
        )
    revision = project_documents.get_revision(conn, document_version_id)
    if revision["document_id"] != document_id:
        raise RevisionDiscussionScopeError(
            "Project Document revision is outside the requested document scope"
        )
    return revision


def _replayed_comment(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    payload_digest: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM doc_document_revision_comments
             WHERE idempotency_key = %s
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["payload_digest"] != payload_digest:
        raise RevisionDiscussionIdempotencyConflict(
            "idempotency key already belongs to another revision comment"
        )
    return _with_boundary(dict(row))


def create_comment(
    conn: psycopg.Connection,
    *,
    document_version_id: str,
    body: str,
    created_by: str,
    idempotency_key: str,
    parent_comment_id: str | None = None,
    anchor_ref: str | None = None,
) -> dict[str, Any]:
    """Append one comment or reply to one exact professional revision."""
    document_version_id = _required(document_version_id, "document_version_id")
    created_by = _required(created_by, "created_by")
    idempotency_key = _required(idempotency_key, "idempotency_key")
    parent_comment_id = (
        _required(parent_comment_id, "parent_comment_id")
        if parent_comment_id is not None
        else None
    )
    body = _body(body)
    anchor_ref = _anchor(anchor_ref)

    payload = {
        "operation": "create_document_revision_comment",
        "document_version_id": document_version_id,
        "parent_comment_id": parent_comment_id,
        "body": body,
        "anchor_ref": anchor_ref,
        "created_by": created_by,
    }
    digest = _payload_digest(payload)

    with conn.transaction():
        # Existence only. Authorization is deliberately outside this persistence owner.
        project_documents.get_revision(conn, document_version_id)
        replay = _replayed_comment(
            conn,
            idempotency_key=idempotency_key,
            payload_digest=digest,
        )
        if replay is not None:
            return replay

        if parent_comment_id is not None:
            parent = _comment_row(conn, parent_comment_id)
            if parent["document_version_id"] != document_version_id:
                raise CrossRevisionReply(
                    "a revision comment may reply only to a comment on the same exact revision"
                )

        comment_id = f"document-revision-comment-{uuid.uuid4().hex}"
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO doc_document_revision_comments (
                    comment_id, document_version_id, parent_comment_id,
                    body, anchor_ref, created_by,
                    idempotency_key, payload_digest
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    comment_id,
                    document_version_id,
                    parent_comment_id,
                    body,
                    anchor_ref,
                    created_by,
                    idempotency_key,
                    digest,
                ),
            )
            return _with_boundary(dict(cur.fetchone()))


def list_comments(
    conn: psycopg.Connection,
    document_version_id: str,
) -> list[dict[str, Any]]:
    document_version_id = _required(document_version_id, "document_version_id")
    project_documents.get_revision(conn, document_version_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM doc_document_revision_comments
             WHERE document_version_id = %s
             ORDER BY created_at, comment_id
            """,
            (document_version_id,),
        )
        rows = cur.fetchall()
    return [_with_boundary(dict(row)) for row in rows]
