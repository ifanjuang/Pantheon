"""Bounded API routes for execution results and review dispositions."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, Query

from . import (
    apu_mapping_converter,
    apu_mapping_reviews,
    execution_results,
    project_claim_candidates,
)


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            execution_results.ExecutionResultNotFound,
            apu_mapping_reviews.ApuMappingReviewNotFound,
            project_claim_candidates.ProjectClaimCandidateNotFound,
        ),
    ):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(
        exc,
        (
            execution_results.ExecutionResultConflict,
            project_claim_candidates.ProjectClaimCandidateConflict,
        ),
    ):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(
        exc,
        (
            execution_results.ExecutionResultError,
            apu_mapping_reviews.ApuMappingReviewError,
            project_claim_candidates.ProjectClaimCandidateError,
        ),
    ):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="execution result operation failed")


def install_execution_result_routes(
    app,
    *,
    with_connection: Callable[[Callable[..., Any]], Any],
    require_read_key,
    require_editor_key,
    require_hermes_key,
) -> None:
    @app.post("/execution-results", dependencies=[Depends(require_hermes_key)])
    def submit_execution_result(
        payload: dict[str, Any],
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            stored = with_connection(
                lambda conn: execution_results.store_execution_result(
                    conn,
                    execution_result=payload,
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {
            "status": "recorded",
            "execution": stored,
            "result_stored": True,
            "result_accepted": False,
            "project_claim_created": False,
            "apu_mutated": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.get(
        "/execution-results/{execution_result_id}",
        dependencies=[Depends(require_read_key)],
    )
    def read_execution_result(execution_result_id: str) -> dict[str, Any]:
        try:
            return with_connection(
                lambda conn: execution_results.get_execution_result(conn, execution_result_id)
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.get(
        "/projects/{project_ref}/execution-results",
        dependencies=[Depends(require_read_key)],
    )
    def list_execution_results(
        project_ref: str,
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        try:
            items = with_connection(
                lambda conn: execution_results.list_project_execution_results(
                    conn, project_ref=project_ref, limit=limit
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {"project_ref": project_ref, "items": items, "count": len(items)}

    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/dispositions",
        dependencies=[Depends(require_editor_key)],
    )
    def review_result_candidate(
        execution_result_id: str,
        result_ref: str,
        payload: dict[str, Any],
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(status_code=422, detail="X-Pantheon-Human-Actor is required")
        try:
            current = with_connection(
                lambda conn: execution_results.get_execution_result(conn, execution_result_id)
            )
            if result_ref not in {item["result_id"] for item in current["results"]}:
                raise execution_results.ExecutionResultNotFound(
                    "result candidate does not belong to execution result"
                )
            stored = with_connection(
                lambda conn: execution_results.append_review_disposition(
                    conn,
                    result_ref=result_ref,
                    disposition=str(payload.get("disposition") or ""),
                    reviewer=actor,
                    reviewer_kind="human",
                    note=payload.get("note"),
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {
            "status": "recorded",
            "execution": stored,
            "review_disposition_recorded": True,
            "human_decision_recorded": False,
            "project_claim_created": False,
            "apu_mutated": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/project-claim",
        dependencies=[Depends(require_editor_key)],
        status_code=201,
    )
    def create_project_claim_from_candidate(
        execution_result_id: str,
        result_ref: str,
        payload: dict[str, Any],
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(status_code=422, detail="X-Pantheon-Human-Actor is required")
        try:
            claim = with_connection(
                lambda conn: project_claim_candidates.create_claim_from_candidate(
                    conn,
                    execution_id=execution_result_id,
                    result_id=result_ref,
                    actor=actor,
                    status=str(payload.get("status") or ""),
                    certainty=payload.get("certainty"),
                    backing_ref=payload.get("backing_ref"),
                    supersedes=payload.get("supersedes"),
                    note=payload.get("note"),
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {
            "status": "created",
            "claim": claim,
            "project_claim_created": True,
            "source_result_mutated": False,
            "project_record_mutated": False,
            "human_decision_recorded": False,
            "work_issue_created": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/prepare-apu-mapping",
        dependencies=[Depends(require_editor_key)],
    )
    def prepare_apu_mapping(
        execution_result_id: str,
        result_ref: str,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            stored = with_connection(
                lambda conn: apu_mapping_converter.convert_and_store(
                    conn,
                    execution_result_id=execution_result_id,
                    source_result_ref=result_ref,
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {
            "status": "prepared",
            "execution": stored,
            "mapping_candidate_created": True,
            "source_disposition_required": "accepted_for_mapping",
            "apu_mutated": False,
            "stable_identity_confirmed": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/mappings/{mapping_ref}/reviews",
        dependencies=[Depends(require_editor_key)],
    )
    def review_apu_mapping(
        execution_result_id: str,
        result_ref: str,
        mapping_ref: str,
        payload: dict[str, Any],
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(status_code=422, detail="X-Pantheon-Human-Actor is required")
        try:
            review = with_connection(
                lambda conn: apu_mapping_reviews.append_mapping_review(
                    conn,
                    execution_result_id=execution_result_id,
                    result_ref=result_ref,
                    mapping_ref=mapping_ref,
                    action=str(payload.get("action") or ""),
                    selected_stable_object_ref=payload.get("selected_stable_object_ref"),
                    clarification_question=payload.get("clarification_question"),
                    note=payload.get("note"),
                    reviewer=actor,
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {
            "status": "recorded",
            "review": review,
            "mapping_review_recorded": True,
            "write_preparation_allowed": review["action"] in {
                "select_existing_object", "mark_unmatched"
            },
            "apu_mutated": False,
            "stable_identity_confirmed": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.get(
        "/execution-results/{execution_result_id}/results/{result_ref}/mappings/{mapping_ref}/reviews",
        dependencies=[Depends(require_read_key)],
    )
    def read_apu_mapping_reviews(
        execution_result_id: str,
        result_ref: str,
        mapping_ref: str,
    ) -> dict[str, Any]:
        try:
            items = with_connection(
                lambda conn: apu_mapping_reviews.list_mapping_reviews(
                    conn,
                    execution_result_id=execution_result_id,
                    result_ref=result_ref,
                    mapping_ref=mapping_ref,
                )
            )
        except Exception as exc:
            raise _translate_error(exc) from exc
        return {
            "execution_result_id": execution_result_id,
            "result_ref": result_ref,
            "mapping_ref": mapping_ref,
            "items": items,
            "count": len(items),
            "current_review": items[-1] if items else None,
        }
