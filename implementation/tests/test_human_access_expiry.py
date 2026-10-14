"""Expiry/renewal acceptance for B1 human access history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest

from mvp_vertical import agency_data, human_access


@pytest.fixture
def conn():
    try:
        connection = human_access.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE human_resource_grants, human_oidc_bindings, human_principals, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def test_expired_grant_can_be_reissued_without_rewriting_history(conn) -> None:
    agency_data.create_project(
        conn,
        project_id="project-a",
        code="PROJECT-A",
        display_name="Project A",
        actor="admin",
        actor_kind="human",
        idempotency_key=_id("project"),
    )
    human_access.create_principal(conn, principal_ref="principal-a", created_by="admin")
    expired_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    old_grant = conn.execute(
        """
        INSERT INTO human_resource_grants (
            grant_id, principal_ref, project_id, resource_type, resource_id,
            action, valid_from, valid_until, granted_by, reason
        ) VALUES (%s, 'principal-a', 'project-a', 'project', 'project-a',
                  'project.read', %s, %s, 'admin', 'expired temporary access')
        RETURNING grant_id
        """,
        (_id("grant"), expired_at - timedelta(hours=1), expired_at),
    ).fetchone()[0]
    conn.commit()
    assert not human_access.has_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
    )

    renewed = human_access.grant_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
        granted_by="admin",
        reason="renewed explicitly",
    )
    conn.commit()
    assert renewed["grant_id"] != old_grant
    old = conn.execute(
        "SELECT revoked_at, reason FROM human_resource_grants WHERE grant_id = %s",
        (old_grant,),
    ).fetchone()
    assert old[0] is not None
    assert old[1] == "expired temporary access"
    assert human_access.has_access(
        conn,
        principal_ref="principal-a",
        project_id="project-a",
        resource_type="project",
        resource_id="project-a",
        action="project.read",
    )


def test_expired_oidc_binding_can_be_reissued_and_old_binding_is_retained(conn) -> None:
    human_access.create_principal(conn, principal_ref="principal-a", created_by="admin")
    expired_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    old_binding = conn.execute(
        """
        INSERT INTO human_oidc_bindings (
            binding_id, principal_ref, issuer, subject, bound_by,
            valid_from, valid_until, reason
        ) VALUES (%s, 'principal-a', 'https://id.example.test/', 'subject-a',
                  'admin', %s, %s, 'expired binding')
        RETURNING binding_id
        """,
        (_id("binding"), expired_at - timedelta(hours=1), expired_at),
    ).fetchone()[0]
    conn.commit()
    with pytest.raises(human_access.PrincipalNotBound):
        human_access.resolve_principal_context(
            conn,
            {"iss": "https://id.example.test/", "sub": "subject-a", "exp": 9999999999},
        )

    renewed = human_access.bind_oidc_identity(
        conn,
        principal_ref="principal-a",
        issuer="https://id.example.test/",
        subject="subject-a",
        bound_by="admin",
        reason="explicit renewal",
    )
    conn.commit()
    assert renewed["binding_id"] != old_binding
    old = conn.execute(
        "SELECT revoked_at, reason FROM human_oidc_bindings WHERE binding_id = %s",
        (old_binding,),
    ).fetchone()
    assert old[0] is not None
    assert old[1] == "expired binding"
    context = human_access.resolve_principal_context(
        conn,
        {"iss": "https://id.example.test/", "sub": "subject-a", "exp": 9999999999},
    )
    assert context.principal_ref == "principal-a"
