"""Provider-neutral OIDC principal binding and direct scoped human access.

This module is an implementation/security seam. It does not own professional
roles, project participation, approval, Evidence, decision authority, IdP
invitation lifecycle or provider routing.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

import psycopg
from psycopg.rows import dict_row

from . import agency_data, project_documents, store
from .policy_gate import PolicyClient, enforce_consequential

MIGRATION = Path(__file__).resolve().parent / "sql" / "030_human_principal_access.sql"
ACTION_MIGRATION = (
    Path(__file__).resolve().parent
    / "sql"
    / "031_human_document_comment_access.sql"
)
MANAGEMENT_MIGRATION = (
    Path(__file__).resolve().parent
    / "sql"
    / "033_human_project_access_management.sql"
)
ACTIONS = {
    "project.read",
    "project.access.manage",
    "document.read",
    "document.revision.submit",
    "document.comment",
}
RESOURCE_TYPES = {"project", "project_document"}


class HumanAccessError(ValueError):
    """Base refusal for bounded human authentication/access."""


class AccessConfigurationError(HumanAccessError):
    pass


class AuthenticationFailed(HumanAccessError):
    pass


class PrincipalNotFound(HumanAccessError):
    pass


class PrincipalNotBound(HumanAccessError):
    pass


class PrincipalDisabled(HumanAccessError):
    pass


class BindingRefused(HumanAccessError):
    """The chokepoint refused this identity binding."""


class BindingPolicyUnavailable(HumanAccessError):
    """The decision point could not be reached; the binding fails closed."""


class BindingConflict(HumanAccessError):
    pass


class GrantConflict(HumanAccessError):
    pass


class AccessDenied(HumanAccessError):
    pass


@dataclass(frozen=True)
class PrincipalContext:
    principal_ref: str
    issuer: str
    subject: str
    display_name: str | None = None
    email: str | None = None
    issued_at: Any = None
    expires_at: Any = None
    auth_time: Any = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Mapping[str, Any]: ...


class OidcJwtVerifier:
    """Verify a provider-neutral OIDC/JWT access token against explicit config.

    Provider discovery is deliberately not hidden in Pantheon. Deployment supplies
    issuer, audience and JWKS URL explicitly; the verifier validates signature,
    issuer, audience, expiry and subject. Provider-specific SDKs are not used.
    """

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        algorithms: tuple[str, ...] = ("RS256",),
    ) -> None:
        self.issuer = _required(issuer, "issuer")
        self.audience = _required(audience, "audience")
        self.jwks_url = _required(jwks_url, "jwks_url")
        if not algorithms or any(not str(item).strip() for item in algorithms):
            raise AccessConfigurationError("at least one explicit JWT algorithm is required")
        self.algorithms = tuple(str(item).strip() for item in algorithms)
        self._jwks_client = None

    @classmethod
    def from_env_optional(cls) -> "OidcJwtVerifier | None":
        issuer = os.getenv("MVP_OIDC_ISSUER", "").strip()
        audience = os.getenv("MVP_OIDC_AUDIENCE", "").strip()
        jwks_url = os.getenv("MVP_OIDC_JWKS_URL", "").strip()
        algorithms_raw = os.getenv("MVP_OIDC_ALGORITHMS", "RS256").strip()
        configured = [bool(issuer), bool(audience), bool(jwks_url)]
        if not any(configured):
            return None
        if not all(configured):
            raise AccessConfigurationError(
                "MVP_OIDC_ISSUER, MVP_OIDC_AUDIENCE and MVP_OIDC_JWKS_URL must be configured together"
            )
        algorithms = tuple(item.strip() for item in algorithms_raw.split(",") if item.strip())
        return cls(
            issuer=issuer,
            audience=audience,
            jwks_url=jwks_url,
            algorithms=algorithms,
        )

    def verify(self, token: str) -> Mapping[str, Any]:
        token = _required(token, "access token")
        try:
            import jwt
        except ImportError as exc:  # pragma: no cover - packaging contract covers this
            raise AccessConfigurationError(
                "PyJWT crypto support is required for configured OIDC human access"
            ) from exc
        try:
            if self._jwks_client is None:
                self._jwks_client = jwt.PyJWKClient(self.jwks_url)
            key = self._jwks_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except Exception as exc:
            raise AuthenticationFailed("OIDC access token verification failed") from exc
        if not str(claims.get("sub") or "").strip():
            raise AuthenticationFailed("OIDC subject is required")
        return claims


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = store.connect(dsn)
    conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    project_documents.ensure_schema(conn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(ACTION_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(MANAGEMENT_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(project_documents.MIGRATION.read_text(encoding="utf-8"))
    conn.execute(project_documents.REFERENCE_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(ACTION_MIGRATION.read_text(encoding="utf-8"))
    conn.execute(MANAGEMENT_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HumanAccessError(f"{field} is required")
    return text


def _optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _active_window_sql(alias: str) -> str:
    return (
        f"{alias}.revoked_at IS NULL "
        f"AND {alias}.valid_from <= CURRENT_TIMESTAMP "
        f"AND ({alias}.valid_until IS NULL OR {alias}.valid_until > CURRENT_TIMESTAMP)"
    )


def _principal_row(conn: psycopg.Connection, principal_ref: str) -> dict[str, Any]:
    principal_ref = _required(principal_ref, "principal_ref")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM human_principals WHERE principal_ref = %s", (principal_ref,))
        row = cur.fetchone()
    if row is None:
        raise PrincipalNotFound(f"unknown human principal: {principal_ref}")
    return dict(row)


def create_principal(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    created_by: str,
) -> dict[str, Any]:
    principal_ref = _required(principal_ref, "principal_ref")
    created_by = _required(created_by, "created_by")
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO human_principals (principal_ref, created_by)
            VALUES (%s, %s)
            ON CONFLICT (principal_ref) DO NOTHING
            """,
            (principal_ref, created_by),
        )
        return _principal_row(conn, principal_ref)


def disable_principal(conn: psycopg.Connection, *, principal_ref: str) -> dict[str, Any]:
    principal = _principal_row(conn, principal_ref)
    if principal["disabled_at"] is not None:
        return principal
    with conn.transaction():
        conn.execute(
            "UPDATE human_principals SET disabled_at = clock_timestamp() WHERE principal_ref = %s",
            (principal_ref,),
        )
        return _principal_row(conn, principal_ref)


def binding_digest(
    *,
    principal_ref: str,
    issuer: str,
    subject: str,
    valid_until: Any = None,
) -> str:
    """Digest the exact binding being made, so a decision can cover a content.

    An approval that names a binding is worth less than one that covers it. This
    is the shape `apu_write_preparation.append_authorization` already uses, and
    the one this review recommended everywhere else.
    """
    payload = {
        "operation": "bind_oidc_identity",
        "principal_ref": principal_ref,
        "issuer": issuer,
        "subject": subject,
        "valid_until": None if valid_until is None else str(valid_until),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def bind_oidc_identity(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    issuer: str,
    subject: str,
    bound_by: str,
    reason: str | None = None,
    valid_until: Any = None,
    policy_client: PolicyClient | None = None,
    decision_payload: dict[str, Any] | None = None,
    required_ceiling: str = "C3",
) -> dict[str, Any]:
    """Make an external OIDC identity able to act as a governed principal.

    This is the root of trust for every route behind `require_principal`:
    `resolve_principal_context` resolves each request against the row this
    writes. Nothing else in the product writes it.

    `project.access.manage` cannot authorize this act, and that is not a gap in
    this module. `033_human_project_access_management.sql` says so in the
    schema: that action "does not encode professional role, approval, Decision,
    Evidence or IdP invitation authority", and it "remains a locally provisioned
    bootstrap capability". A project-scoped grant producing a system-wide
    identity would be an escalation, and the grant table could not express the
    permission anyway — `project_id` is NOT NULL against `agency_projects`.

    So the authority for a binding is not a grant. It is the chokepoint: when
    `policy_client` is supplied, the effect routes through
    `enforce_consequential` with an expectation bound to
    `binding_digest(...)`, so the decision must cover this exact binding rather
    than name it. Composition is where that becomes mandatory — see the CLI,
    which refuses to bind unless a decision point is configured or enforcement
    is explicitly declared disabled.
    """
    principal = _principal_row(conn, principal_ref)
    if principal["disabled_at"] is not None:
        raise PrincipalDisabled(f"human principal is disabled: {principal_ref}")
    issuer = _required(issuer, "issuer")
    subject = _required(subject, "subject")
    bound_by = _required(bound_by, "bound_by")
    reason = _optional(reason)

    if policy_client is not None:
        digest = binding_digest(
            principal_ref=principal_ref,
            issuer=issuer,
            subject=subject,
            valid_until=valid_until,
        )
        # A binding is not project-scoped: it makes an identity able to act
        # wherever that principal is granted anything. The scope of the act is
        # the principal, and saying so is more truthful than borrowing a project.
        scope = {"scope_type": "human_principal", "scope_id": principal_ref}
        object_identity = f"human_oidc_binding:{principal_ref}:{issuer}:{subject}"
        expectation = {
            "required_ceiling": required_ceiling,
            "required_scope": scope,
            "object_identity": object_identity,
            "expected_digest": digest,
        }
        candidate = {
            "intent": "bind_oidc_identity",
            "decision_expectation": expectation,
            "request": {
                "intent": "bind_oidc_identity",
                # Writes governed state, sends nothing, promotes no memory.
                "external_effect": False,
                "writes_state": True,
                "transmission_requested": False,
                "memory_promotion_requested": False,
                "professional_position": False,
                "financial_or_contractual_effect": False,
                "scope": scope,
            },
        }
        verdict = enforce_consequential(
            policy_client,
            candidate=candidate,
            decision_payload=dict(decision_payload or {}),
        )
        if not verdict.allowed:
            message = (
                "policy chokepoint blocked the OIDC identity binding "
                f"({verdict.disposition}): {verdict.reasons}"
            )
            if verdict.disposition == "policy_unavailable":
                raise BindingPolicyUnavailable(message)
            raise BindingRefused(message)

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT * FROM human_oidc_bindings b
                 WHERE b.issuer = %s AND b.subject = %s AND {_active_window_sql('b')}
                """,
                (issuer, subject),
            )
            existing = cur.fetchone()
        if existing is not None:
            row = dict(existing)
            if row["principal_ref"] != principal_ref:
                raise BindingConflict("OIDC issuer+subject is already bound to another principal")
            return row

        binding_id = f"human-binding-{uuid.uuid4().hex}"
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO human_oidc_bindings (
                    binding_id, principal_ref, issuer, subject, bound_by, reason, valid_until
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (binding_id, principal_ref, issuer, subject, bound_by, reason, valid_until),
            )
            return dict(cur.fetchone())


def revoke_oidc_binding(conn: psycopg.Connection, *, binding_id: str) -> dict[str, Any]:
    binding_id = _required(binding_id, "binding_id")
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM human_oidc_bindings WHERE binding_id = %s", (binding_id,))
            row = cur.fetchone()
        if row is None:
            raise PrincipalNotBound(f"unknown OIDC binding: {binding_id}")
        if row["revoked_at"] is None:
            conn.execute(
                "UPDATE human_oidc_bindings SET revoked_at = clock_timestamp() WHERE binding_id = %s",
                (binding_id,),
            )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM human_oidc_bindings WHERE binding_id = %s", (binding_id,))
            return dict(cur.fetchone())


def _validate_grant_target(
    conn: psycopg.Connection,
    *,
    project_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
) -> None:
    if resource_type not in RESOURCE_TYPES:
        raise HumanAccessError(f"unsupported resource_type: {resource_type}")
    if action not in ACTIONS:
        raise HumanAccessError(f"unsupported access action: {action}")
    agency_data.get_project(conn, project_id)
    if resource_type == "project":
        if resource_id != project_id or action not in {"project.read", "project.access.manage"}:
            raise HumanAccessError(
                "project grants support only project.read or project.access.manage on the exact project id"
            )
        return
    if action not in {"document.read", "document.revision.submit", "document.comment"}:
        raise HumanAccessError(
            "Project Document grants support only document.read, document.revision.submit or document.comment"
        )
    document = project_documents.get_document(conn, resource_id)
    if document["parent_project_id"] != project_id:
        raise HumanAccessError("Project Document grant target belongs to another Project")


def grant_access(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    granted_by: str,
    reason: str | None = None,
    valid_until: Any = None,
) -> dict[str, Any]:
    principal = _principal_row(conn, principal_ref)
    if principal["disabled_at"] is not None:
        raise PrincipalDisabled(f"human principal is disabled: {principal_ref}")
    project_id = _required(project_id, "project_id")
    resource_type = _required(resource_type, "resource_type")
    resource_id = _required(resource_id, "resource_id")
    action = _required(action, "action")
    granted_by = _required(granted_by, "granted_by")
    reason = _optional(reason)
    _validate_grant_target(
        conn,
        project_id=project_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
    )

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT * FROM human_resource_grants g
                 WHERE g.principal_ref = %s
                   AND g.project_id = %s
                   AND g.resource_type = %s
                   AND g.resource_id = %s
                   AND g.action = %s
                   AND {_active_window_sql('g')}
                """,
                (principal_ref, project_id, resource_type, resource_id, action),
            )
            existing = cur.fetchone()
        if existing is not None:
            return dict(existing)

        grant_id = f"human-grant-{uuid.uuid4().hex}"
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO human_resource_grants (
                    grant_id, principal_ref, project_id, resource_type, resource_id,
                    action, valid_until, granted_by, reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    grant_id,
                    principal_ref,
                    project_id,
                    resource_type,
                    resource_id,
                    action,
                    valid_until,
                    granted_by,
                    reason,
                ),
            )
            return dict(cur.fetchone())


def get_grant(conn: psycopg.Connection, grant_id: str) -> dict[str, Any]:
    grant_id = _required(grant_id, "grant_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM human_resource_grants WHERE grant_id = %s", (grant_id,))
        row = cur.fetchone()
    if row is None:
        raise GrantConflict(f"unknown human resource grant: {grant_id}")
    return dict(row)


def list_project_grants(
    conn: psycopg.Connection,
    *,
    project_id: str,
    include_inactive: bool = True,
) -> list[dict[str, Any]]:
    project_id = _required(project_id, "project_id")
    agency_data.get_project(conn, project_id)
    where = "g.project_id = %s"
    if not include_inactive:
        where += f" AND {_active_window_sql('g')}"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT g.*,
                   p.disabled_at AS principal_disabled_at
              FROM human_resource_grants g
              JOIN human_principals p ON p.principal_ref = g.principal_ref
             WHERE {where}
             ORDER BY g.principal_ref, g.resource_type, g.resource_id,
                      g.action, g.valid_from, g.grant_id
            """,
            (project_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def revoke_grant(conn: psycopg.Connection, *, grant_id: str) -> dict[str, Any]:
    grant_id = _required(grant_id, "grant_id")
    with conn.transaction():
        row = get_grant(conn, grant_id)
        if (
            row["revoked_at"] is None
            and row["resource_type"] == "project"
            and row["resource_id"] == row["project_id"]
            and row["action"] == "project.read"
            and has_access(
                conn,
                principal_ref=row["principal_ref"],
                project_id=row["project_id"],
                resource_type="project",
                resource_id=row["project_id"],
                action="project.access.manage",
            )
        ):
            raise HumanAccessError(
                "cannot revoke project.read while principal holds active project.access.manage"
            )
        if row["revoked_at"] is None:
            conn.execute(
                "UPDATE human_resource_grants SET revoked_at = clock_timestamp() WHERE grant_id = %s",
                (grant_id,),
            )
        return get_grant(conn, grant_id)


def resolve_principal_context(
    conn: psycopg.Connection,
    claims: Mapping[str, Any],
) -> PrincipalContext:
    issuer = _required(claims.get("iss"), "OIDC issuer")
    subject = _required(claims.get("sub"), "OIDC subject")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT b.principal_ref, p.disabled_at
              FROM human_oidc_bindings b
              JOIN human_principals p ON p.principal_ref = b.principal_ref
             WHERE b.issuer = %s
               AND b.subject = %s
               AND {_active_window_sql('b')}
            """,
            (issuer, subject),
        )
        row = cur.fetchone()
    if row is None:
        raise PrincipalNotBound("authenticated OIDC identity is not bound to a local human principal")
    if row["disabled_at"] is not None:
        raise PrincipalDisabled(f"human principal is disabled: {row['principal_ref']}")
    display_name = _optional(claims.get("name")) or _optional(claims.get("preferred_username"))
    return PrincipalContext(
        principal_ref=row["principal_ref"],
        issuer=issuer,
        subject=subject,
        display_name=display_name,
        email=_optional(claims.get("email")),
        issued_at=claims.get("iat"),
        expires_at=claims.get("exp"),
        auth_time=claims.get("auth_time"),
    )


def has_access(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
) -> bool:
    principal = _principal_row(conn, principal_ref)
    if principal["disabled_at"] is not None:
        return False
    if action not in ACTIONS or resource_type not in RESOURCE_TYPES:
        return False
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT 1
              FROM human_resource_grants g
             WHERE g.principal_ref = %s
               AND g.project_id = %s
               AND g.resource_type = %s
               AND g.resource_id = %s
               AND g.action = %s
               AND {_active_window_sql('g')}
             LIMIT 1
            """,
            (principal_ref, project_id, resource_type, resource_id, action),
        )
        return cur.fetchone() is not None


def require_access(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
) -> None:
    if not has_access(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
    ):
        raise AccessDenied(
            f"principal {principal_ref} is not granted {action} on {resource_type}:{resource_id} in project {project_id}"
        )


def list_accessible_projects(conn: psycopg.Connection, principal_ref: str) -> list[dict[str, Any]]:
    principal = _principal_row(conn, principal_ref)
    if principal["disabled_at"] is not None:
        return []
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT DISTINCT g.project_id
              FROM human_resource_grants g
             WHERE g.principal_ref = %s
               AND g.resource_type = 'project'
               AND g.resource_id = g.project_id
               AND g.action = 'project.read'
               AND {_active_window_sql('g')}
             ORDER BY g.project_id
            """,
            (principal_ref,),
        )
        project_ids = [row[0] for row in cur.fetchall()]
    projects = [agency_data.get_project(conn, project_id) for project_id in project_ids]
    return sorted(projects, key=lambda item: (str(item["display_name"]).casefold(), item["project_id"]))


def list_accessible_documents(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
) -> list[dict[str, Any]]:
    require_access(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
        resource_type="project",
        resource_id=project_id,
        action="project.read",
    )
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT DISTINCT g.resource_id
              FROM human_resource_grants g
             WHERE g.principal_ref = %s
               AND g.project_id = %s
               AND g.resource_type = 'project_document'
               AND g.action = 'document.read'
               AND {_active_window_sql('g')}
             ORDER BY g.resource_id
            """,
            (principal_ref, project_id),
        )
        document_ids = [row[0] for row in cur.fetchall()]
    documents: list[dict[str, Any]] = []
    for document_id in document_ids:
        document = project_documents.get_document(conn, document_id)
        if document["parent_project_id"] == project_id:
            documents.append(document)
    return sorted(documents, key=lambda item: (str(item["title"]).casefold(), item["document_id"]))


AUTHORITY = {
    "technical_access_only": True,
    "is_professional_role": False,
    "is_approval": False,
    "is_decision_authority": False,
    "is_evidence": False,
    "changes_project_truth": False,
}
