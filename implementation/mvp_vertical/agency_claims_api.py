"""FastAPI routes for semantic ProjectClaims.

Global Claim reads use the normal Agency Data read gate. Direct Claim creation is
human only and cannot cite an Execution Result; that path is owned by the reviewed
candidate transition in execution_result_api.

Read projections keep current, temporal and conflict semantics explicit:

    current projection != temporal reconstruction
    conflict candidate != resolved contradiction
    provenance != Evidence
    projection != persistence
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import agency_claims, project_claim_conflicts


class ClaimBackingRefBody(BaseModel):
    entity_type: str = Field(min_length=1, max_length=120)
    entity_id: str = Field(min_length=1, max_length=500)
    observed_status: str | None = Field(default=None, max_length=120)


class ProjectClaimCreateBody(BaseModel):
    claim_type: str = Field(min_length=1, max_length=120)
    value: Any
    source_kind: Literal[
        "information",
        "document",
        "human_assertion",
        "derived",
        "external_projection",
    ] = "human_assertion"
    backing_ref: ClaimBackingRefBody | None = None
    source_ref: str | None = Field(default=None, max_length=2000)
    derivation_note: str | None = Field(default=None, max_length=10_000)
    status: Literal["asserted", "source_backed", "verified", "contested", "retired"] = "asserted"
    certainty: Literal["E0", "E1", "E2", "E3", "E4"] = "E0"
    observed_at: datetime | None = None
    effective_at: datetime | None = None
    supersedes: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=10_000)


def install_agency_claim_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_global_agency_read: Callable,
    require_human_agency_writer: Callable,
    require_actor: Callable,
) -> None:
    def claim_operation(operation):
        try:
            return with_connection(operation)
        except agency_claims.ClaimNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except agency_claims.AgencyClaimError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def conflict_projection(project_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        try:
            candidates = with_connection(
                lambda conn: project_claim_conflicts.detect_project_claim_conflicts(
                    conn, project_id
                )
            )
        except project_claim_conflicts.ProjectClaimConflictError as exc:
            return [], {
                "status": "unavailable",
                "scope": "active_unsuperseded_scalar_claims",
                "reason": str(exc),
                "absence_of_candidates_inferred": False,
                "resolves_conflict": False,
            }
        return candidates, {
            "status": "available",
            "scope": "active_unsuperseded_scalar_claims",
            "candidate_count": len(candidates),
            "absence_of_candidates_inferred": True,
            "resolves_conflict": False,
        }

    @app.get("/agency/projects/{project_id}/claims")
    def list_project_claims(
        project_id: str,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        claims = claim_operation(lambda conn: agency_claims.list_project_claims(conn, project_id))
        projected_claims = claim_operation(
            lambda conn: agency_claims.active_project_claims(conn, project_id)
        )
        values, refs = claim_operation(
            lambda conn: agency_claims.project_claim_projection(conn, project_id)
        )
        conflict_candidates, conflict_status = conflict_projection(project_id)
        return {
            "system_of_record": "postgres",
            "project_id": project_id,
            "claims": claims,
            "projected_claims": projected_claims,
            "claim_values": values,
            "claim_refs": refs,
            "perspective": {
                "mode": "current",
                "business_time": None,
                "knowledge_time": None,
                "claim_scope": "active_unsuperseded",
            },
            "temporal_axes": {
                "observed_at": "observation_time",
                "effective_at": "explicit_business_effective_start",
                "knowledge_time": "postgres_recording_time_cutoff",
            },
            "conflict_candidates": conflict_candidates,
            "conflict_projection": conflict_status,
            "conflicts_resolved": False,
            "claim_is_visible_card_family": False,
            "authorization_inferred": False,
            "evidence_inferred": False,
        }

    @app.get("/agency/projects/{project_id}/claims/as-of")
    def list_project_claims_as_of(
        project_id: str,
        business_time: datetime | None = None,
        knowledge_time: datetime | None = None,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        if business_time is None and knowledge_time is None:
            raise HTTPException(
                status_code=422,
                detail="business_time or knowledge_time is required for an as-of ProjectClaim read",
            )

        if business_time is not None:
            projected_claims = claim_operation(
                lambda conn: agency_claims.applicable_project_claims_as_of(
                    conn,
                    project_id,
                    business_time,
                    knowledge_time=knowledge_time,
                )
            )
            mode = (
                "business_and_knowledge_as_of"
                if knowledge_time is not None
                else "business_as_of_current_knowledge"
            )
        else:
            projected_claims = claim_operation(
                lambda conn: agency_claims.project_claims_known_as_of(
                    conn,
                    project_id,
                    knowledge_time,
                )
            )
            mode = "knowledge_as_of"

        return {
            "system_of_record": "postgres",
            "project_id": project_id,
            "claims": projected_claims,
            "perspective": {
                "mode": mode,
                "business_time": business_time.isoformat() if business_time is not None else None,
                "knowledge_time": knowledge_time.isoformat() if knowledge_time is not None else None,
                "claim_scope": "unsuperseded_non_retired_within_requested_cutoffs",
            },
            "temporal_axes": {
                "observed_at": "observation_time",
                "effective_at": "explicit_business_effective_start",
                "knowledge_time": "postgres_recording_time_cutoff",
            },
            "conflict_candidates": [],
            "conflict_projection": {
                "status": "not_evaluated",
                "scope": "temporal_perspective",
                "reason": (
                    "P3 conflict-candidate contract is bounded to current active unsuperseded scalar Claims"
                ),
                "absence_of_candidates_inferred": False,
                "resolves_conflict": False,
            },
            "conflicts_resolved": False,
            "claim_is_visible_card_family": False,
            "authorization_inferred": False,
            "evidence_inferred": False,
        }

    @app.post("/agency/projects/{project_id}/claims", status_code=201)
    def create_project_claim(
        project_id: str,
        body: ProjectClaimCreateBody,
        _writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        values = body.model_dump(exclude_none=True)
        if body.backing_ref is not None:
            values["backing_ref"] = body.backing_ref.model_dump(exclude_none=True)
        claim = claim_operation(
            lambda conn: agency_claims.record_claim(
                conn,
                project_id=project_id,
                actor=actor,
                **values,
            )
        )
        return {
            "system_of_record": "postgres",
            "claim": claim,
            "project_mutated": False,
            "evidence_admitted": False,
            "approval_inferred": False,
        }
