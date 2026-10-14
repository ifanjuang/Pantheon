"""Bounded cross-family references to stable APU object identities.

This module reuses the existing DecisionRequest scope contract, WorkIssue scope
links and ProjectClaim backing_ref. It does not create a universal relation graph
or move business authority into APU.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import psycopg
from psycopg.rows import dict_row

from . import agency_claims, decision_requests


MIGRATION = Path(__file__).resolve().parent / "sql" / "023_apu_cross_family_links.sql"
SCOPE_ENTITY_TYPE = "apu_object"
_GOVERNED_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class ApuCrossFamilyError(decision_requests.DecisionRequestError):
    pass


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ApuCrossFamilyError(f"{field} is required")
    return text


def _normalize_scope_refs(
    scope_refs: Iterable[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in scope_refs or []:
        if not isinstance(raw, dict):
            raise ApuCrossFamilyError("Decision Request scope_refs must contain objects")
        unknown = set(raw) - {"entity_type", "entity_id"}
        if unknown:
            raise ApuCrossFamilyError(
                "unsupported Decision Request scope field(s): " + ", ".join(sorted(unknown))
            )
        entity_type = _required(raw.get("entity_type"), "scope_ref.entity_type")
        entity_id = _required(raw.get("entity_id"), "scope_ref.entity_id")
        if entity_type != SCOPE_ENTITY_TYPE:
            raise ApuCrossFamilyError("Decision Request scopes admit only apu_object")
        if not _GOVERNED_ID.fullmatch(entity_id):
            raise ApuCrossFamilyError("scope_ref.entity_id must be a governed id")
        key = (entity_type, entity_id)
        if key in seen:
            raise ApuCrossFamilyError("Decision Request scope_refs must be unique")
        seen.add(key)
        normalized.append({"entity_type": entity_type, "entity_id": entity_id})
    return normalized


def list_decision_scope_refs(conn: psycopg.Connection, request_id: str) -> list[dict[str, str]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT entity_type, entity_id
              FROM agency_decision_request_scope_refs
             WHERE request_id = %s
             ORDER BY ordinal, entity_id
            """,
            (request_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _request_exists(conn: psycopg.Connection, request_id: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM agency_decision_requests WHERE request_id = %s",
            (request_id,),
        ).fetchone()
        is not None
    )


def _store_decision_scope_refs(
    conn: psycopg.Connection,
    *,
    request_id: str,
    scope_refs: list[dict[str, str]],
    created_by: str,
) -> None:
    for ordinal, scope in enumerate(scope_refs):
        conn.execute(
            """
            INSERT INTO agency_decision_request_scope_refs (
                request_id, entity_type, entity_id, ordinal, created_by
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                request_id,
                scope["entity_type"],
                scope["entity_id"],
                ordinal,
                created_by,
            ),
        )


def enrich_request_projection(
    conn: psycopg.Connection,
    projection: dict[str, Any],
) -> dict[str, Any]:
    output = dict(projection)
    request = dict(output["decision_request"])
    request["scope_refs"] = list_decision_scope_refs(conn, request["request_id"])
    try:
        decision_requests._request_validator().validate(request)
    except Exception as exc:
        raise ApuCrossFamilyError(
            f"stored APU-scoped Decision Request violates its governed contract: {exc}"
        ) from exc
    output["decision_request"] = request
    return output


def create_decision_request(
    conn: psycopg.Connection,
    *,
    scope_refs: Iterable[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    normalized = _normalize_scope_refs(scope_refs)
    request_id = _required(kwargs.get("request_id"), "request_id")
    project_ref = str(kwargs.get("project_ref") or "").strip() or None
    created_by = _required(kwargs.get("created_by"), "created_by")
    if normalized and project_ref is None:
        raise ApuCrossFamilyError("APU-scoped Decision Request requires project_ref")

    with conn.transaction():
        preexisting = _request_exists(conn, request_id)
        projection = decision_requests.create_request(conn, **kwargs)
        existing = list_decision_scope_refs(conn, request_id)
        if preexisting:
            if existing != normalized:
                raise decision_requests.DecisionRequestConflict(
                    "Decision Request scope_refs are immutable and differ from the replay"
                )
            return enrich_request_projection(conn, projection)

        if normalized:
            try:
                _store_decision_scope_refs(
                    conn,
                    request_id=request_id,
                    scope_refs=normalized,
                    created_by=created_by,
                )
            except (
                psycopg.errors.ForeignKeyViolation,
                psycopg.errors.UniqueViolation,
                psycopg.errors.RaiseException,
                psycopg.errors.CheckViolation,
            ) as exc:
                raise ApuCrossFamilyError(str(exc)) from exc
        return enrich_request_projection(conn, projection)


def get_request(conn: psycopg.Connection, request_id: str) -> dict[str, Any]:
    return enrich_request_projection(conn, decision_requests.get_request(conn, request_id))


def list_requests(
    conn: psycopg.Connection,
    *,
    status: str | None = None,
    project_ref: str | None = None,
    work_issue_ref: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return [
        enrich_request_projection(conn, item)
        for item in decision_requests.list_requests(
            conn,
            status=status,
            project_ref=project_ref,
            work_issue_ref=work_issue_ref,
            limit=limit,
        )
    ]


def get_decision(conn: psycopg.Connection, decision_id: str) -> dict[str, Any]:
    projection = decision_requests.get_decision(conn, decision_id)
    request_id = projection["decision_record"]["applies_to"]
    return projection | {
        "scope_refs": list_decision_scope_refs(conn, request_id),
        "scope_refs_are_request_owned": True,
    }


def list_decision_requests_for_apu_object(
    conn: psycopg.Connection,
    *,
    object_id: str,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 1000:
        raise ApuCrossFamilyError("Decision Request scope list limit must be between 1 and 1000")
    params: list[Any] = [object_id]
    filters = ["scope.entity_type = 'apu_object'", "scope.entity_id = %s"]
    if status is not None:
        filters.append("request.status = %s")
        params.append(status)
    params.append(limit)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT request.request_id
              FROM agency_decision_request_scope_refs scope
              JOIN agency_decision_requests request
                ON request.request_id = scope.request_id
             WHERE {' AND '.join(filters)}
             ORDER BY request.created_at DESC, request.request_id DESC
             LIMIT %s
            """,
            tuple(params),
        )
        request_ids = [row["request_id"] for row in cur.fetchall()]
    return [get_request(conn, request_id) for request_id in request_ids]


def list_project_claims_for_apu_object(
    conn: psycopg.Connection,
    *,
    object_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 1000:
        raise ApuCrossFamilyError("ProjectClaim backing list limit must be between 1 and 1000")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT claim_id
              FROM agency_project_claims
             WHERE backing_entity_type = 'apu_object'
               AND backing_entity_id = %s
             ORDER BY observed_at DESC, created_at DESC, claim_id DESC
             LIMIT %s
            """,
            (object_id, limit),
        )
        claim_ids = [row["claim_id"] for row in cur.fetchall()]
    return [agency_claims.get_claim(conn, claim_id) for claim_id in claim_ids]
