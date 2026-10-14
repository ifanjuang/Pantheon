"""Human review API for Project attribute ChangeCandidates.

This surface creates, lists, applies or rejects proposal envelopes. It grants no
Hermes mutation authority and never treats candidate status as Project status.

The installer also composes the sibling ProjectClaim HTTP surface because both
use the exact same global Agency read / human writer dependencies. Their domain
models remain separate: ChangeCandidate proposes Project attribute mutation;
ProjectClaim records source-qualified semantic values.
"""

from __future__ import annotations

from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import agency_change_candidate_review, agency_change_candidates, agency_data
from .agency_change_candidate_review_api import install_agency_change_candidate_review_routes
from .agency_claims_api import install_agency_claim_routes


class ProjectChangeCandidateCreateBody(BaseModel):
    base_revision: int = Field(ge=1)
    proposed_attributes: dict[str, Any] = Field(min_length=1)
    reason: str | None = Field(default=None, max_length=10_000)
    source_refs: list[str] = Field(default_factory=list, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=200)


class ProjectChangeCandidateApplyBody(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)


class ProjectChangeCandidateRejectBody(BaseModel):
    reason: str = Field(min_length=1, max_length=10_000)
    idempotency_key: str = Field(min_length=8, max_length=200)


def install_agency_change_candidate_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_human_writer: Callable,
    require_actor: Callable,
) -> None:
    def operation(call):
        try:
            return with_connection(call)
        except agency_data.ProjectNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except agency_change_candidates.ChangeCandidateNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            agency_change_candidates.ChangeCandidateConflict,
            agency_change_candidates.ChangeCandidateIdempotencyConflict,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (
            agency_change_candidates.ChangeCandidateError,
            agency_data.AgencyDataError,
        ) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/agency/projects/{project_id}/change-candidates")
    def list_change_candidates(
        project_id: str,
        status: Literal[
            "pending_review",
            "revision_requested",
            "applied",
            "rejected",
            "stale",
        ] | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        if status == "revision_requested":
            candidates = operation(
                lambda conn: agency_change_candidate_review.list_revision_requested_project_candidates(
                    conn,
                    project_id=project_id,
                    limit=limit,
                )
            )
        else:
            candidates = operation(
                lambda conn: agency_change_candidates.list_project_candidates(
                    conn,
                    project_id,
                    status=status,
                    limit=limit,
                )
            )
        return {
            "system_of_record": "postgres",
            "entity_type": "project",
            "entity_id": project_id,
            "change_candidates": candidates,
            "candidate_status_is_entity_status": False,
        }

    @app.post("/agency/projects/{project_id}/change-candidates", status_code=201)
    def create_change_candidate(
        project_id: str,
        body: ProjectChangeCandidateCreateBody,
        _writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        candidate = operation(
            lambda conn: agency_change_candidates.create_project_candidate(
                conn,
                project_id=project_id,
                base_revision=body.base_revision,
                proposed_attributes=body.proposed_attributes,
                proposer=actor,
                proposer_kind="human",
                idempotency_key=body.idempotency_key,
                reason=body.reason,
                source_refs=body.source_refs,
            )
        )
        return {
            "effect": "change_candidate_created",
            "execution_authorized": False,
            "approval_inferred": False,
            "change_candidate": candidate,
        }

    @app.post("/agency/change-candidates/{candidate_id}/apply")
    def apply_change_candidate(
        candidate_id: str,
        body: ProjectChangeCandidateApplyBody,
        _writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        candidate = operation(
            lambda conn: agency_change_candidates.apply_project_candidate(
                conn,
                candidate_id=candidate_id,
                actor=actor,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "project_attribute_change_applied" if candidate["status"] == "applied" else "change_candidate_stale",
            "approval_inferred": False,
            "applied": candidate["status"] == "applied",
            "change_candidate": candidate,
        }

    @app.post("/agency/change-candidates/{candidate_id}/reject")
    def reject_change_candidate(
        candidate_id: str,
        body: ProjectChangeCandidateRejectBody,
        _writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        candidate = operation(
            lambda conn: agency_change_candidates.reject_project_candidate(
                conn,
                candidate_id=candidate_id,
                actor=actor,
                reason=body.reason,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "change_candidate_rejected",
            "approval_inferred": False,
            "applied": False,
            "change_candidate": candidate,
        }

    install_agency_change_candidate_review_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_human_writer=require_human_writer,
        require_actor=require_actor,
    )

    # Sibling semantic surface: same read/human writer gates, separate domain.
    install_agency_claim_routes(
        app,
        with_connection=with_connection,
        require_global_agency_read=require_read_key,
        require_human_agency_writer=require_human_writer,
        require_actor=require_actor,
    )
