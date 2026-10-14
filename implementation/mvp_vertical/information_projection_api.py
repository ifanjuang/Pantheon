"""FastAPI routes for Information card projection metadata and Document links."""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from . import information_projection
from .canonical_projections import project_information


class ContactRefBody(BaseModel):
    label: str = Field(min_length=1, max_length=500)
    person_id: str | None = Field(default=None, max_length=200)
    organization_id: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=300)


class ProjectionMetadataBody(BaseModel):
    expected_revision: int = Field(ge=0)
    idempotency_key: str = Field(min_length=8, max_length=200)
    source_date: date | None = None
    received_at: datetime | None = None
    issued_at: datetime | None = None
    media_types: list[str] = Field(default_factory=lambda: ["text"], min_length=1, max_length=20)
    contact_refs: list[ContactRefBody] = Field(default_factory=list, max_length=500)


class DocumentLinkBody(BaseModel):
    document_id: str = Field(min_length=1, max_length=300)
    role: Literal["primary", "supporting", "attachment"] = "supporting"
    observed_version: int | None = Field(default=None, ge=1)
    observed_digest: str | None = Field(default=None, max_length=300)
    expected_revision: int = Field(ge=0)
    idempotency_key: str = Field(min_length=8, max_length=200)


class DocumentUnlinkBody(BaseModel):
    expected_revision: int = Field(ge=0)
    idempotency_key: str = Field(min_length=8, max_length=200)


def install_information_projection_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_writer_kind: Callable,
    require_actor: Callable,
) -> None:
    """Install bounded routes into the existing Cockpit app."""

    def projection_operation(operation):
        try:
            return with_connection(operation)
        except information_projection.InformationProjectionNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            information_projection.StaleInformationProjectionWrite,
            information_projection.InformationProjectionIdempotencyConflict,
            information_projection.InformationProjectionGateRequired,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except information_projection.InformationProjectionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except psycopg.errors.RaiseException as exc:
            detail = str(exc).splitlines()[0]
            raise HTTPException(status_code=422, detail=detail) from exc

    def require_human_writer(writer_kind: str = Depends(require_writer_kind)) -> Literal["human"]:
        if writer_kind != "human":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hermes direct Information projection writes are disabled; "
                    "use an admitted bounded capability"
                ),
            )
        return "human"

    @app.get("/agency/information/{information_id}/projection")
    def get_information_projection(
        information_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        projection = projection_operation(
            lambda conn: information_projection.get_projection(conn, information_id)
        )
        return {"system_of_record": "postgres", "information_projection": project_information(projection), **projection}

    @app.get("/agency/projects/{project_id}/information-projections")
    def list_project_information_projections(
        project_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        projections = projection_operation(
            lambda conn: information_projection.list_project_projections(conn, project_id)
        )
        return {
            "system_of_record": "postgres",
            "project_id": project_id,
            "information_projections": projections,
            "canonical_information_projections": [project_information(item) for item in projections],
            "authorization_inferred": False,
        }

    @app.put("/agency/information/{information_id}/projection-metadata")
    def update_information_projection_metadata(
        information_id: str,
        body: ProjectionMetadataBody,
        writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        values = body.model_dump()
        values["contact_refs"] = [item.model_dump(exclude_none=True) for item in body.contact_refs]
        projection = projection_operation(
            lambda conn: information_projection.update_projection_metadata(
                conn,
                information_id=information_id,
                actor=actor,
                actor_kind=writer_kind,
                **values,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_information_projection_write",
            "approval_inferred": False,
            "information_projection": project_information(projection),
            **projection,
        }

    @app.post(
        "/agency/information/{information_id}/documents",
        status_code=status.HTTP_201_CREATED,
    )
    def link_information_document(
        information_id: str,
        body: DocumentLinkBody,
        response: Response,
        writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        projection = projection_operation(
            lambda conn: information_projection.add_document_link(
                conn,
                information_id=information_id,
                actor=actor,
                actor_kind=writer_kind,
                **body.model_dump(),
            )
        )
        response.status_code = (
            status.HTTP_201_CREATED
            if projection.get("document_link_operation") == "created"
            else status.HTTP_200_OK
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_information_document_link_write",
            "approval_inferred": False,
            "information_projection": project_information(projection),
            **projection,
        }

    @app.delete("/agency/information/{information_id}/documents/{document_id}")
    def unlink_information_document(
        information_id: str,
        document_id: str,
        body: DocumentUnlinkBody,
        writer_kind: Literal["human"] = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        projection = projection_operation(
            lambda conn: information_projection.remove_document_link(
                conn,
                information_id=information_id,
                document_id=document_id,
                actor=actor,
                actor_kind=writer_kind,
                **body.model_dump(),
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_information_document_link_write",
            "approval_inferred": False,
            "information_projection": project_information(projection),
            **projection,
        }
