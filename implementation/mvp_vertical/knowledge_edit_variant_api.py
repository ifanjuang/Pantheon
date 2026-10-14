"""Bounded mobile review routes for Knowledge edit proposal variants."""

from __future__ import annotations

from typing import Any, Callable, Literal

from fastapi import Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import decision_requests, knowledge, knowledge_edit_variants
from .policy_gate import PolicyClient


class VariantEditRequestBody(BaseModel):
    request_id: str = Field(min_length=3, max_length=200)
    instruction_kind: Literal["rewrite", "expand", "simplify", "verify", "move_to_lot"]
    instruction: str = Field(min_length=1, max_length=10_000)
    base_version: int = Field(ge=1)
    selection_start: int = Field(ge=0)
    selection_end: int = Field(ge=1)
    selected_text: str = Field(min_length=1, max_length=500_000)
    requested_by: str = Field(min_length=1, max_length=500)
    requested_variant_count: Literal[1, 2] = 1
    idempotency_key: str = Field(min_length=8, max_length=200)


class VariantSelectionBody(BaseModel):
    variant_id: str = Field(min_length=3, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)


class VariantRejectionBody(BaseModel):
    reason: str = Field(min_length=1, max_length=10_000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class ApplySelectedVariantBody(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    # Required when Pantheon policy enforcement is active; ignored otherwise.
    human_decision_ref: str | None = Field(default=None, min_length=2, max_length=500)


def _human_actor(value: str | None) -> str:
    actor = (value or "").strip()
    if not actor:
        raise HTTPException(
            status_code=422,
            detail="X-Pantheon-Human-Actor is required for Knowledge review",
        )
    return actor


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, (knowledge.KnowledgeNotFound, decision_requests.DecisionRecordNotFound)):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, decision_requests.DecisionRequestError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(
        exc,
        (
            knowledge.StaleKnowledgeWrite,
            knowledge.IdempotencyConflict,
            knowledge_edit_variants.KnowledgeEditVariantConflict,
        ),
    ):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, knowledge.KnowledgeError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Knowledge edit review operation failed")


def install_knowledge_edit_variant_routes(
    app,
    *,
    with_connection: Callable[[Callable[..., Any]], Any],
    require_editor_key,
) -> None:
    def operation(call):
        try:
            return with_connection(call)
        except Exception as exc:
            raise _translate(exc) from exc

    def require_policy_client() -> PolicyClient | None:
        """Same chokepoint `cockpit_api.py` defines, read off the same app.state.

        This module is installed onto the app `cockpit_shell.create_cockpit_app`
        already configured, so `policy_client`/`policy_enforcement` are already
        set there. Read defensively rather than assuming: this installer is
        also unit-tested against a bare app that never went through that
        composition, where the attributes do not exist yet.
        """
        enforcement = getattr(app.state, "policy_enforcement", "required")
        if enforcement == "disabled":
            return None
        client = getattr(app.state, "policy_client", None)
        if client is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Pantheon policy decision point is not configured; "
                    "applying a selected Knowledge edit variant cannot be "
                    "admitted. Set MVP_POLICY_API_URL and MVP_POLICY_API_KEY, "
                    "or declare MVP_POLICY_ENFORCEMENT=disabled explicitly."
                ),
            )
        return client

    @app.post(
        "/knowledge/{knowledge_id}/variant-edit-requests",
        status_code=202,
        dependencies=[Depends(require_editor_key)],
    )
    def create_variant_edit_request(
        knowledge_id: str,
        body: VariantEditRequestBody,
    ) -> dict[str, Any]:
        review = operation(
            lambda conn: knowledge_edit_variants.create_variant_request(
                conn,
                knowledge_id=knowledge_id,
                **body.model_dump(),
            )
        )
        return {
            "effect": "knowledge_edit_request_queued",
            "knowledge_mutated": False,
            "execution_authorized": False,
            "task_authorized": False,
            "evidence_admitted": False,
            **review,
        }

    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/project-knowledge-edit-variant",
        dependencies=[Depends(require_editor_key)],
    )
    def project_execution_result_variant(
        execution_result_id: str,
        result_ref: str,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        review = operation(
            lambda conn: knowledge_edit_variants.project_execution_result_variant(
                conn,
                execution_result_id=execution_result_id,
                result_ref=result_ref,
                idempotency_key=idempotency_key or "",
            )
        )
        return {
            "effect": "knowledge_edit_variant_projected",
            "execution_result_mutated": False,
            "knowledge_mutated": False,
            "variant_selected": False,
            "edit_applied": False,
            "evidence_admitted": False,
            **review,
        }

    @app.get(
        "/knowledge/{knowledge_id}/edit-reviews",
        dependencies=[Depends(require_editor_key)],
    )
    def list_edit_reviews(
        knowledge_id: str,
        status: Literal[
            "queued_for_hermes", "proposed", "applied", "conflict", "rejected"
        ] | None = None,
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        reviews = operation(
            lambda conn: knowledge_edit_variants.list_variant_reviews(
                conn,
                knowledge_id=knowledge_id,
                status=status,
                limit=limit,
            )
        )
        return {
            "knowledge_id": knowledge_id,
            "edit_reviews": reviews,
            "variant_selected_is_edit_applied": False,
            "proposal_is_evidence": False,
        }

    @app.get(
        "/edit-requests/{request_id}/review",
        dependencies=[Depends(require_editor_key)],
    )
    def get_edit_review(request_id: str) -> dict[str, Any]:
        return operation(
            lambda conn: knowledge_edit_variants.get_variant_review(conn, request_id)
        )

    @app.post(
        "/edit-requests/{request_id}/select-variant",
        dependencies=[Depends(require_editor_key)],
    )
    def select_edit_variant(
        request_id: str,
        body: VariantSelectionBody,
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
    ) -> dict[str, Any]:
        actor = _human_actor(human_actor)
        review = operation(
            lambda conn: knowledge_edit_variants.select_variant(
                conn,
                request_id=request_id,
                variant_id=body.variant_id,
                actor=actor,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "knowledge_edit_variant_selected",
            "knowledge_mutated": False,
            "edit_applied": False,
            "task_authorized": False,
            "evidence_admitted": False,
            **review,
        }

    @app.post(
        "/edit-requests/{request_id}/reject",
        dependencies=[Depends(require_editor_key)],
    )
    def reject_edit_request(
        request_id: str,
        body: VariantRejectionBody,
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
    ) -> dict[str, Any]:
        actor = _human_actor(human_actor)
        review = operation(
            lambda conn: knowledge_edit_variants.reject_request(
                conn,
                request_id=request_id,
                actor=actor,
                reason=body.reason,
                idempotency_key=body.idempotency_key,
            )
        )
        return {
            "effect": "knowledge_edit_request_rejected",
            "knowledge_mutated": False,
            "task_authorized": False,
            "evidence_admitted": False,
            **review,
        }

    @app.post(
        "/edit-requests/{request_id}/apply-selected",
        dependencies=[Depends(require_editor_key)],
    )
    def apply_selected_edit_variant(
        request_id: str,
        body: ApplySelectedVariantBody,
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
        policy_client: PolicyClient | None = Depends(require_policy_client),
    ) -> dict[str, Any]:
        actor = _human_actor(human_actor)

        def apply_variant(conn):
            canonical_decision = {}
            if policy_client is not None:
                if not body.human_decision_ref:
                    raise decision_requests.DecisionRequestError(
                        "applying a Knowledge variant requires a canonical human Decision reference"
                    )
                with conn.transaction():
                    canonical_decision = decision_requests.policy_decision_payload(
                        conn, body.human_decision_ref, expectation={}
                    )
            return knowledge_edit_variants.apply_selected_variant(
                conn,
                request_id=request_id,
                actor=actor,
                idempotency_key=body.idempotency_key,
                policy_client=policy_client,
                decision_payload=canonical_decision,
            )

        applied = operation(apply_variant)
        return {
            "effect": "knowledge_edit_variant_applied",
            "edit_applied": True,
            "review_status_promoted": False,
            "evidence_admitted": False,
            **applied,
        }
