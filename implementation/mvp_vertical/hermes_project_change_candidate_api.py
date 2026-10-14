"""Admission-bound Hermes creation of Project attribute ChangeCandidates.

Hermes may deposit a proposal only for a Project already present in the exact
active Context Pack. This route never applies the proposal and never mutates the
Project. Human review through the Agency ChangeCandidate gate remains required.
"""

from __future__ import annotations

import hmac
from typing import Any, Callable

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import agency_change_candidates, hermes_active_context, hermes_scoped_context


class HermesProjectChangeCandidateBody(BaseModel):
    expected_project_revision: int = Field(ge=1)
    proposed_attributes: dict[str, Any] = Field(min_length=1)
    reason: str | None = Field(default=None, max_length=10_000)
    source_refs: list[str] = Field(default_factory=list, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=200)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def install_hermes_project_change_candidate_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
) -> None:
    def require_hermes_key(authorization: str | None = Header(default=None)) -> None:
        expected = getattr(app.state, "hermes_api_key", "")
        if not expected:
            raise HTTPException(status_code=503, detail="Hermes API key is not configured")
        if not hmac.compare_digest(_bearer_token(authorization), expected):
            raise HTTPException(status_code=401, detail="invalid Hermes API key")

    def require_hermes_actor(
        x_pantheon_hermes_actor: str | None = Header(default=None, alias="X-Pantheon-Hermes-Actor"),
    ) -> str:
        if not x_pantheon_hermes_actor or not x_pantheon_hermes_actor.strip():
            raise HTTPException(
                status_code=422,
                detail="X-Pantheon-Hermes-Actor is required for a Hermes candidate proposal",
            )
        return x_pantheon_hermes_actor.strip()

    def operation(call):
        try:
            return with_connection(call)
        except hermes_active_context.ActiveContextNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            hermes_active_context.ActiveContextConflict,
            hermes_scoped_context.ScopedContextConflict,
            agency_change_candidates.ChangeCandidateConflict,
            agency_change_candidates.ChangeCandidateIdempotencyConflict,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (
            hermes_scoped_context.HermesScopedContextError,
            agency_change_candidates.ChangeCandidateError,
        ) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post(
        "/hermes/execution-admissions/{admission_id}/projects/{project_id}/change-candidates",
        status_code=201,
    )
    def create_project_change_candidate(
        admission_id: str,
        project_id: str,
        body: HermesProjectChangeCandidateBody,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        def create(conn):
            scoped = hermes_active_context.get_active_context_entity(
                conn,
                admission_id=admission_id,
                entity_type="project",
                entity_id=f"project:{project_id}",
                actor=actor,
            )
            current_revision = scoped.get("current_revision")
            if current_revision != body.expected_project_revision:
                raise agency_change_candidates.ChangeCandidateConflict(
                    f"stale Project revision for Hermes candidate: expected "
                    f"{body.expected_project_revision}, current {current_revision}"
                )

            manifest = hermes_active_context.get_active_context_manifest(
                conn,
                admission_id=admission_id,
                actor=actor,
            )
            admitted_sources = set(manifest.get("source_refs") or [])
            outside = sorted(set(body.source_refs) - admitted_sources)
            if outside:
                raise agency_change_candidates.ChangeCandidateError(
                    "Hermes ChangeCandidate references source(s) outside the admitted Context Pack: "
                    + ", ".join(outside)
                )

            return agency_change_candidates.create_project_candidate(
                conn,
                project_id=project_id,
                base_revision=body.expected_project_revision,
                proposed_attributes=body.proposed_attributes,
                proposer=actor,
                proposer_kind="hermes",
                reason=body.reason,
                source_refs=body.source_refs,
                idempotency_key=body.idempotency_key,
            )

        candidate = operation(create)
        return {
            "effect": "project_change_candidate_proposed",
            "project_mutated": False,
            "execution_authorized": False,
            "human_apply_required": True,
            "evidence_admitted": False,
            "change_candidate": candidate,
            "non_equivalences": [
                "candidate created != Project mutated",
                "candidate created != approved",
                "source_ref != Evidence",
                "runtime authority != human apply authority",
            ],
        }
