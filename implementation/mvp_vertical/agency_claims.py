"""Semantic ProjectClaim persistence for Agency Data.

A ProjectClaim is backend semantics, not a visible Cockpit family. It records a
governed project assertion while preserving its support and, when applicable, the
exact Execution Result candidate reviewed before the separate Claim was created.

    ProjectClaim != Execution Result
    ProjectClaim != Evidence
    ProjectClaim != approval
    source_backed != verified != opposable

Rows are append-only. A later Claim may supersede a prior Claim; the prior row is
never rewritten. Every emitted Claim is validated against the vendored Pantheon
Next governance schema.

Temporal reads keep three axes distinct:

    observed_at  = when the assertion/support was observed
    effective_at = explicit business-effective start, when one is asserted
    created_at   = PostgreSQL recording/system time

``created_at`` remains implementation metadata rather than a ProjectClaim field.
A missing ``effective_at`` is never replaced by ``observed_at`` or ``created_at``.
Supersession is lineage: an as-of view only lets a superseding Claim displace its
predecessor when that superseding Claim is itself inside the requested temporal
perspective.

Structured ``basis_refs`` preserve the governed references used to form an
assertion. They are provenance only: a basis reference is not Evidence admission,
verification, approval or project truth.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import agency_schema, pantheon_contracts

SCHEMA = pantheon_contracts.schema_path("project_claim")
MIGRATION = Path(__file__).resolve().parent / "sql" / "019_project_claim_candidates.sql"
PROVENANCE_MIGRATION = (
    Path(__file__).resolve().parent / "sql" / "036_project_claim_provenance_basis.sql"
)

GOVERNANCE_REFS = [
    "docs/domain-packs/architecture/PROJECT_CARD_DECK_COMPOSITION.md",
    "docs/governance/AGENCY_DATA_SYSTEM_OF_RECORD.md",
    "docs/governance/CARD_STACK_MODEL.md",
]
CLAIM_STATUSES = {"asserted", "source_backed", "verified", "contested", "retired"}
SOURCE_KINDS = {
    "information",
    "document",
    "human_assertion",
    "derived",
    "execution_result",
    "external_projection",
}
CERTAINTIES = {"E0", "E1", "E2", "E3", "E4"}


class AgencyClaimError(ValueError):
    pass


class ClaimNotFound(AgencyClaimError):
    pass


class ClaimContractViolation(AgencyClaimError):
    pass


@lru_cache(maxsize=1)
def _validator() -> jsonschema.Draft202012Validator:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def validate_claim(claim: dict[str, Any]) -> None:
    try:
        _validator().validate(claim)
    except jsonschema.ValidationError as exc:
        raise ClaimContractViolation(
            f"project claim violates its governed contract: {exc.message}"
        ) from exc


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _candidate_ref_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if not row.get("candidate_execution_id") or not row.get("candidate_result_id"):
        return None
    return {
        "execution_id": row["candidate_execution_id"],
        "result_id": row["candidate_result_id"],
        "review_disposition_id": row.get("candidate_review_disposition_id"),
    }


def _claim_from_row(row: dict[str, Any]) -> dict[str, Any]:
    backing_ref = None
    if row.get("backing_entity_type") and row.get("backing_entity_id"):
        backing_ref = {
            "entity_type": row["backing_entity_type"],
            "entity_id": row["backing_entity_id"],
            "observed_status": row.get("backing_observed_status"),
        }
    claim = {
        "claim_id": row["claim_id"],
        "project_id": row["project_id"],
        "claim_type": row["claim_type"],
        "value": row["value"],
        "unit": row.get("unit"),
        "backing_ref": backing_ref,
        "provenance": {
            "source_kind": row["source_kind"],
            "source_ref": row.get("source_ref"),
            "candidate_ref": _candidate_ref_from_row(row),
            "basis_refs": _jsonable(row.get("basis_refs") or []),
            "asserted_by": row.get("asserted_by"),
            "derivation_note": row.get("derivation_note"),
        },
        "status": row["status"],
        "certainty": row.get("certainty") or "E0",
        "observed_at": _jsonable(row["observed_at"]),
        "effective_at": _jsonable(row.get("effective_at")),
        "revision": row["revision"],
        "supersedes": row.get("supersedes"),
        "note": row.get("note"),
        "governance_refs": list(GOVERNANCE_REFS),
    }
    validate_claim(claim)
    return claim


def _declared_claim_field(claim_type: str) -> dict[str, Any]:
    fields = agency_schema.project_claim_fields()
    field = fields.get(str(claim_type or "").strip())
    if field is None:
        raise AgencyClaimError(f"undeclared Project claim type: {claim_type}")
    return field


def _normalize_claim_value(field: dict[str, Any], value: Any) -> Any:
    if field.get("aggregation") == "list":
        if not isinstance(value, str):
            raise AgencyClaimError(f"Project claim {field['claim_type']} requires one scalar string value")
        value = value.strip()
        if not value:
            raise AgencyClaimError(f"Project claim {field['claim_type']} may not be empty")
        return value
    try:
        return agency_schema.normalize_field_value("project", field, value)
    except agency_schema.AgencySchemaError as exc:
        raise AgencyClaimError(str(exc)) from exc


def _normalize_backing_ref(backing_ref: dict[str, Any] | None) -> dict[str, str | None] | None:
    if backing_ref is None:
        return None
    if not isinstance(backing_ref, dict):
        raise AgencyClaimError("backing_ref must be an object")
    unknown = set(backing_ref) - {"entity_type", "entity_id", "observed_status"}
    if unknown:
        raise AgencyClaimError(f"unsupported backing_ref field(s): {', '.join(sorted(unknown))}")
    entity_type = str(backing_ref.get("entity_type") or "").strip()
    entity_id = str(backing_ref.get("entity_id") or "").strip()
    if not entity_type or not entity_id:
        raise AgencyClaimError("backing_ref requires entity_type and entity_id")
    observed_status = backing_ref.get("observed_status")
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "observed_status": str(observed_status).strip() if observed_status is not None else None,
    }


def _normalize_candidate_ref(candidate_ref: dict[str, Any] | None) -> dict[str, str | None] | None:
    if candidate_ref is None:
        return None
    if not isinstance(candidate_ref, dict):
        raise AgencyClaimError("candidate_ref must be an object")
    unknown = set(candidate_ref) - {"execution_id", "result_id", "review_disposition_id"}
    if unknown:
        raise AgencyClaimError(f"unsupported candidate_ref field(s): {', '.join(sorted(unknown))}")
    execution_id = str(candidate_ref.get("execution_id") or "").strip()
    result_id = str(candidate_ref.get("result_id") or "").strip()
    if not execution_id or not result_id:
        raise AgencyClaimError("candidate_ref requires execution_id and result_id")
    disposition_id = candidate_ref.get("review_disposition_id")
    return {
        "execution_id": execution_id,
        "result_id": result_id,
        "review_disposition_id": str(disposition_id).strip() if disposition_id is not None else None,
    }


def _normalize_basis_refs(basis_refs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if basis_refs is None:
        return []
    if not isinstance(basis_refs, list):
        raise AgencyClaimError("basis_refs must be an array")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(basis_refs):
        if not isinstance(raw, dict):
            raise AgencyClaimError(f"basis_refs[{index}] must be an object")
        unknown = set(raw) - {
            "entity_type",
            "entity_id",
            "observed_revision",
            "observed_status",
        }
        if unknown:
            raise AgencyClaimError(
                f"unsupported basis_refs[{index}] field(s): {', '.join(sorted(unknown))}"
            )
        entity_type = str(raw.get("entity_type") or "").strip()
        entity_id = str(raw.get("entity_id") or "").strip()
        if not entity_type or not entity_id:
            raise AgencyClaimError(
                f"basis_refs[{index}] requires entity_type and entity_id"
            )
        observed_revision = raw.get("observed_revision")
        if observed_revision is not None and (
            isinstance(observed_revision, bool)
            or not isinstance(observed_revision, int)
            or observed_revision < 0
        ):
            raise AgencyClaimError(
                f"basis_refs[{index}].observed_revision must be a non-negative integer or null"
            )
        observed_status = raw.get("observed_status")
        item = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "observed_revision": observed_revision,
            "observed_status": (
                str(observed_status).strip() if observed_status is not None else None
            ),
        }
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if marker in seen:
            raise AgencyClaimError("basis_refs must contain unique references")
        seen.add(marker)
        normalized.append(item)
    return normalized


def _normalize_datetime(value: str | datetime | None, field: str, *, default_now: bool) -> str | None:
    if value is None:
        return datetime.now(timezone.utc).isoformat() if default_now else None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise AgencyClaimError(f"{field} must be an ISO datetime") from exc
    else:
        raise AgencyClaimError(f"{field} must be an ISO datetime")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _required_datetime(value: str | datetime | None, field: str) -> str:
    normalized = _normalize_datetime(value, field, default_now=False)
    if normalized is None:
        raise AgencyClaimError(f"{field} is required")
    return normalized


def _temporal_claim_rows(
    conn: psycopg.Connection,
    project_id: str,
    *,
    recorded_through: str | None = None,
    effective_through: str | None = None,
) -> list[dict[str, Any]]:
    project_id = str(project_id or "").strip()
    if not project_id:
        raise AgencyClaimError("project_id is required")

    conditions = ["project_id = %s"]
    params: list[Any] = [project_id]
    if recorded_through is not None:
        conditions.append("created_at <= %s")
        params.append(recorded_through)
    if effective_through is not None:
        conditions.extend(["effective_at IS NOT NULL", "effective_at <= %s"])
        params.append(effective_through)

    query = f"""
        SELECT *
          FROM agency_project_claims
         WHERE {' AND '.join(conditions)}
         ORDER BY observed_at DESC, created_at DESC, claim_id DESC
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, tuple(params))
        return [dict(row) for row in cur.fetchall()]


def _unsuperseded_claims(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims = [_claim_from_row(row) for row in rows]
    superseded = {claim["supersedes"] for claim in claims if claim.get("supersedes")}
    return [
        claim
        for claim in claims
        if claim["status"] != "retired" and claim["claim_id"] not in superseded
    ]


def record_claim(
    conn: psycopg.Connection,
    *,
    project_id: str,
    claim_type: str,
    value: Any,
    actor: str,
    source_kind: str = "human_assertion",
    backing_ref: dict[str, Any] | None = None,
    source_ref: str | None = None,
    candidate_ref: dict[str, Any] | None = None,
    basis_refs: list[dict[str, Any]] | None = None,
    derivation_note: str | None = None,
    status: str = "asserted",
    certainty: str = "E0",
    observed_at: str | datetime | None = None,
    effective_at: str | datetime | None = None,
    supersedes: str | None = None,
    note: str | None = None,
    claim_id: str | None = None,
) -> dict[str, Any]:
    """Append one governed Claim. This records an assertion; it approves nothing."""
    project_id = str(project_id or "").strip()
    actor = str(actor or "").strip()
    claim_type = str(claim_type or "").strip()
    certainty = str(certainty or "").strip()
    if not project_id or not actor or not claim_type:
        raise AgencyClaimError("project_id, claim_type and actor are required")
    if status not in CLAIM_STATUSES:
        raise AgencyClaimError(f"unknown claim status: {status}")
    if source_kind not in SOURCE_KINDS:
        raise AgencyClaimError(f"unknown claim source_kind: {source_kind}")
    if certainty not in CERTAINTIES:
        raise AgencyClaimError(f"unknown claim certainty: {certainty}")

    field = _declared_claim_field(claim_type)
    normalized_value = _normalize_claim_value(field, value)
    normalized_backing = _normalize_backing_ref(backing_ref)
    normalized_candidate = _normalize_candidate_ref(candidate_ref)
    normalized_basis_refs = _normalize_basis_refs(basis_refs)
    if status in {"source_backed", "verified"} and normalized_backing is None:
        raise AgencyClaimError(f"{status} Project claim requires backing_ref")
    if source_kind == "execution_result" and normalized_candidate is None:
        raise AgencyClaimError("execution_result Project claim requires candidate_ref")
    if source_kind == "execution_result" and not normalized_basis_refs:
        raise AgencyClaimError("execution_result Project claim requires basis_refs")
    if status == "verified" and (
        source_kind != "execution_result"
        or normalized_candidate is None
        or not normalized_candidate.get("review_disposition_id")
    ):
        raise AgencyClaimError(
            "verified Project claim requires a human-reviewed execution_result candidate"
        )
    if source_kind == "derived" and not str(derivation_note or "").strip():
        raise AgencyClaimError("derived Project claim requires derivation_note")
    expected_unit = field.get("unit")
    unit = expected_unit if expected_unit else None
    observed = _normalize_datetime(observed_at, "observed_at", default_now=True)
    effective = _normalize_datetime(effective_at, "effective_at", default_now=False)
    claim_id = str(claim_id or f"claim.{uuid.uuid4().hex}").strip().lower()

    if supersedes:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT project_id, claim_type FROM agency_project_claims WHERE claim_id = %s",
                (supersedes,),
            )
            prior = cur.fetchone()
        if prior is None:
            raise ClaimNotFound(f"unknown superseded Project claim: {supersedes}")
        if prior["project_id"] != project_id or prior["claim_type"] != claim_type:
            raise AgencyClaimError("supersedes must reference the same project and claim_type")

    candidate = {
        "claim_id": claim_id,
        "project_id": project_id,
        "claim_type": claim_type,
        "value": normalized_value,
        "unit": unit,
        "backing_ref": normalized_backing,
        "provenance": {
            "source_kind": source_kind,
            "source_ref": str(source_ref).strip() if source_ref is not None else None,
            "candidate_ref": normalized_candidate,
            "basis_refs": normalized_basis_refs,
            "asserted_by": actor,
            "derivation_note": str(derivation_note).strip() if derivation_note is not None else None,
        },
        "status": status,
        "certainty": certainty,
        "observed_at": observed,
        "effective_at": effective,
        "revision": 0,
        "supersedes": supersedes,
        "note": str(note).strip() if note is not None else None,
        "governance_refs": list(GOVERNANCE_REFS),
    }
    validate_claim(candidate)

    with conn.transaction():
        project = conn.execute(
            "SELECT project_id FROM agency_projects WHERE project_id = %s",
            (project_id,),
        ).fetchone()
        if project is None:
            raise AgencyClaimError(f"unknown Agency Project: {project_id}")
        conn.execute(
            """
            INSERT INTO agency_project_claims (
                claim_id, project_id, claim_type, value, unit,
                backing_entity_type, backing_entity_id, backing_observed_status,
                source_kind, source_ref, candidate_execution_id, candidate_result_id,
                candidate_review_disposition_id, basis_refs, asserted_by, derivation_note,
                status, certainty, observed_at, effective_at, revision, supersedes, note
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, 0, %s, %s
            )
            """,
            (
                claim_id,
                project_id,
                claim_type,
                Jsonb(normalized_value),
                unit,
                normalized_backing["entity_type"] if normalized_backing else None,
                normalized_backing["entity_id"] if normalized_backing else None,
                normalized_backing["observed_status"] if normalized_backing else None,
                source_kind,
                candidate["provenance"]["source_ref"],
                normalized_candidate["execution_id"] if normalized_candidate else None,
                normalized_candidate["result_id"] if normalized_candidate else None,
                normalized_candidate["review_disposition_id"] if normalized_candidate else None,
                Jsonb(normalized_basis_refs),
                actor,
                candidate["provenance"]["derivation_note"],
                status,
                certainty,
                observed,
                effective,
                supersedes,
                candidate["note"],
            ),
        )
    return get_claim(conn, claim_id)


def get_claim(conn: psycopg.Connection, claim_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM agency_project_claims WHERE claim_id = %s", (claim_id,))
        row = cur.fetchone()
    if row is None:
        raise ClaimNotFound(f"unknown Project claim: {claim_id}")
    return _claim_from_row(dict(row))


def list_project_claims(conn: psycopg.Connection, project_id: str, *, limit: int = 500) -> list[dict[str, Any]]:
    project_id = str(project_id or "").strip()
    if not project_id:
        raise AgencyClaimError("project_id is required")
    if limit < 1 or limit > 1000:
        raise AgencyClaimError("claim list limit must be between 1 and 1000")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM agency_project_claims
             WHERE project_id = %s
             ORDER BY observed_at DESC, created_at DESC, claim_id DESC
             LIMIT %s
            """,
            (project_id, limit),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_claim_from_row(row) for row in rows]


def active_project_claims(conn: psycopg.Connection, project_id: str) -> list[dict[str, Any]]:
    """Return unsuperseded, non-retired Claims in newest-first order."""
    claims = list_project_claims(conn, project_id)
    superseded = {claim["supersedes"] for claim in claims if claim.get("supersedes")}
    return [
        claim
        for claim in claims
        if claim["status"] != "retired" and claim["claim_id"] not in superseded
    ]


def project_claims_known_as_of(
    conn: psycopg.Connection,
    project_id: str,
    knowledge_time: str | datetime,
) -> list[dict[str, Any]]:
    """Reconstruct active Claim state using only rows recorded by ``knowledge_time``.

    PostgreSQL ``created_at`` is the system/recording axis for this read. A later
    correction, retirement or superseding Claim cannot rewrite what Pantheon could
    have known before that row was recorded.
    """
    recorded_through = _required_datetime(knowledge_time, "knowledge_time")
    rows = _temporal_claim_rows(
        conn,
        project_id,
        recorded_through=recorded_through,
    )
    return _unsuperseded_claims(rows)


def applicable_project_claims_as_of(
    conn: psycopg.Connection,
    project_id: str,
    business_time: str | datetime,
    *,
    knowledge_time: str | datetime | None = None,
) -> list[dict[str, Any]]:
    """Return Claims explicitly applicable at business time under one knowledge view.

    ``effective_at`` is the business/world-time axis. Claims without an explicit
    ``effective_at`` are excluded rather than coercing observation or recording
    time into applicability. When ``knowledge_time`` is supplied, only rows already
    recorded by that system time participate; omitting it gives the current
    retrospective view of the requested business time.

    Supersession is evaluated after both cutoffs, so a superseding Claim only closes
    its predecessor when the superseder itself was known (if bounded) and explicitly
    effective by the requested business time.
    """
    effective_through = _required_datetime(business_time, "business_time")
    recorded_through = (
        _required_datetime(knowledge_time, "knowledge_time")
        if knowledge_time is not None
        else None
    )
    rows = _temporal_claim_rows(
        conn,
        project_id,
        recorded_through=recorded_through,
        effective_through=effective_through,
    )
    return _unsuperseded_claims(rows)


def project_claim_projection(conn: psycopg.Connection, project_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return display values plus provenance refs for declared Project claim fields."""
    active = active_project_claims(conn, project_id)
    fields = agency_schema.project_claim_fields()
    by_type: dict[str, list[dict[str, Any]]] = {}
    for claim in active:
        if claim["claim_type"] in fields:
            by_type.setdefault(claim["claim_type"], []).append(claim)

    values: dict[str, Any] = {}
    refs: dict[str, Any] = {}
    for claim_type, field in fields.items():
        candidates = by_type.get(claim_type, [])
        if not candidates:
            continue
        if field.get("aggregation") == "list":
            seen: set[str] = set()
            projected_values: list[Any] = []
            projected_refs: list[dict[str, Any]] = []
            for claim in candidates:
                marker = json.dumps(claim["value"], sort_keys=True, ensure_ascii=False)
                if marker in seen:
                    continue
                seen.add(marker)
                projected_values.append(claim["value"])
                projected_refs.append(claim)
            values[claim_type] = projected_values
            refs[claim_type] = projected_refs
        else:
            values[claim_type] = candidates[0]["value"]
            refs[claim_type] = candidates[0]
    return values, refs


def enrich_project_with_claims(conn: psycopg.Connection, project: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(project)
    values, refs = project_claim_projection(conn, project["project_id"])
    enriched["claim_values"] = values
    enriched["claim_refs"] = refs
    return enriched
