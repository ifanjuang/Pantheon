"""Human-only API for selecting one retained Project change alternative.

The route projects the selected immutable variant into the existing pending Agency
ChangeCandidate owner. It does not apply the Project mutation, create a Decision,
admit Evidence, promote memory or authorize an external effect.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, Header, HTTPException

from . import project_change_variants


def install_project_change_variant_routes(
    app,
    *,
    with_connection: Callable[[Callable[..., Any]], Any],
    require_editor_key,
) -> None:
    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/project-change-candidate",
        dependencies=[Depends(require_editor_key)],
        status_code=201,
    )
    def select_project_change_variant(
        execution_result_id: str,
        result_ref: str,
        human_actor: str | None = Header(
            default=None,
            alias="X-Pantheon-Human-Actor",
        ),
        idempotency_key: str | None = Header(
            default=None,
            alias="Idempotency-Key",
        ),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(
                status_code=422,
                detail="X-Pantheon-Human-Actor is required",
            )
        try:
            transition = with_connection(
                lambda conn: project_change_variants.select_variant_for_change_candidate(
                    conn,
                    execution_id=execution_result_id,
                    result_id=result_ref,
                    actor=actor,
                    idempotency_key=idempotency_key or "",
                )
            )
        except project_change_variants.ProjectChangeVariantConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except project_change_variants.ProjectChangeVariantError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return {
            "status": "created",
            "selection": transition["selection"],
            "change_candidate": transition["change_candidate"],
            "review_disposition_recorded": True,
            "change_candidate_created": True,
            "variant_selected": True,
            "project_mutated": False,
            "human_decision_recorded": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }
