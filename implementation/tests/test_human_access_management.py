"""PostgreSQL acceptance for B4 project-scoped access management extension."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import agency_data, human_access, project_documents


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = human_access.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE human_resource_grants, human_oidc_bindings, human_principals, "
        "doc_document_version_reference_observations, doc_document_events, "
        "doc_document_versions, doc_documents, agency_project_events, agency_projects "
        "RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn, project_id: str) -> None:
    agency_data.create_project(
        conn,
        project_id=project_id,
        code=project_id.upper(),
        display_name=project_id,
        actor="bootstrap",
        actor_kind="human",
        idempotency_key=_id("project"),
    )


def test_management_action_is_exact_project_scoped_and_distinct_from_document_actions(conn) -> None:
    _project(conn, "project-a")
    project_documents.create_document(
        conn,
        document_id="document-a",
        parent_project_id="project-a",
        document_type="ETUDE",
        title="Study",
        actor="bootstrap",
        actor_kind="human",
        idempotency_key=_id("document"),
    )
    human_access.create_principal(conn, principal_ref="manager", created_by="bootstrap")
    manage = human_access.grant_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.access.manage",
        granted_by="bootstrap",
    )
    conn.commit()

    assert human_access.has_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.access.manage",
    )
    assert not human_access.has_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project_document",
        resource_id="document-a",
        action="document.read",
    )
    assert manage["action"] == "project.access.manage"
    assert human_access.AUTHORITY["is_approval"] is False
    assert human_access.AUTHORITY["is_professional_role"] is False

    with pytest.raises(human_access.HumanAccessError, match="project grants support"):
        human_access.grant_access(
            conn,
            principal_ref="manager",
            project_id="project-a",
            resource_type="project",
            resource_id="not-project-a",
            action="project.access.manage",
            granted_by="bootstrap",
        )


def test_project_grant_listing_and_revocation_keep_history(conn) -> None:
    _project(conn, "project-a")
    human_access.create_principal(conn, principal_ref="person", created_by="bootstrap")
    grant = human_access.grant_access(
        conn,
        principal_ref="person",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="bootstrap",
    )
    conn.commit()

    assert [row["grant_id"] for row in human_access.list_project_grants(
        conn, project_id="project-a", include_inactive=False
    )] == [grant["grant_id"]]

    revoked = human_access.revoke_grant(conn, grant_id=grant["grant_id"])
    conn.commit()
    assert revoked["revoked_at"] is not None
    assert human_access.list_project_grants(
        conn, project_id="project-a", include_inactive=False
    ) == []
    all_rows = human_access.list_project_grants(
        conn, project_id="project-a", include_inactive=True
    )
    assert len(all_rows) == 1
    assert all_rows[0]["grant_id"] == grant["grant_id"]
    assert all_rows[0]["revoked_at"] is not None


def test_project_read_cannot_be_revoked_while_manage_grant_is_active(conn) -> None:
    _project(conn, "project-a")
    human_access.create_principal(conn, principal_ref="manager", created_by="bootstrap")
    read_grant = human_access.grant_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="bootstrap",
    )
    manage_grant = human_access.grant_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.access.manage",
        granted_by="bootstrap",
    )
    conn.commit()

    with pytest.raises(
        human_access.HumanAccessError,
        match="cannot revoke project.read while principal holds active project.access.manage",
    ):
        human_access.revoke_grant(conn, grant_id=read_grant["grant_id"])

    assert human_access.has_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
    )
    assert human_access.has_access(
        conn,
        principal_ref="manager",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.access.manage",
    )

    revoked_manage = human_access.revoke_grant(conn, grant_id=manage_grant["grant_id"])
    revoked_read = human_access.revoke_grant(conn, grant_id=read_grant["grant_id"])
    conn.commit()

    assert revoked_manage["revoked_at"] is not None
    assert revoked_read["revoked_at"] is not None
