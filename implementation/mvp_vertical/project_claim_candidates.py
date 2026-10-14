"""Human-governed creation of a ProjectClaim from one reviewed result candidate.

The source Execution Result remains immutable. This adapter verifies one exact typed
candidate and its latest human disposition, then creates a separate append-only
ProjectClaim with exact provenance.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row

from . import agency_claims, agency_schema, pantheon_contracts


SCHEMA = pantheon_contracts.schema_path("project_claim_candidate")
ADMITTED_BACKING_TYPES = {"project", "information", "apu_object"}


class ProjectClaimCandidateError(ValueError):
    pass


class ProjectClaimCandidateNotFound(ProjectClaimCandidateError):
    pass


class ProjectClaimCandidateConflict(ProjectClaimCandidateError):
    pass


@lru_cache(maxsize=1)
def _validator() -> jsonschema.Draft202012Validator:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def _validate_candidate(payload: dict[str, Any]) -> None:
    try:
        _validator().validate(payload)
    except jsonschema.ValidationError as exc:
        raise ProjectClaimCandidateError(
            f"project claim candidate violates its governed contract: {exc.message}"
        ) from exc


def _claim_id(execution_id: str, result_id: str) -> str:
    digest = hashlib.sha256(f"{execution_id}\0{result_id}".encode()).hexdigest()[:24]
    return f"claim.execution.{digest}"


def _load_candidate(
    conn: psycopg.Connection,
    *,
    execution_id: str,
    result_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT e.execution_result_id, e.project_ref,
                   i.result_id, i.result_kind, i.schema_ref, i.payload
              FROM execution_results e
              JOIN execution_result_items i
                ON i.execution_result_id = e.execution_result_id
             WHERE e.execution_result_id = %s
               AND i.result_id = %s
            """,
            (execution_id, result_id),
        )
        row = cur.fetchone()
        if row is None:
            raise ProjectClaimCandidateNotFound(
                "unknown ProjectClaim candidate for this execution result"
            )
        if row["result_kind"] != "project_claim_candidate":
            raise ProjectClaimCandidateError(
                f"result is {row['result_kind']}, not project_claim_candidate"
            )
        if row["schema_ref"] != "schemas/project_claim_candidate.schema.yaml":
            raise ProjectClaimCandidateError("ProjectClaim candidate schema_ref is not governed")
        payload = dict(row["payload"])
        _validate_candidate(payload)

        cur.execute(
            """
            SELECT disposition_id, disposition, reviewer, reviewer_kind, occurred_at
              FROM execution_result_review_dispositions
             WHERE result_ref = %s
             ORDER BY occurred_at DESC, disposition_id DESC
             LIMIT 1
            """,
            (result_id,),
        )
        disposition = cur.fetchone()
    if disposition is None:
        raise ProjectClaimCandidateError("ProjectClaim candidate has not been reviewed")
    if disposition["reviewer_kind"] != "human":
        raise ProjectClaimCandidateError("ProjectClaim candidate review must be human")
    if disposition["disposition"] != "accepted_for_claim":
        raise ProjectClaimCandidateError(
            "latest ProjectClaim candidate disposition is not accepted_for_claim"
        )
    return dict(row), dict(disposition)


def _validate_candidate_unit(payload: dict[str, Any]) -> None:
    field = agency_schema.project_claim_fields().get(payload["claim_type"])
    if field is None:
        raise ProjectClaimCandidateError(
            f"undeclared Project claim type: {payload['claim_type']}"
        )
    expected_unit = field.get("unit") or None
    proposed_unit = payload.get("unit") or None
    if proposed_unit != expected_unit:
        raise ProjectClaimCandidateError(
            f"candidate unit {proposed_unit!r} does not match governed unit {expected_unit!r}"
        )


def _backing_project(
    conn: psycopg.Connection,
    *,
    entity_type: str,
    entity_id: str,
) -> str | None:
    if entity_type == "project":
        row = conn.execute(
            "SELECT project_id FROM agency_projects WHERE project_id = %s",
            (entity_id,),
        ).fetchone()
    elif entity_type == "information":
        row = conn.execute(
            "SELECT project_id FROM agency_information_cards WHERE information_id = %s",
            (entity_id,),
        ).fetchone()
    elif entity_type == "apu_object":
        row = conn.execute(
            "SELECT project_id FROM agency_apu_objects WHERE object_id = %s",
            (entity_id,),
        ).fetchone()
    else:  # guarded by ADMITTED_BACKING_TYPES
        row = None
    if row is None:
        raise ProjectClaimCandidateError(
            f"unknown {entity_type} backing_ref: {entity_id}"
        )
    return str(row[0])


def _select_backing_ref(
    conn: psycopg.Connection,
    *,
    payload: dict[str, Any],
    requested: dict[str, Any] | None,
    project_id: str,
) -> dict[str, Any] | None:
    if requested is None:
        return None
    entity_type = str(requested.get("entity_type") or "").strip()
    entity_id = str(requested.get("entity_id") or "").strip()
    if not entity_type or not entity_id:
        raise ProjectClaimCandidateError("backing_ref requires entity_type and entity_id")
    if entity_type not in ADMITTED_BACKING_TYPES:
        raise ProjectClaimCandidateError(
            "candidate-backed Claim admits only project, information or apu_object backing"
        )

    selected: dict[str, Any] | None = None
    for basis in payload["basis_refs"]:
        if basis["entity_type"] == entity_type and basis["entity_id"] == entity_id:
            selected = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "observed_status": basis.get("observed_status"),
            }
            break
    if selected is None:
        raise ProjectClaimCandidateError("backing_ref must be one of the candidate basis_refs")

    if _backing_project(conn, entity_type=entity_type, entity_id=entity_id) != project_id:
        raise ProjectClaimCandidateError("backing_ref does not belong to the candidate Project")
    return selected


def create_claim_from_candidate(
    conn: psycopg.Connection,
    *,
    execution_id: str,
    result_id: str,
    actor: str,
    status: str,
    certainty: str | None = None,
    backing_ref: dict[str, Any] | None = None,
    supersedes: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    execution_id = str(execution_id or "").strip()
    result_id = str(result_id or "").strip()
    actor = str(actor or "").strip()
    if not execution_id or not result_id or not actor:
        raise ProjectClaimCandidateError("execution_id, result_id and actor are required")

    with conn.transaction():
        # Serialize Claim creation for one immutable candidate. The replay lookup
        # is a second statement after the lock, so READ COMMITTED takes a fresh
        # snapshot and sees a Claim committed while this transaction was waiting.
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT result_id
                  FROM execution_result_items
                 WHERE execution_result_id = %s
                   AND result_id = %s
                 FOR UPDATE
                """,
                (execution_id, result_id),
            )
            locked = cur.fetchone()
            if locked is None:
                raise ProjectClaimCandidateNotFound(
                    "unknown ProjectClaim candidate for this execution result"
                )
            cur.execute(
                """
                SELECT claim_id
                  FROM agency_project_claims
                 WHERE candidate_execution_id = %s
                   AND candidate_result_id = %s
                """,
                (execution_id, result_id),
            )
            existing = cur.fetchone()
        if existing is not None:
            return agency_claims.get_claim(conn, existing["claim_id"])

        item, disposition = _load_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
        )
        payload = dict(item["payload"])
        project_id = str(item.get("project_ref") or "").strip()
        if not project_id or project_id != payload["project_ref"]:
            raise ProjectClaimCandidateError(
                "execution project_ref and candidate project_ref must match"
            )
        _validate_candidate_unit(payload)

        selected_backing = _select_backing_ref(
            conn,
            payload=payload,
            requested=backing_ref,
            project_id=project_id,
        )
        if status in {"source_backed", "verified"} and selected_backing is None:
            raise ProjectClaimCandidateError(f"{status} Claim requires a selected basis_ref")

        selected_certainty = str(certainty or payload["certainty"]).strip()
        selected_supersedes = supersedes or payload.get("supersedes_claim_ref")

        try:
            return agency_claims.record_claim(
                conn,
                claim_id=_claim_id(execution_id, result_id),
                project_id=project_id,
                claim_type=payload["claim_type"],
                value=payload["proposed_value"],
                actor=actor,
                source_kind="execution_result",
                backing_ref=selected_backing,
                candidate_ref={
                    "execution_id": execution_id,
                    "result_id": result_id,
                    "review_disposition_id": disposition["disposition_id"],
                },
                basis_refs=payload["basis_refs"],
                status=status,
                certainty=selected_certainty,
                observed_at=payload["observed_at"],
                effective_at=payload.get("effective_at"),
                supersedes=selected_supersedes,
                note=note,
            )
        except agency_claims.AgencyClaimError as exc:
            raise ProjectClaimCandidateError(str(exc)) from exc
