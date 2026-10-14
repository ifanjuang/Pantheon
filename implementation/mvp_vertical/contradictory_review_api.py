"""Bounded API installer for contradictory review candidates.

The write surface accepts only Hermes-authenticated candidate reports. Reading a
stored report does not approve it, validate Evidence or close the rite.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from . import contradictory_review_store


class ContradictoryReviewSubmission(BaseModel):
    report: dict[str, Any]


class ContradictoryReviewProjection(BaseModel):
    review_id: str
    project_id: str
    task_contract_ref: str
    candidate_id: str
    candidate_digest: str
    execution_id: str
    review_status: str
    report: dict[str, Any]
    submitted_by: str


def _projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_id": row["review_id"],
        "project_id": row["project_id"],
        "task_contract_ref": row["task_contract_ref"],
        "candidate_id": row["candidate_id"],
        "candidate_digest": row["candidate_digest"],
        "execution_id": row["execution_id"],
        "review_status": row["review_status"],
        "report": row["report"],
        "submitted_by": row["submitted_by"],
        "submitted_at": row.get("submitted_at"),
        "authority": {
            "is_evidence": False,
            "is_approval": False,
            "is_zeus_closure": False,
            "is_task_authorization": False,
        },
    }


def install_contradictory_review_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_hermes_key: Callable,
    persist_fn: Callable = contradictory_review_store.persist_candidate,
    get_fn: Callable = contradictory_review_store.get_candidate,
    list_fn: Callable = contradictory_review_store.list_project_candidates,
) -> None:
    """Install stable append-only candidate routes without execution behavior."""

    def require_hermes_actor(
        x_pantheon_actor: str | None = Header(default=None, alias="X-Pantheon-Actor"),
    ) -> str:
        actor = str(x_pantheon_actor or "").strip()
        if not actor:
            raise HTTPException(
                status_code=422,
                detail="X-Pantheon-Actor is required for Hermes candidate submission",
            )
        return actor

    @app.post(
        "/projects/{project_id}/contradictory-reviews",
        status_code=201,
    )
    def submit_contradictory_review(
        project_id: str,
        body: ContradictoryReviewSubmission,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict[str, Any]:
        try:
            row = with_connection(
                lambda conn: persist_fn(
                    conn,
                    project_id=project_id,
                    submitted_by=actor,
                    report_payload=body.report,
                )
            )
        except contradictory_review_store.ContradictoryReviewConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except contradictory_review_store.ContradictoryReviewStoreError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _projection(row)

    @app.get("/projects/{project_id}/contradictory-reviews")
    def list_contradictory_reviews(
        project_id: str,
        limit: int = Query(default=100, ge=1, le=200),
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        try:
            rows = with_connection(
                lambda conn: list_fn(conn, project_id, limit=limit)
            )
        except contradictory_review_store.ContradictoryReviewStoreError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "project_id": project_id,
            "reviews": [_projection(row) for row in rows],
            "authority": "candidate_projection_only",
        }

    @app.get("/contradictory-reviews/{review_id}")
    def get_contradictory_review(
        review_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        try:
            row = with_connection(lambda conn: get_fn(conn, review_id))
        except contradictory_review_store.ContradictoryReviewNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except contradictory_review_store.ContradictoryReviewStoreError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _projection(row)
