"""Human-gated WorkIssue scope routes.

These endpoints create and project aggregate-owned scope links. They do not
widen Context Packs, dispatch Hermes or create a second relation authority.
"""

from __future__ import annotations

from typing import Callable, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from . import work_issue_scopes, work_issues


ScopeEntityType = Literal[
    "agency",
    "project",
    "information",
    "decision",
    "person",
    "organization",
    "apu_object",
]
ScopeRole = Literal["primary", "related"]


class ScopeInput(BaseModel):
    scope_link_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    entity_type: ScopeEntityType
    entity_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    scope_role: ScopeRole = "related"
    rationale: str | None = Field(default=None, min_length=1, max_length=10000)


class ScopedWorkIssueCreateBody(BaseModel):
    issue_id: str = Field(pattern=r"^[a-z0-9._-]+$")
    case_ref: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=3, max_length=1000)
    description: str = Field(min_length=1, max_length=20000)
    idempotency_key: str = Field(min_length=8, max_length=200)
    issue_type: Literal[
        "research", "verification", "correction", "drafting", "decision", "action"
    ] = "action"
    priority: str = Field(default="normal", min_length=1, max_length=100)
    requested_effect: Literal[
        "read_only", "draft", "internal_write", "external_effect", "canonical_effect"
    ] = "draft"
    assigned_to: str | None = Field(default=None, min_length=1, max_length=200)
    task_contract_ref: str | None = Field(default=None, min_length=1, max_length=500)
    context_pack_ref: str | None = Field(default=None, min_length=1, max_length=500)
    scopes: list[ScopeInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def exactly_one_primary_scope(self):
        if sum(scope.scope_role == "primary" for scope in self.scopes) != 1:
            raise ValueError("exactly one primary WorkIssue scope is required")
        identities = {(scope.entity_type, scope.entity_id) for scope in self.scopes}
        if len(identities) != len(self.scopes):
            raise ValueError("duplicate WorkIssue scope endpoint")
        return self


class AddScopeBody(ScopeInput):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class RetireScopeBody(BaseModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    rationale: str | None = Field(default=None, min_length=1, max_length=10000)


class ReplacePrimaryScopeBody(BaseModel):
    replacement_scope_link_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    entity_type: ScopeEntityType
    entity_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    rationale: str | None = Field(default=None, min_length=1, max_length=10000)


def install_work_issue_scope_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_editor_key: Callable,
    require_human_actor: Callable,
) -> None:
    def execute(operation):
        try:
            return with_connection(operation)
        except (work_issues.IssueNotFound, work_issue_scopes.ScopeLinkNotFound) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except work_issues.StaleWrite as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except work_issue_scopes.ScopeOwnerUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except work_issue_scopes.ScopeConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (work_issue_scopes.WorkIssueScopeError, work_issues.WorkIssueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/work/issues", status_code=201)
    def create_scoped_work_issue(
        body: ScopedWorkIssueCreateBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        projection = execute(
            lambda conn: work_issue_scopes.create_scoped_issue(
                conn,
                created_by=actor,
                scopes=[scope.model_dump() for scope in body.scopes],
                **body.model_dump(exclude={"scopes"}),
            )
        )
        return {
            "effect": "work_issue_created",
            "scope_is_not_authorization": True,
            "work_issue": projection,
        }

    @app.get("/work/issues/{issue_id}/scopes")
    def get_work_issue_scopes(
        issue_id: str,
        include_retired: bool = False,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        projection = execute(
            lambda conn: work_issue_scopes.get_scoped_issue(
                conn,
                issue_id,
                include_retired_scopes=include_retired,
            )
        )
        return projection

    @app.get("/work/scopes/{entity_type}/{entity_id}/issues")
    def list_work_issues_by_scope(
        entity_type: ScopeEntityType,
        entity_id: str,
        include_terminal: bool = True,
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        projections = execute(
            lambda conn: work_issue_scopes.list_scoped_issue_projections(
                conn,
                entity_type=entity_type,
                entity_id=entity_id,
                include_terminal=include_terminal,
                limit=limit,
            )
        )
        return {
            "scope_ref": {"entity_type": entity_type, "entity_id": entity_id},
            "scope_match": "exact_entity_ref",
            "scope_is_not_authorization": True,
            "work_issues": projections,
        }

    @app.post("/work/issues/{issue_id}/scopes", status_code=201)
    def add_work_issue_scope(
        issue_id: str,
        body: AddScopeBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        projection = execute(
            lambda conn: work_issue_scopes.add_scope(
                conn,
                issue_id=issue_id,
                actor=actor,
                **body.model_dump(),
            )
        )
        return {
            "effect": "work_issue_scope_linked",
            "scope_is_not_authorization": True,
            "work_issue": projection,
        }

    @app.post("/work/issues/{issue_id}/scopes/{scope_link_id}/retire")
    def retire_work_issue_scope(
        issue_id: str,
        scope_link_id: str,
        body: RetireScopeBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        projection = execute(
            lambda conn: work_issue_scopes.retire_scope(
                conn,
                issue_id=issue_id,
                scope_link_id=scope_link_id,
                actor=actor,
                **body.model_dump(),
            )
        )
        return {
            "effect": "work_issue_scope_retired",
            "scope_is_not_authorization": True,
            "work_issue": projection,
        }

    @app.post("/work/issues/{issue_id}/scopes/{scope_link_id}/replace-primary")
    def replace_primary_work_issue_scope(
        issue_id: str,
        scope_link_id: str,
        body: ReplacePrimaryScopeBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        projection = execute(
            lambda conn: work_issue_scopes.replace_primary_scope(
                conn,
                issue_id=issue_id,
                current_scope_link_id=scope_link_id,
                actor=actor,
                **body.model_dump(),
            )
        )
        return {
            "effect": "work_issue_primary_scope_replaced",
            "scope_is_not_authorization": True,
            "work_issue": projection,
        }
