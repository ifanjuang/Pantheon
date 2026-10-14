"""FastAPI routes for explicit project-scoped Entity relations."""

from __future__ import annotations

from typing import Callable, Literal

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from . import entity_relations


class EntityRefBody(BaseModel):
    entity_type: Literal[
        "project", "information", "decision", "person", "organization", "apu_object"
    ]
    entity_id: str = Field(min_length=1, max_length=300)


class EntityRelationProposeBody(BaseModel):
    relation_id: str = Field(min_length=1, max_length=300)
    project_ref: str = Field(min_length=1, max_length=300)
    from_ref: EntityRefBody = Field(alias="from")
    to_ref: EntityRefBody = Field(alias="to")
    relation_type: Literal[
        "responds_to", "relies_on", "supersedes", "contradicts"
    ]
    rationale: str | None = Field(default=None, max_length=10000)
    source_refs: list[str] = Field(default_factory=list, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)


class EntityRelationDecisionBody(BaseModel):
    # A relation now passes through proposed -> canonical -> retired, so a
    # decision can legitimately arrive at revision 2. The old `le=1` encoded a
    # two-state lifecycle and would refuse every retirement of a canonized edge.
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


def install_entity_relation_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_editor_key: Callable,
    require_hermes_key: Callable | None = None,
) -> None:
    def operation(callback):
        try:
            return with_connection(callback)
        except entity_relations.EntityRelationNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            entity_relations.EntityRelationConflict,
            entity_relations.EntityRelationGateRequired,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except entity_relations.EntityRelationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except psycopg.errors.RaiseException as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc).splitlines()[0],
            ) from exc

    def human_actor(
        value: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
    ) -> str:
        actor = str(value or "").strip()
        if not actor:
            raise HTTPException(
                status_code=400,
                detail="X-Pantheon-Human-Actor is required",
            )
        return actor

    @app.get("/agency/entity-relations/{relation_id}")
    def get_entity_relation(
        relation_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        relation = operation(lambda conn: entity_relations.get_relation(conn, relation_id))
        return {
            "system_of_record": "postgres",
            "relation": relation,
            "project_truth_created": False,
            "evidence_admitted": False,
        }

    @app.get("/agency/projects/{project_id}/entity-relations")
    def list_project_entity_relations(
        project_id: str,
        include_retired: bool = False,
        limit: int = 200,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        relations = operation(
            lambda conn: entity_relations.list_project_relations(
                conn,
                project_id=project_id,
                include_retired=include_retired,
                limit=limit,
            )
        )
        return {
            "system_of_record": "postgres",
            "project_ref": project_id,
            "relations": relations,
            "inferred_relations_included": False,
        }

    @app.get("/agency/entities/{entity_type}/{entity_id}/relations")
    def list_entity_relations(
        entity_type: Literal["information"],
        entity_id: str,
        include_retired: bool = False,
        limit: int = 200,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        relations = operation(
            lambda conn: entity_relations.list_entity_relations(
                conn,
                entity={"entity_type": entity_type, "entity_id": entity_id},
                include_retired=include_retired,
                limit=limit,
            )
        )
        return {
            "system_of_record": "postgres",
            "entity": {"entity_type": entity_type, "entity_id": entity_id},
            "relations": relations,
        }

    @app.post("/agency/entity-relations", status_code=status.HTTP_201_CREATED)
    def propose_entity_relation(
        body: EntityRelationProposeBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(human_actor),
    ) -> dict:
        values = body.model_dump(by_alias=False)
        relation = operation(
            lambda conn: entity_relations.propose_relation(
                conn,
                relation_id=values["relation_id"],
                project_id=values["project_ref"],
                from_ref=values["from_ref"],
                to_ref=values["to_ref"],
                relation_type=values["relation_type"],
                rationale=values["rationale"],
                source_refs=values["source_refs"],
                actor=actor,
                actor_kind="human",
                idempotency_key=values["idempotency_key"],
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "entity_relation_proposed",
            "relation": relation,
            "relation_canonized": False,
            "project_truth_created": False,
            "evidence_admitted": False,
            "task_authorized": False,
        }

    # Hermes reaches relations through this route and no other. It proposes; it
    # cannot canonize, reject or retire, and the schema refuses a Hermes actor on
    # any of those events even if a future caller tries.
    if require_hermes_key is not None:

        @app.post("/hermes/entity-relations", status_code=status.HTTP_201_CREATED)
        def propose_entity_relation_as_hermes(
            body: EntityRelationProposeBody,
            _authorized: None = Depends(require_hermes_key),
            actor: str = Header(alias="X-Pantheon-Hermes-Actor"),
        ) -> dict:
            values = body.model_dump(by_alias=False)
            relation = operation(
                lambda conn: entity_relations.propose_relation(
                    conn,
                    relation_id=values["relation_id"],
                    project_id=values["project_ref"],
                    from_ref=values["from_ref"],
                    to_ref=values["to_ref"],
                    relation_type=values["relation_type"],
                    rationale=values["rationale"],
                    source_refs=values["source_refs"],
                    actor=actor,
                    actor_kind="hermes",
                    idempotency_key=values["idempotency_key"],
                )
            )
            return {
                "system_of_record": "postgres",
                "effect": "entity_relation_proposed",
                "relation": relation,
                "relation_canonized": False,
                "project_truth_created": False,
                "evidence_admitted": False,
                "task_authorized": False,
            }

    @app.post("/agency/entity-relations/{relation_id}/canonize")
    def canonize_entity_relation(
        relation_id: str,
        body: EntityRelationDecisionBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(human_actor),
    ) -> dict:
        relation = operation(
            lambda conn: entity_relations.canonize_relation(
                conn,
                relation_id=relation_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind="human",
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "canonical_entity_relation_created",
            "relation": relation,
            "evidence_admitted": False,
            "task_authorized": False,
        }

    @app.post("/agency/entity-relations/{relation_id}/reject")
    def reject_entity_relation(
        relation_id: str,
        body: EntityRelationDecisionBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(human_actor),
    ) -> dict:
        relation = operation(
            lambda conn: entity_relations.reject_relation(
                conn,
                relation_id=relation_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind="human",
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "entity_relation_rejected",
            "relation": relation,
            "history_deleted": False,
        }

    @app.post("/agency/entity-relations/{relation_id}/retire")
    def retire_entity_relation(
        relation_id: str,
        body: EntityRelationDecisionBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(human_actor),
    ) -> dict:
        relation = operation(
            lambda conn: entity_relations.retire_relation(
                conn,
                relation_id=relation_id,
                expected_revision=body.expected_revision,
                actor=actor,
                actor_kind="human",
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "canonical_entity_relation_retired",
            "relation": relation,
            "history_deleted": False,
        }
