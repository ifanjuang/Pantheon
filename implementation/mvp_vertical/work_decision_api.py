"""Human review endpoints over Work Issues already waiting for review.

This surface is part of the WorkIssue lifecycle. Accepting closes the issue as
answered; returning for rework moves it to ``in_progress``. It does not create a
Decision Request or Decision record and must not be presented as the Decisions
attention inbox.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import work_issue_read, work_issues


class WorkReviewBody(BaseModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


def install_work_decision_routes(
    app: FastAPI,
    *,
    require_editor_key: Callable,
    require_human_actor: Callable,
    with_connection: Callable,
) -> None:
    """Install Work review routes under stable responsibility-based paths.

    The installer name is retained inside the implementation module until its
    owning Cockpit composition is consolidated; no legacy HTTP alias is kept.
    """

    def review(operation):
        try:
            return with_connection(operation)
        except work_issues.IssueNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except work_issues.StaleWrite as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (work_issues.TransitionRefused, work_issues.WorkIssueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/work/issues/{issue_id}/review")
    def get_work_review(
        issue_id: str,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        issue = review(lambda conn: work_issue_read.get_issue_record(conn, issue_id))
        return {
            "work_issue": issue,
            "review_available": issue.get("status") == "review",
            "decision_request_created": False,
            "decision_recorded": False,
        }

    @app.post("/work/issues/{issue_id}/review/accept")
    def accept_work_review(
        issue_id: str,
        body: WorkReviewBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        projection = review(
            lambda conn: work_issues.close_issue(
                conn,
                issue_id=issue_id,
                decided_by=actor,
                close_reason="answered",
                expected_version=body.expected_version,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "work_review_accepted",
            "approval_inferred": False,
            "decision_request_created": False,
            "decision_recorded": False,
            "work_issue": projection,
        }

    @app.post("/work/issues/{issue_id}/review/return")
    def return_work_review_for_rework(
        issue_id: str,
        body: WorkReviewBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        projection = review(
            lambda conn: work_issues.transition_issue(
                conn,
                issue_id=issue_id,
                to_status="in_progress",
                actor=actor,
                actor_kind="human",
                expected_version=body.expected_version,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "work_review_returned_for_rework",
            "approval_inferred": False,
            "decision_request_created": False,
            "decision_recorded": False,
            "work_issue": projection,
        }
