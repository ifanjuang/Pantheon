"""FastAPI route installer for generic Source intake admission."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import source_intake
from .canonical_projections import project_source


class SourceOriginBody(BaseModel):
    system: str = Field(min_length=1, max_length=200)
    external_ref: str = Field(min_length=1, max_length=2000)
    producer: str | None = Field(default=None, max_length=500)
    received_by: str | None = Field(default=None, max_length=500)


class SourceCreateBody(BaseModel):
    source_id: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9._-]+$")
    source_kind: Literal[
        "email", "document", "image", "audio", "video", "model",
        "url", "text", "archive", "event", "other",
    ]
    origin: SourceOriginBody
    raw_source_ref: str = Field(min_length=1, max_length=4000)
    received_at: datetime
    declared_project_name: str | None = Field(default=None, max_length=500)
    source_date: datetime | None = None
    mime_type: str | None = Field(default=None, max_length=300)
    checksum: str | None = Field(default=None, min_length=64, max_length=64)
    confidentiality: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=200)


class SourceMutationBody(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class SourceMetadataBody(SourceMutationBody):
    declared_project_name: str | None = Field(default=None, max_length=500)
    source_date: datetime | None = None
    mime_type: str | None = Field(default=None, max_length=300)
    checksum: str | None = Field(default=None, min_length=64, max_length=64)
    confidentiality: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] | None = None


class ProjectCandidateBody(BaseModel):
    project_ref: str = Field(min_length=1, max_length=200)
    score: float = Field(ge=0, le=1)
    basis: list[str] = Field(min_length=1, max_length=20)
    producer: str = Field(min_length=1, max_length=500)
    created_at: datetime


class SourceSuggestBody(SourceMutationBody):
    candidates: list[ProjectCandidateBody] = Field(min_length=1, max_length=20)


class SourceLinkBody(SourceMutationBody):
    project_id: str = Field(min_length=1, max_length=200)


class SourceContainsBody(BaseModel):
    target_source_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)


def install_source_intake_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_writer_kind: Callable,
    require_actor: Callable,
) -> None:
    def operation(callback):
        try:
            return with_connection(callback)
        except source_intake.SourceNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            source_intake.StaleSourceWrite,
            source_intake.SourceIdempotencyConflict,
            source_intake.SourceGovernanceGateRequired,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except source_intake.SourceIntakeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def require_human_writer(writer_kind: str = Depends(require_writer_kind)) -> str:
        if writer_kind != "human":
            raise HTTPException(
                status_code=403,
                detail="global Source intake writes require a human editor credential",
            )
        return writer_kind

    @app.get("/agency/sources")
    def list_sources(
        project_link_status: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        sources = operation(
            lambda conn: source_intake.list_sources(
                conn,
                project_link_status=project_link_status,
                project_id=project_id,
                limit=limit,
            )
        )
        return {
            "system_of_record": "postgres",
            "scope_match": "agency_sources",
            "sources": sources,
            "source_projections": [project_source(item) for item in sources],
            "semantic_effects": {
                "information_created": False,
                "project_created": False,
                "evidence_admitted": False,
            },
        }

    @app.get("/agency/sources/{source_id}")
    def get_source(
        source_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        source = operation(lambda conn: source_intake.get_source(conn, source_id))
        return {"system_of_record": "postgres", "source": source, "source_projection": project_source(source)}

    @app.post("/agency/sources", status_code=201)
    def create_source(
        body: SourceCreateBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        values = body.model_dump()
        origin = values.pop("origin")
        idempotency_key = values.pop("idempotency_key")
        source = operation(
            lambda conn: source_intake.create_source(
                conn,
                **values,
                origin_system=origin["system"],
                origin_external_ref=origin["external_ref"],
                origin_producer=origin.get("producer"),
                received_by=origin.get("received_by"),
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "source": source, "source_projection": project_source(source),
            "project_mutated": False,
            "information_created": False,
            "evidence_admitted": False,
        }

    @app.patch("/agency/sources/{source_id}/metadata")
    def update_source_metadata(
        source_id: str,
        body: SourceMetadataBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        changes = body.model_dump(
            exclude={"expected_revision", "idempotency_key"}, exclude_unset=True
        )
        source = operation(
            lambda conn: source_intake.update_metadata(
                conn,
                source_id=source_id,
                changes=changes,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {"system_of_record": "postgres", "source": source, "source_projection": project_source(source)}

    @app.post("/agency/sources/{source_id}/suggest-projects")
    def suggest_source_projects(
        source_id: str,
        body: SourceSuggestBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        candidates = [item.model_dump(mode="json") for item in body.candidates]
        source = operation(
            lambda conn: source_intake.suggest_projects(
                conn,
                source_id=source_id,
                candidates=candidates,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "source": source, "source_projection": project_source(source),
            "project_link_confirmed": False,
        }

    @app.post("/agency/sources/{source_id}/link-project")
    def link_source_project(
        source_id: str,
        body: SourceLinkBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        source = operation(
            lambda conn: source_intake.link_project(
                conn,
                source_id=source_id,
                project_id=body.project_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {"system_of_record": "postgres", "source": source, "source_projection": project_source(source)}

    @app.post("/agency/sources/{source_id}/unlink-project")
    def unlink_source_project(
        source_id: str,
        body: SourceMutationBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        source = operation(
            lambda conn: source_intake.unlink_project(
                conn,
                source_id=source_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {"system_of_record": "postgres", "source": source, "source_projection": project_source(source)}

    @app.post("/agency/sources/{source_id}/exclude")
    def exclude_source(
        source_id: str,
        body: SourceMutationBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        source = operation(
            lambda conn: source_intake.exclude_source(
                conn,
                source_id=source_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {"system_of_record": "postgres", "source": source, "source_projection": project_source(source)}

    @app.post("/agency/sources/{source_id}/restore")
    def restore_source(
        source_id: str,
        body: SourceMutationBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        source = operation(
            lambda conn: source_intake.restore_source(
                conn,
                source_id=source_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {"system_of_record": "postgres", "source": source, "source_projection": project_source(source)}

    @app.post("/agency/sources/{source_id}/contains", status_code=201)
    def relate_contained_source(
        source_id: str,
        body: SourceContainsBody,
        writer_kind: str = Depends(require_human_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        relation = operation(
            lambda conn: source_intake.relate_contained_source(
                conn,
                source_id=source_id,
                target_source_id=body.target_source_id,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "relation": relation,
            "project_mutated": False,
            "information_created": False,
        }
