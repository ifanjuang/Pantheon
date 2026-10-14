"""Human-only structured review routes for Agency ChangeCandidates."""

from __future__ import annotations

from typing import Callable, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import agency_change_candidate_review, agency_change_candidates


class ChangeCandidateReviewAnnotationBody(BaseModel):
    annotation_type: Literal[
        "source_required",
        "question",
        "hypothesis",
        "contradiction",
        "needs_deeper_review",
    ]
    field: str | None = Field(default=None, max_length=200)
    message: str = Field(min_length=1, max_length=5_000)
    source_refs: list[str] = Field(default_factory=list, max_length=50)


class ChangeCandidateRevisionRequestBody(BaseModel):
    annotations: list[ChangeCandidateReviewAnnotationBody] = Field(min_length=1, max_length=50)
    note: str | None = Field(default=None, max_length=10_000)
    idempotency_key: str = Field(min_length=8, max_length=200)


def install_agency_change_candidate_review_routes(
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
        except agency_change_candidates.ChangeCandidateNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            agency_change_candidates.ChangeCandidateConflict,
            agency_change_candidates.ChangeCandidateIdempotencyConflict,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except agency_change_candidates.ChangeCandidateError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/agency/change-candidates/{candidate_id}")
    def get_change_candidate_review(
        candidate_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        review = operation(
            lambda conn: agency_change_candidate_review.get_project_candidate_review(
                conn,
                candidate_id=candidate_id,
            )
        )
        return {
            "system_of_record": "postgres",
            **review,
            "candidate_status_is_entity_status": False,
            "review_event_is_authorization": False,
        }

    @app.post("/agency/change-candidates/{candidate_id}/request-revision")
    def request_change_candidate_revision(
        candidate_id: str,
        body: ChangeCandidateRevisionRequestBody,
        _writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        review = operation(
            lambda conn: agency_change_candidate_review.request_project_candidate_revision(
                conn,
                candidate_id=candidate_id,
                actor=actor,
                annotations=[item.model_dump() for item in body.annotations],
                note=body.note,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "change_candidate_revision_requested",
            "project_mutated": False,
            "execution_authorized": False,
            "task_authorized": False,
            "evidence_admitted": False,
            "new_candidate_created": False,
            "human_follow_up_required": True,
            **review,
        }
