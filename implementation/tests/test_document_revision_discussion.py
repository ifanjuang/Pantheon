"""PostgreSQL acceptance for B3 exact-revision human discussion."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from mvp_vertical import (
    agency_data,
    document_revision_discussion,
    human_access,
    project_documents,
)


@pytest.fixture
def conn():
    try:
        connection = document_revision_discussion.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_revision_comments, human_resource_grants, "
        "human_oidc_bindings, human_principals, "
        "doc_document_version_reference_observations, doc_document_events, "
        "doc_document_versions, doc_documents, agency_project_events, "
        "agency_projects, document_versions, source_documents "
        "RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, project_id: str) -> dict:
    project = agency_data.create_project(
        conn,
        project_id=project_id,
        code=project_id.upper(),
        display_name=f"Project {project_id}",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("project"),
    )
    conn.commit()
    return project


def _document(conn, project_id: str, title: str) -> dict:
    document = project_documents.create_document(
        conn,
        parent_project_id=project_id,
        document_type="ETUDE",
        title=title,
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    conn.commit()
    return document


def _revision(
    conn,
    *,
    project_id: str,
    document_id: str,
    label: str,
    digest_char: str,
) -> dict:
    source_document_id = _id("technical-document")
    source_ref = f"incoming/{source_document_id}-{label}.pdf"
    digest = digest_char * 64
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 1234, 'ready')
        """,
        (source_document_id, project_id, project_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (source_document_id, source_ref, digest),
    )
    conn.commit()
    revision = project_documents.link_revision(
        conn,
        document_id=document_id,
        source_document_id=source_document_id,
        source_version=1,
        revision_label=label,
        received_at=datetime(2026, 8, 8, 18, 0, tzinfo=timezone.utc),
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("revision"),
    )
    conn.commit()
    return revision


def _principal(conn, principal_ref: str) -> None:
    human_access.create_principal(
        conn,
        principal_ref=principal_ref,
        created_by="admin",
    )
    conn.commit()


def test_comment_and_reply_are_append_only_non_authoritative_context(conn) -> None:
    _project(conn, "project-a")
    document = _document(conn, "project-a", "BET structure")
    revision = _revision(
        conn,
        project_id="project-a",
        document_id=document["document_id"],
        label="C",
        digest_char="c",
    )
    _principal(conn, "principal-bet")

    before_events = conn.execute(
        "SELECT count(*) FROM doc_document_events WHERE document_id = %s",
        (document["document_id"],),
    ).fetchone()[0]
    conn.commit()

    exact_body = "  Vérifier la retombée de poutre\navant validation.  "
    exact_anchor = "page:3#detail-poutre-A"
    root = document_revision_discussion.create_comment(
        conn,
        document_version_id=revision["version_id"],
        body=exact_body,
        anchor_ref=exact_anchor,
        created_by="principal-bet",
        idempotency_key="comment-root-0001",
    )
    reply = document_revision_discussion.create_comment(
        conn,
        document_version_id=revision["version_id"],
        parent_comment_id=root["comment_id"],
        body="Réponse agence : à coordonner avec le CCTP.",
        created_by="principal-bet",
        idempotency_key="comment-reply-0001",
    )

    comments = document_revision_discussion.list_comments(
        conn,
        revision["version_id"],
    )
    assert [item["comment_id"] for item in comments] == [
        root["comment_id"],
        reply["comment_id"],
    ]
    assert comments[0]["body"] == exact_body
    assert comments[0]["anchor_ref"] == exact_anchor
    assert comments[0]["created_by"] == "principal-bet"
    assert comments[1]["parent_comment_id"] == root["comment_id"]
    assert comments[0]["authority"]["is_professional_review"] is False
    assert comments[0]["authority"]["is_approval"] is False
    assert comments[0]["authority"]["is_decision"] is False
    assert comments[0]["authority"]["is_evidence"] is False
    assert comments[0]["authority"]["changes_current_authority"] is False

    after_events = conn.execute(
        "SELECT count(*) FROM doc_document_events WHERE document_id = %s",
        (document["document_id"],),
    ).fetchone()[0]
    assert after_events == before_events

    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            "UPDATE doc_document_revision_comments SET body = 'mutated' WHERE comment_id = %s",
            (root["comment_id"],),
        )
    conn.rollback()
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            "DELETE FROM doc_document_revision_comments WHERE comment_id = %s",
            (root["comment_id"],),
        )
    conn.rollback()


def test_comment_idempotency_replays_same_payload_and_rejects_changed_payload(conn) -> None:
    _project(conn, "project-a")
    document = _document(conn, "project-a", "BET thermique")
    revision = _revision(
        conn,
        project_id="project-a",
        document_id=document["document_id"],
        label="B",
        digest_char="b",
    )
    _principal(conn, "principal-bet")

    first = document_revision_discussion.create_comment(
        conn,
        document_version_id=revision["version_id"],
        body="Même commentaire.",
        created_by="principal-bet",
        idempotency_key="comment-idem-0001",
    )
    replay = document_revision_discussion.create_comment(
        conn,
        document_version_id=revision["version_id"],
        body="Même commentaire.",
        created_by="principal-bet",
        idempotency_key="comment-idem-0001",
    )
    assert replay["comment_id"] == first["comment_id"]
    assert conn.execute(
        "SELECT count(*) FROM doc_document_revision_comments WHERE idempotency_key = %s",
        ("comment-idem-0001",),
    ).fetchone()[0] == 1
    conn.commit()

    with pytest.raises(
        document_revision_discussion.RevisionDiscussionIdempotencyConflict
    ):
        document_revision_discussion.create_comment(
            conn,
            document_version_id=revision["version_id"],
            body="Payload différent.",
            created_by="principal-bet",
            idempotency_key="comment-idem-0001",
        )


def test_reply_cannot_cross_revision_and_sql_fk_repeats_the_invariant(conn) -> None:
    _project(conn, "project-a")
    document = _document(conn, "project-a", "BET structure")
    revision_c = _revision(
        conn,
        project_id="project-a",
        document_id=document["document_id"],
        label="C",
        digest_char="c",
    )
    revision_d = _revision(
        conn,
        project_id="project-a",
        document_id=document["document_id"],
        label="D",
        digest_char="d",
    )
    _principal(conn, "principal-bet")

    parent = document_revision_discussion.create_comment(
        conn,
        document_version_id=revision_c["version_id"],
        body="Commentaire C",
        created_by="principal-bet",
        idempotency_key="comment-c-0001",
    )
    with pytest.raises(document_revision_discussion.CrossRevisionReply):
        document_revision_discussion.create_comment(
            conn,
            document_version_id=revision_d["version_id"],
            parent_comment_id=parent["comment_id"],
            body="Réponse D interdite",
            created_by="principal-bet",
            idempotency_key="comment-d-cross-0001",
        )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute(
            """
            INSERT INTO doc_document_revision_comments (
                comment_id, document_version_id, parent_comment_id,
                body, created_by, idempotency_key, payload_digest
            ) VALUES ('manual-cross-reply', %s, %s,
                      'cross revision', 'principal-bet',
                      'manual-cross-reply-key', %s)
            """,
            (revision_d["version_id"], parent["comment_id"], "f" * 64),
        )
    conn.rollback()


def test_document_comment_is_distinct_direct_access_action(conn) -> None:
    _project(conn, "project-a")
    document = _document(conn, "project-a", "BET structure")
    _principal(conn, "principal-bet")
    _principal(conn, "principal-reader")

    for principal_ref in ("principal-bet", "principal-reader"):
        human_access.grant_access(
            conn,
            principal_ref=principal_ref,
            project_id="project-a",
            resource_type="project",
            resource_id="project-a",
            action="project.read",
            granted_by="admin",
        )
        human_access.grant_access(
            conn,
            principal_ref=principal_ref,
            project_id="project-a",
            resource_type="project_document",
            resource_id=document["document_id"],
            action="document.read",
            granted_by="admin",
        )
    human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=document["document_id"],
        action="document.comment",
        granted_by="admin",
    )
    conn.commit()

    assert human_access.has_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=document["document_id"],
        action="document.comment",
    )
    assert not human_access.has_access(
        conn,
        principal_ref="principal-reader",
        project_id="project-a",
        resource_type="project_document",
        resource_id=document["document_id"],
        action="document.comment",
    )
    with pytest.raises(human_access.HumanAccessError, match="unsupported access action"):
        human_access.grant_access(
            conn,
            principal_ref="principal-bet",
            project_id="project-a",
            resource_type="project_document",
            resource_id=document["document_id"],
            action="validate_cctp",
            granted_by="admin",
        )
