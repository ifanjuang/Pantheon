"""Bounded ProjectClaim conflict-candidate detection and persistence.

This module detects unresolved tensions between active scalar ProjectClaims. It
creates review candidates only. It never mutates a Claim, marks a Claim contested,
admits Evidence, creates a Decision, resolves a conflict or merges identity.

P3 deliberately exposes no public persistence entry point. Persisted candidates
store only the identities and detector result required to preserve the historical
tension. ProjectClaim value, time and provenance remain owned by the immutable
ProjectClaims and are reconstructed when a candidate is read.

`docs/governance/MISSING_INFORMATION_DISCIPLINE.md` (candidate) owns the policy
this module mechanizes for scalar Claims: a contradiction is preserved and
exposed, never averaged, merged or silently decided by source preference. That
document also states the boundary this module does not cross — geometric and
relational contradictions are outside `SCAN_SCOPE` and remain that document's
search/ask responsibility until a demonstrated need extends detection here.

    conflict detected != conflict resolved
    candidate != Decision
    provenance difference != authority
    temporal ambiguity != contradiction
    projection != persistence
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row

from . import agency_claims, agency_schema, pantheon_contracts

CONTRACT = "project_claim_conflict_candidate"
MIGRATION = Path(__file__).resolve().parent / "sql" / "037_project_claim_conflict_candidates.sql"
DETECTOR_ID = "project_claim_pairwise_conflict"
DETECTOR_VERSION = "1"
SCAN_SCOPE = "active_unsuperseded_scalar_claims"

LIMITATIONS = [
    "same project and claim_type does not prove identical professional scope",
    "effective_at is only an explicit start; no validity end is inferred",
    "detector output is a review candidate and does not select a winning Claim",
    # `SCAN_SCOPE` states this as configuration; it belongs here too, because this
    # list is what travels to a consumer. An empty candidate list otherwise reads
    # as "nothing contradicts" when it only means "no scalar value contradicts".
    "scalar Claim values only; geometric and relational contradictions are outside this detector",
]

AUTHORITY = {
    "is_evidence": False,
    "is_decision": False,
    "resolves_conflict": False,
    "mutates_project_claim": False,
    "authorizes_effect": False,
    "merges_identity": False,
}


class ProjectClaimConflictError(ValueError):
    """Base refusal for ProjectClaim conflict-candidate operations."""


class ProjectClaimConflictNotFound(ProjectClaimConflictError):
    pass


class ProjectClaimConflictCollision(ProjectClaimConflictError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _basis_marker(value: dict[str, Any]) -> str:
    return _canonical_json(value)


def _basis_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_refs = left.get("provenance", {}).get("basis_refs") or []
    right_refs = right.get("provenance", {}).get("basis_refs") or []
    if not left_refs and not right_refs:
        return "no_structured_basis"
    if not left_refs or not right_refs:
        return "partially_unknown"
    left_set = {_basis_marker(item) for item in left_refs}
    right_set = {_basis_marker(item) for item in right_refs}
    if left_set == right_set:
        return "same_structured_basis"
    if left_set & right_set:
        return "overlapping_structured_basis"
    return "disjoint_structured_basis"


def _backing_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_ref = left.get("backing_ref")
    right_ref = right.get("backing_ref")
    if left_ref is None and right_ref is None:
        return "none"
    if left_ref is None or right_ref is None:
        return "partially_unknown"
    return "same" if _canonical_json(left_ref) == _canonical_json(right_ref) else "different"


def _effective_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_value = left.get("effective_at")
    right_value = right.get("effective_at")
    if left_value is None and right_value is None:
        return "both_unknown"
    if left_value is None or right_value is None:
        return "partially_unknown"
    if left_value == right_value:
        return "same_explicit_start"
    return "different_explicit_start"


def _classification(effective_relation: str) -> str:
    if effective_relation == "same_explicit_start":
        return "value_conflict_same_effective_start"
    if effective_relation == "both_unknown":
        return "value_conflict_undated"
    return "temporal_ambiguity"


def _build_candidate(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    ordered = sorted((left, right), key=lambda item: item["claim_id"])
    left, right = ordered
    if left["claim_id"] == right["claim_id"]:
        raise ProjectClaimConflictError("conflict candidate requires two distinct Claims")
    if left["project_id"] != right["project_id"]:
        raise ProjectClaimConflictError("conflict candidate Claims must belong to the same Project")
    if left["claim_type"] != right["claim_type"]:
        raise ProjectClaimConflictError("conflict candidate Claims must have the same claim_type")
    if left.get("unit") != right.get("unit"):
        raise ProjectClaimConflictError(
            "same-type ProjectClaims carry different governed units; this is a Claim integrity violation, not a conflict candidate"
        )
    if left["value"] == right["value"]:
        raise ProjectClaimConflictError("Claims do not carry a detectable value tension")

    effective_relation = _effective_relation(left, right)
    identity = {
        "detector_id": DETECTOR_ID,
        "version": DETECTOR_VERSION,
        "project_id": left["project_id"],
        "claim_type": left["claim_type"],
        "claim_ids": [left["claim_id"], right["claim_id"]],
    }
    candidate = {
        "conflict_candidate_id": f"pcc-{_digest(identity)[:24]}",
        "project_id": left["project_id"],
        "claim_type": left["claim_type"],
        "claim_refs": [
            {"claim_id": left["claim_id"]},
            {"claim_id": right["claim_id"]},
        ],
        "classification": _classification(effective_relation),
        "comparison": {
            "effective_time_relation": effective_relation,
            "basis_relation": _basis_relation(left, right),
            "backing_relation": _backing_relation(left, right),
            "scope_relation": "same_project_same_claim_type_only",
        },
        "detector": {
            "detector_id": DETECTOR_ID,
            "version": DETECTOR_VERSION,
            "scan_scope": SCAN_SCOPE,
        },
        "limitations": list(LIMITATIONS),
        "authority": dict(AUTHORITY),
    }
    try:
        pantheon_contracts.validate(CONTRACT, candidate)
    except pantheon_contracts.ContractViolation as exc:
        raise ProjectClaimConflictError(str(exc)) from exc
    return candidate


def detect_project_claim_conflicts(conn, project_id: str) -> list[dict[str, Any]]:
    """Read active scalar Claims and return deterministic unresolved tension candidates."""
    project_id = str(project_id or "").strip()
    if not project_id:
        raise ProjectClaimConflictError("project_id is required")

    fields = agency_schema.project_claim_fields()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for claim in agency_claims.active_project_claims(conn, project_id):
        field = fields.get(claim["claim_type"])
        if field is None:
            raise ProjectClaimConflictError(
                f"undeclared Project claim type during conflict scan: {claim['claim_type']}"
            )
        if field.get("aggregation") == "list":
            continue
        grouped.setdefault(claim["claim_type"], []).append(claim)

    detected: list[dict[str, Any]] = []
    for claim_type in sorted(grouped):
        claims = sorted(grouped[claim_type], key=lambda item: item["claim_id"])
        for left, right in combinations(claims, 2):
            if left.get("unit") != right.get("unit"):
                raise ProjectClaimConflictError(
                    f"same-type ProjectClaims {left['claim_id']} and {right['claim_id']} carry different governed units"
                )
            if left["value"] == right["value"]:
                continue
            detected.append(_build_candidate(left, right))
    return sorted(detected, key=lambda item: item["conflict_candidate_id"])


def _row(conn, conflict_candidate_id: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_project_claim_conflict_candidates WHERE conflict_candidate_id = %s",
            (conflict_candidate_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else None


def _active_claims_by_id(conn, project_id: str) -> dict[str, dict[str, Any]]:
    return {
        claim["claim_id"]: claim
        for claim in agency_claims.active_project_claims(conn, project_id)
    }


def _candidate_from_row(conn, row: dict[str, Any]) -> dict[str, Any]:
    if row["detector_id"] != DETECTOR_ID or row["detector_version"] != DETECTOR_VERSION:
        raise ProjectClaimConflictError(
            "persisted ProjectClaim conflict candidate uses an unsupported detector version"
        )
    left = agency_claims.get_claim(conn, row["left_claim_id"])
    right = agency_claims.get_claim(conn, row["right_claim_id"])
    candidate = _build_candidate(left, right)
    if (
        candidate["conflict_candidate_id"] != row["conflict_candidate_id"]
        or candidate["project_id"] != row["project_id"]
        or candidate["claim_type"] != row["claim_type"]
        or candidate["classification"] != row["classification"]
    ):
        raise ProjectClaimConflictError(
            "persisted ProjectClaim conflict candidate does not match its immutable Claim inputs"
        )
    return candidate


def _record_view(conn, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "conflict_candidate_id": row["conflict_candidate_id"],
        "project_id": row["project_id"],
        "claim_type": row["claim_type"],
        "left_claim_id": row["left_claim_id"],
        "right_claim_id": row["right_claim_id"],
        "classification": row["classification"],
        "detector_id": row["detector_id"],
        "detector_version": row["detector_version"],
        "submitted_by": row["submitted_by"],
        "created_at": _jsonable(row["created_at"]),
        "candidate": _candidate_from_row(conn, row),
    }


def _persist_candidate(
    conn,
    *,
    candidate: dict[str, Any],
    submitted_by: str,
) -> dict[str, Any]:
    """Internal P3 persistence qualifier; no public mutation entry point is exposed."""
    submitted_by = str(submitted_by or "").strip()
    if not submitted_by:
        raise ProjectClaimConflictError("submitted_by is required")
    try:
        pantheon_contracts.validate(CONTRACT, candidate)
    except pantheon_contracts.ContractViolation as exc:
        raise ProjectClaimConflictError(str(exc)) from exc

    project_id = str(candidate.get("project_id") or "").strip()
    claim_refs = candidate.get("claim_refs") or []
    if len(claim_refs) != 2:
        raise ProjectClaimConflictError("conflict candidate requires exactly two claim_refs")
    claim_ids = [str(item.get("claim_id") or "").strip() for item in claim_refs]
    active = _active_claims_by_id(conn, project_id)
    if any(claim_id not in active for claim_id in claim_ids):
        raise ProjectClaimConflictError(
            "conflict candidate must bind two currently active unsuperseded ProjectClaims"
        )

    expected = _build_candidate(active[claim_ids[0]], active[claim_ids[1]])
    if _canonical_json(expected) != _canonical_json(candidate):
        raise ProjectClaimConflictError(
            "conflict candidate does not match the exact current detector result"
        )

    conflict_candidate_id = candidate["conflict_candidate_id"]
    existing = _row(conn, conflict_candidate_id)
    if existing is not None:
        expected_row = {
            "project_id": project_id,
            "claim_type": candidate["claim_type"],
            "left_claim_id": claim_ids[0],
            "right_claim_id": claim_ids[1],
            "classification": candidate["classification"],
            "detector_id": DETECTOR_ID,
            "detector_version": DETECTOR_VERSION,
        }
        if any(existing[key] != value for key, value in expected_row.items()):
            raise ProjectClaimConflictCollision(
                "conflict candidate id already exists with another Project, Claim pair or detector result"
            )
        return _record_view(conn, existing)

    with conn.transaction():
        conn.execute(
            """
            INSERT INTO agency_project_claim_conflict_candidates (
                conflict_candidate_id, project_id, claim_type,
                left_claim_id, right_claim_id, classification,
                detector_id, detector_version, submitted_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                conflict_candidate_id,
                project_id,
                candidate["claim_type"],
                claim_ids[0],
                claim_ids[1],
                candidate["classification"],
                DETECTOR_ID,
                DETECTOR_VERSION,
                submitted_by,
            ),
        )
    persisted = _row(conn, conflict_candidate_id)
    if persisted is None:
        raise ProjectClaimConflictError("conflict candidate was not persisted")
    return _record_view(conn, persisted)


def get_candidate(conn, conflict_candidate_id: str) -> dict[str, Any]:
    value = _row(conn, str(conflict_candidate_id or "").strip())
    if value is None:
        raise ProjectClaimConflictNotFound(
            f"unknown ProjectClaim conflict candidate: {conflict_candidate_id}"
        )
    return _record_view(conn, value)


def list_project_candidates(conn, project_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
    project_id = str(project_id or "").strip()
    if not project_id:
        raise ProjectClaimConflictError("project_id is required")
    if limit < 1 or limit > 500:
        raise ProjectClaimConflictError("limit must be between 1 and 500")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
              FROM agency_project_claim_conflict_candidates
             WHERE project_id = %s
             ORDER BY created_at DESC, conflict_candidate_id
             LIMIT %s
            """,
            (project_id, limit),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_record_view(conn, row) for row in rows]
