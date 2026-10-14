"""Read-only global Decisions inbox.

The global space is a projection of Decision Requests whose ``project_ref`` is
null. It is not an agency-level Decision authority and it never duplicates a
request already classified into a Project.
"""

from __future__ import annotations

from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, HTTPException

from . import decision_request_views, decision_requests


RequestStatus = Literal["pending", "resolved", "cancelled"]


def install_decision_inbox_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
) -> None:
    def execute(operation):
        try:
            return with_connection(operation)
        except decision_requests.DecisionRequestError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/decision-inbox")
    def list_unclassified_decision_requests(
        status: RequestStatus | None = "pending",
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        items = execute(
            lambda conn: decision_request_views.list_unclassified_requests(
                conn,
                status=status,
                limit=limit,
            )
        )
        return {
            "decision_requests": items,
            "unclassified_only": True,
            "project_ref": None,
            "agency_decision_owner": False,
            "attention_only_when_pending": True,
        }
