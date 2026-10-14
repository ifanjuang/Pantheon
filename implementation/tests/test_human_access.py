"""PostgreSQL acceptance for B1 provider-neutral human access."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import agency_data, human_access, project_documents


@pytest.fixture
def conn():
    try:
        connection = human_access.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE human_resource_grants, human_oidc_bindings, human_principals, "
        "doc_document_version_reference_observations, doc_document_events, "
        "doc_document_versions, doc_documents, agency_project_events, "
        "agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, project_id: str, *, contact_role: str | None = None) -> dict:
    contacts = []
    if contact_role:
        contacts = [{"name": "External person", "organization": "BET Example", "role": contact_role}]
    project = agency_data.create_project(
        conn,
        project_id=project_id,
        code=project_id.upper(),
        display_name=f"Project {project_id}",
        contacts=contacts,
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("project-create"),
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
        idempotency_key=_id("document-create"),
    )
    conn.commit()
    return document


def _principal(conn, principal_ref: str, subject: str) -> dict:
    human_access.create_principal(conn, principal_ref=principal_ref, created_by="admin")
    binding = human_access.bind_oidc_identity(
        conn,
        principal_ref=principal_ref,
        issuer="https://id.example.test/application/o/pantheon/",
        subject=subject,
        bound_by="admin",
    )
    conn.commit()
    return binding


def _claims(subject: str, *, email: str = "same@example.test") -> dict:
    return {
        "iss": "https://id.example.test/application/o/pantheon/",
        "sub": subject,
        "name": f"User {subject}",
        "email": email,
        "iat": 100,
        "exp": 9999999999,
    }


def test_professional_role_does_not_create_access(conn) -> None:
    _project(conn, "project-a", contact_role="BET structure")
    _principal(conn, "principal-bet", "bet-subject")

    assert human_access.list_accessible_projects(conn, "principal-bet") == []
    with pytest.raises(human_access.AccessDenied):
        human_access.require_access(
            conn,
            principal_ref="principal-bet",
            project_id="project-a",
            resource_type="project",
            resource_id="project-a",
            action="project.read",
        )


def test_two_humans_are_distinct_and_external_scope_does_not_leak(conn) -> None:
    _project(conn, "project-a")
    _project(conn, "project-b")
    doc_a1 = _document(conn, "project-a", "Structure A")
    doc_a2 = _document(conn, "project-a", "Thermal A")
    _document(conn, "project-b", "Structure B")
    _principal(conn, "principal-internal", "internal-subject")
    _principal(conn, "principal-bet", "bet-subject")

    human_access.grant_access(
        conn,
        principal_ref="principal-internal",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
    )
    human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
    )
    human_access.grant_access(
        conn,
        principal_ref="principal-bet",
        project_id="project-a",
        resource_type="project_document",
        resource_id=doc_a1["document_id"],
        action="document.read",
        granted_by="admin",
    )
    conn.commit()

    internal = human_access.resolve_principal_context(conn, _claims("internal-subject"))
    bet = human_access.resolve_principal_context(conn, _claims("bet-subject"))
    assert internal.principal_ref != bet.principal_ref
    assert [p["project_id"] for p in human_access.list_accessible_projects(conn, bet.principal_ref)] == ["project-a"]
    assert [d["document_id"] for d in human_access.list_accessible_documents(
        conn, principal_ref=bet.principal_ref, project_id="project-a"
    )] == [doc_a1["document_id"]]
    assert doc_a2["document_id"] not in {
        d["document_id"] for d in human_access.list_accessible_documents(
            conn, principal_ref=bet.principal_ref, project_id="project-a"
        )
    }
    with pytest.raises(human_access.AccessDenied):
        human_access.require_access(
            conn,
            principal_ref=bet.principal_ref,
            project_id="project-b",
            resource_type="project",
            resource_id="project-b",
            action="project.read",
        )


def test_actions_are_closed_and_do_not_encode_professional_approval(conn) -> None:
    _project(conn, "project-a")
    _principal(conn, "principal-a", "subject-a")
    with pytest.raises(human_access.HumanAccessError, match="unsupported access action"):
        human_access.grant_access(
            conn,
            principal_ref="principal-a",
            project_id="project-a",
            resource_type="project",
            resource_id="project-a",
            action="approve_project",
            granted_by="admin",
        )
    assert human_access.AUTHORITY["is_approval"] is False
    assert human_access.AUTHORITY["is_decision_authority"] is False


def test_revocation_blocks_future_access_without_deleting_history(conn) -> None:
    _project(conn, "project-a")
    _principal(conn, "principal-a", "subject-a")
    grant = human_access.grant_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
        reason="temporary collaboration",
    )
    conn.commit()
    assert human_access.has_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
    )

    revoked = human_access.revoke_grant(conn, grant_id=grant["grant_id"])
    conn.commit()
    assert revoked["revoked_at"] is not None
    assert not human_access.has_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
    )
    row = conn.execute(
        "SELECT grant_id, reason, revoked_at FROM human_resource_grants WHERE grant_id = %s",
        (grant["grant_id"],),
    ).fetchone()
    assert row is not None and row[2] is not None


def test_provider_rebind_preserves_principal_and_grants(conn) -> None:
    _project(conn, "project-a")
    old_binding = _principal(conn, "principal-a", "old-subject")
    grant = human_access.grant_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
    )
    conn.commit()
    assert human_access.resolve_principal_context(conn, _claims("old-subject")).principal_ref == "principal-a"

    human_access.revoke_oidc_binding(conn, binding_id=old_binding["binding_id"])
    with pytest.raises(human_access.PrincipalNotBound):
        human_access.resolve_principal_context(conn, _claims("old-subject"))

    human_access.bind_oidc_identity(
        conn,
        principal_ref="principal-a",
        issuer="https://new-idp.example.test/",
        subject="new-subject",
        bound_by="admin",
        reason="provider migration",
    )
    conn.commit()
    migrated = human_access.resolve_principal_context(
        conn,
        {"iss": "https://new-idp.example.test/", "sub": "new-subject", "exp": 9999999999},
    )
    assert migrated.principal_ref == "principal-a"
    assert human_access.has_access(
        conn,
        principal_ref=migrated.principal_ref,
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
    )
    assert conn.execute(
        "SELECT count(*) FROM human_resource_grants WHERE grant_id = %s",
        (grant["grant_id"],),
    ).fetchone()[0] == 1


def test_email_is_projection_not_identity_key(conn) -> None:
    _principal(conn, "principal-a", "subject-a")
    _principal(conn, "principal-b", "subject-b")
    a = human_access.resolve_principal_context(conn, _claims("subject-a", email="shared@example.test"))
    b = human_access.resolve_principal_context(conn, _claims("subject-b", email="shared@example.test"))
    assert a.email == b.email
    assert a.principal_ref != b.principal_ref


def test_grant_identity_is_sql_immutable_except_revocation(conn) -> None:
    _project(conn, "project-a")
    _principal(conn, "principal-a", "subject-a")
    grant = human_access.grant_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
    )
    conn.commit()
    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute(
            "UPDATE human_resource_grants SET action = 'document.read' WHERE grant_id = %s",
            (grant["grant_id"],),
        )
    conn.rollback()
