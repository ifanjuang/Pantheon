"""FastAPI routes for hierarchical Agency Data Category classification."""

from __future__ import annotations

import hmac
from typing import Any, Callable

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from . import agency_classification


class CategoryCreateBody(BaseModel):
    category_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=4000)
    parent_category_id: str | None = Field(default=None, max_length=200)
    applies_to: list[str] = Field(min_length=1, max_length=10)
    sort_order: int = Field(default=0, ge=0)


class CategoryUpdateBody(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    parent_category_id: str | None = Field(default=None, max_length=200)
    applies_to: list[str] | None = Field(default=None, min_length=1, max_length=10)
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("sort_order")
    @classmethod
    def reject_explicit_null_sort_order(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("sort_order cannot be null")
        return value


class CategoryArchiveBody(BaseModel):
    expected_revision: int = Field(ge=1)


class CategoryAssignmentCreateBody(BaseModel):
    assignment_id: str = Field(min_length=1, max_length=250)
    entity_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(min_length=1, max_length=250)
    rationale: str | None = Field(default=None, max_length=4000)


class CategoryAssignmentRetireBody(BaseModel):
    expected_revision: int = Field(ge=1)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def install_agency_classification_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_editor_key: Callable,
    require_human_actor: Callable,
) -> None:
    def require_classification_editor(
        authorization: str | None = Header(default=None),
    ) -> None:
        supplied = _bearer_token(authorization)
        editor = getattr(app.state, "editor_api_key", "")
        hermes = getattr(app.state, "hermes_api_key", "")
        editor_match = bool(editor and supplied and hmac.compare_digest(supplied, editor))
        hermes_match = bool(hermes and supplied and hmac.compare_digest(supplied, hermes))
        if editor_match and hermes_match:
            raise HTTPException(
                status_code=503,
                detail="editor and Hermes Category writer keys must be distinct",
            )
        if hermes_match:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hermes direct Category persistence is disabled; "
                    "suggest classification through a bounded task instead"
                ),
            )
        require_editor_key(authorization)

    def operation(fn):
        try:
            return with_connection(fn)
        except (
            agency_classification.CategoryNotFound,
            agency_classification.CategoryAssignmentNotFound,
        ) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            agency_classification.StaleCategoryWrite,
            agency_classification.StaleCategoryAssignmentWrite,
            psycopg.errors.UniqueViolation,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (
            agency_classification.AgencyClassificationError,
            psycopg.errors.RaiseException,
            psycopg.errors.CheckViolation,
            psycopg.errors.ForeignKeyViolation,
        ) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def read_envelope(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "system_of_record": "postgres",
            "classification_is_not_authorization": True,
            **payload,
        }

    def write_envelope(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "system_of_record": "postgres",
            "effect": "internal_agency_classification_write",
            "approval_inferred": False,
            "classification_is_not_authorization": True,
            **payload,
        }

    @app.get("/agency/categories")
    def list_categories(
        include_archived: bool = False,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        categories = operation(
            lambda conn: agency_classification.list_categories(
                conn,
                include_archived=include_archived,
            )
        )
        return read_envelope({"categories": categories})

    @app.get("/agency/category-roots")
    def list_category_roots(
        include_archived: bool = False,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        categories = operation(
            lambda conn: agency_classification.list_root_categories(
                conn,
                include_archived=include_archived,
            )
        )
        return read_envelope({"categories": categories})

    @app.get("/agency/categories/{category_id}")
    def get_category(
        category_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        category = operation(lambda conn: agency_classification.get_category(conn, category_id))
        return read_envelope({"category": category})

    @app.get("/agency/categories/{category_id}/collection")
    def get_category_collection(
        category_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        collection = operation(
            lambda conn: agency_classification.get_category_collection(conn, category_id)
        )
        return read_envelope({"collection": collection})

    @app.get("/agency/classification/{entity_type}/{entity_id}")
    def get_entity_categories(
        entity_type: str,
        entity_id: str,
        include_retired: bool = False,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        assignments = operation(
            lambda conn: agency_classification.list_entity_category_assignments(
                conn,
                entity_type=entity_type,
                entity_id=entity_id,
                include_retired=include_retired,
            )
        )
        return read_envelope(
            {
                "entity_ref": {"entity_type": entity_type, "entity_id": entity_id},
                "assignments": assignments,
            }
        )

    @app.post("/agency/categories", status_code=201)
    def create_category(
        body: CategoryCreateBody,
        _authorized: None = Depends(require_classification_editor),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        category = operation(
            lambda conn: agency_classification.create_category(
                conn,
                actor=actor,
                actor_kind="human",
                **body.model_dump(),
            )
        )
        return write_envelope({"category": category})

    @app.patch("/agency/categories/{category_id}")
    def update_category(
        category_id: str,
        body: CategoryUpdateBody,
        _authorized: None = Depends(require_classification_editor),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        supplied = body.model_dump(exclude_unset=True)
        expected_revision = supplied.pop("expected_revision")
        category = operation(
            lambda conn: agency_classification.update_category(
                conn,
                category_id=category_id,
                changes=supplied,
                actor=actor,
                actor_kind="human",
                expected_revision=expected_revision,
            )
        )
        return write_envelope({"category": category})

    @app.post("/agency/categories/{category_id}/archive")
    def archive_category(
        category_id: str,
        body: CategoryArchiveBody,
        _authorized: None = Depends(require_classification_editor),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        category = operation(
            lambda conn: agency_classification.archive_category(
                conn,
                category_id=category_id,
                actor=actor,
                actor_kind="human",
                expected_revision=body.expected_revision,
            )
        )
        return write_envelope({"category": category})

    @app.post("/agency/categories/{category_id}/assignments", status_code=201)
    def assign_category(
        category_id: str,
        body: CategoryAssignmentCreateBody,
        _authorized: None = Depends(require_classification_editor),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        assignment = operation(
            lambda conn: agency_classification.assign_category(
                conn,
                category_id=category_id,
                actor=actor,
                actor_kind="human",
                **body.model_dump(),
            )
        )
        return write_envelope({"assignment": assignment})

    @app.post("/agency/category-assignments/{assignment_id}/retire")
    def retire_category_assignment(
        assignment_id: str,
        body: CategoryAssignmentRetireBody,
        _authorized: None = Depends(require_classification_editor),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        assignment = operation(
            lambda conn: agency_classification.retire_category_assignment(
                conn,
                assignment_id=assignment_id,
                actor=actor,
                actor_kind="human",
                expected_revision=body.expected_revision,
            )
        )
        return write_envelope({"assignment": assignment})
