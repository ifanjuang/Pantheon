"""API acceptance for B3 OIDC-scoped exact-revision discussion."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest
from fastapi.testclient import TestClient

from mvp_vertical import (
    agency_data,
    document_revision_discussion,
    human_access,
    project_documents,
    store,
)
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


class FakeVerifier:
    def __init__(self, tokens: dict[str, dict]):
        self.tokens = tokens

    def verify(self, token: str) -> dict:
        if token not in self.tokens:
            raise human_access.AuthenticationFailed("OIDC access token verification failed")
        return self.tokens[token]


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _seed_revision(conn, *, project_id: str, document_id: str, label: str, digest_char: str) -> dict:
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


def _bind_principal(conn, principal_ref: str, subject: str) -> None:
    human_access.create_principal(conn, principal_ref=principal_ref, created_by="admin")
    human_access.bind_oidc_identity(
        conn,
        principal_ref=principal_ref,
        issuer="https://id.example.test/",
        subject=subject,
        bound_by="admin",
    )
    conn.commit()


def _grant_read(conn, principal_ref: str, project_id: str, document_id: str) -> None:
    human_access.grant_access(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
        resource_type="project",
        resource_id=project_id,
        action="project.read",
        granted_by="admin",
    )
    human_access.grant_access(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
        resource_type="project_document",
        resource_id=document_id,
        action="document.read",
        granted_by="admin",
    )
    conn.commit()


@pytest.fixture
def prepared():
    try:
        conn = store.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    document_revision_discussion.ensure_schema(conn)
    conn.execute(
        "TRUNCATE doc_document_revision_comments, human_resource_grants, "
        "human_oidc_bindings, human_principals, "
        "doc_document_version_reference_observations, doc_document_events, "
        "doc_document_versions, doc_documents, agency_project_events, "
        "agency_projects, document_versions, source_documents "
        "RESTART IDENTITY CASCADE"
    )
    conn.commit()

    for project_id in ("project-a", "project-b"):
        agency_data.create_project(
            conn,
            project_id=project_id,
            code=project_id.upper(),
            display_name=f"Project {project_id}",
            actor="admin",
            actor_kind="human",
            idempotency_key=_id("project"),
        )
    doc_a1 = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="ETUDE",
        title="BET structure",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    doc_a2 = project_documents.create_document(
        conn,
        parent_project_id="project-a",
        document_type="DEVIS",
        title="Offer private",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    doc_b = project_documents.create_document(
        conn,
        parent_project_id="project-b",
        document_type="ETUDE",
        title="Other project study",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    conn.commit()

    revision_a1 = _seed_revision(
        conn,
        project_id="project-a",
        document_id=doc_a1["document_id"],
        label="C",
        digest_char="c",
    )
    revision_a2 = _seed_revision(
        conn,
        project_id="project-a",
        document_id=doc_a2["document_id"],
        label="1",
        digest_char="d",
    )
    revision_b = _seed_revision(
        conn,
        project_id="project-b",
        document_id=doc_b["document_id"],
        label="A",
        digest_char="e",
    )

    _bind_principal(conn, "principal-bet", "bet-subject")
    _bind_principal(conn, "principal-reader", "reader-subject")
    for principal_ref in ("principal-bet", "principal-reader"):
        _grant_read(conn, principal_ref, "project-a", doc_a1["document_id"])
    human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=doc_a1["document_id"],
        action="document.comment",
        granted_by="admin",
    )
    conn.commit()
    conn.close()

    verifier = FakeVerifier(
        {
            "bet-token": {
                "iss": "https://id.example.test/",
                "sub": "bet-subject",
                "name": "BET User",
                "email": "bet@example.test",
                "exp": 9999999999,
            },
            "reader-token": {
                "iss": "https://id.example.test/",
                "sub": "reader-subject",
                "name": "Reader User",
                "email": "reader@example.test",
                "exp": 9999999999,
            },
        }
    )

    def connect_fn():
        return psycopg.connect(store.dsn_from_env())

    app = create_composed_cockpit_app(
        connect_fn=connect_fn,
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
        oidc_verifier=verifier,
    )
    return {
        "client": TestClient(app),
        "doc_a1": doc_a1,
        "doc_a2": doc_a2,
        "doc_b": doc_b,
        "revision_a1": revision_a1,
        "revision_a2": revision_a2,
        "revision_b": revision_b,
    }


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _comment_path(prepared, *, document=None, revision=None) -> str:
    document = document or prepared["doc_a1"]
    revision = revision or prepared["revision_a1"]
    return (
        f"/me/projects/{document['parent_project_id']}"
        f"/documents/{document['document_id']}"
        f"/revisions/{revision['version_id']}/comments"
    )


def test_comment_post_uses_verified_principal_and_reader_can_read_without_comment_grant(prepared) -> None:
    client = prepared["client"]
    response = client.post(
        _comment_path(prepared),
        headers={**_auth("bet-token"), "Idempotency-Key": "bet-comment-0001"},
        json={
            "body": "Merci de confirmer la cote 2,40 m.",
            "anchor_ref": "page:3#cote-240",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["principal_ref"] == "principal-bet"
    assert payload["comment"]["created_by"] == "principal-bet"
    assert payload["comment"]["body"] == "Merci de confirmer la cote 2,40 m."
    assert payload["authority"]["is_professional_review"] is False
    assert payload["authority"]["is_approval"] is False
    assert payload["authority"]["is_decision"] is False

    visible = client.get(
        _comment_path(prepared),
        headers=_auth("reader-token"),
    )
    assert visible.status_code == 200
    assert [item["comment_id"] for item in visible.json()["comments"]] == [
        payload["comment"]["comment_id"]
    ]

    conn = psycopg.connect(store.dsn_from_env())
    try:
        row = conn.execute(
            "SELECT created_by, body FROM doc_document_revision_comments WHERE comment_id = %s",
            (payload["comment"]["comment_id"],),
        ).fetchone()
    finally:
        conn.close()
    assert row == ("principal-bet", "Merci de confirmer la cote 2,40 m.")


def test_read_permission_does_not_imply_document_comment(prepared) -> None:
    client = prepared["client"]
    assert client.get(
        _comment_path(prepared),
        headers=_auth("reader-token"),
    ).status_code == 200
    denied = client.post(
        _comment_path(prepared),
        headers={**_auth("reader-token"), "Idempotency-Key": "reader-comment-0001"},
        json={"body": "Je ne dois pas pouvoir publier."},
    )
    assert denied.status_code == 403


def test_scope_checks_block_ungranted_document_other_project_and_mismatched_revision(prepared) -> None:
    client = prepared["client"]

    ungranted_document = client.get(
        _comment_path(
            prepared,
            document=prepared["doc_a2"],
            revision=prepared["revision_a2"],
        ),
        headers=_auth("bet-token"),
    )
    assert ungranted_document.status_code == 403

    other_project = client.get(
        _comment_path(
            prepared,
            document=prepared["doc_b"],
            revision=prepared["revision_b"],
        ),
        headers=_auth("bet-token"),
    )
    assert other_project.status_code == 403

    mismatched = client.get(
        _comment_path(
            prepared,
            document=prepared["doc_a1"],
            revision=prepared["revision_a2"],
        ),
        headers=_auth("bet-token"),
    )
    assert mismatched.status_code == 404


def test_comment_api_idempotency_and_required_key(prepared) -> None:
    client = prepared["client"]
    path = _comment_path(prepared)
    headers = {**_auth("bet-token"), "Idempotency-Key": "bet-comment-idem-0001"}
    first = client.post(path, headers=headers, json={"body": "Même requête."})
    replay = client.post(path, headers=headers, json={"body": "Même requête."})
    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json()["comment"]["comment_id"] == first.json()["comment"]["comment_id"]

    conflict = client.post(path, headers=headers, json={"body": "Requête différente."})
    assert conflict.status_code == 409

    missing = client.post(
        path,
        headers=_auth("bet-token"),
        json={"body": "Sans clé."},
    )
    assert missing.status_code == 422
