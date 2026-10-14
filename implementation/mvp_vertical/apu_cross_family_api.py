"""Read-only cross-family projections for stable APU object references."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException

from . import agency_claims, apu_cross_family, decision_requests


def install_apu_cross_family_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
) -> None:
    def execute(operation):
        try:
            return with_connection(operation)
        except agency_claims.ClaimNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            apu_cross_family.ApuCrossFamilyError,
            decision_requests.DecisionRequestError,
            agency_claims.AgencyClaimError,
        ) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/agency/apu-objects/{object_id}/project-claims")
    def list_apu_object_project_claims(
        object_id: str,
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        items = execute(
            lambda conn: apu_cross_family.list_project_claims_for_apu_object(
                conn,
                object_id=object_id,
                limit=limit,
            )
        )
        return {
            "apu_object_ref": object_id,
            "project_claims": items,
            "backing_reference_only": True,
            "apu_relation_created": False,
            "claim_authority_transferred": False,
        }
