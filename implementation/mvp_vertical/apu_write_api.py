"""Bounded API routes for APU write preparation, authorization and application."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, Header, HTTPException

from . import apu_write_preparation, execution_results


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, apu_write_preparation.ApuWritePreparationNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, execution_results.ExecutionResultConflict):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, apu_write_preparation.ApuWritePreparationError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="APU write operation failed")


def install_apu_write_routes(
    app,
    *,
    with_connection: Callable[[Callable[..., Any]], Any],
    require_read_key,
    require_editor_key,
) -> None:
    @app.post(
        "/execution-results/{execution_result_id}/results/{result_ref}/mappings/{mapping_ref}/prepare-apu-write",
        dependencies=[Depends(require_editor_key)],
    )
    def prepare_apu_write(
        execution_result_id: str,
        result_ref: str,
        mapping_ref: str,
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(status_code=422, detail="X-Pantheon-Human-Actor is required")
        try:
            command = with_connection(
                lambda conn: apu_write_preparation.prepare_write_command(
                    conn,
                    execution_result_id=execution_result_id,
                    result_ref=result_ref,
                    mapping_ref=mapping_ref,
                    prepared_by=actor,
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate(exc) from exc
        return {
            "status": "prepared",
            "command": command,
            "write_command_prepared": True,
            "application_authorized": False,
            "apu_mutated": False,
            "stable_identity_confirmed": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.get("/apu-write-commands/{command_id}", dependencies=[Depends(require_read_key)])
    def read_apu_write_command(command_id: str) -> dict[str, Any]:
        try:
            return with_connection(
                lambda conn: apu_write_preparation.get_write_command(conn, command_id)
            )
        except Exception as exc:
            raise _translate(exc) from exc

    @app.post(
        "/apu-write-commands/{command_id}/authorizations",
        dependencies=[Depends(require_editor_key)],
    )
    def authorize_apu_write(
        command_id: str,
        payload: dict[str, Any],
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(status_code=422, detail="X-Pantheon-Human-Actor is required")
        try:
            authorization = with_connection(
                lambda conn: apu_write_preparation.append_authorization(
                    conn,
                    command_id=command_id,
                    action=str(payload.get("action") or ""),
                    note=payload.get("note"),
                    authorized_by=actor,
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate(exc) from exc
        allowed = authorization["action"] == "authorize_application"
        return {
            "status": "recorded",
            "authorization": authorization,
            "application_authorized": allowed,
            "command_applied": False,
            "apu_mutated": False,
            "stable_identity_confirmed": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "external_effect_authorized": False,
        }

    @app.get(
        "/apu-write-commands/{command_id}/authorizations",
        dependencies=[Depends(require_read_key)],
    )
    def read_apu_write_authorizations(command_id: str) -> dict[str, Any]:
        try:
            items = with_connection(
                lambda conn: apu_write_preparation.list_authorizations(conn, command_id)
            )
        except Exception as exc:
            raise _translate(exc) from exc
        return {
            "command_id": command_id,
            "items": items,
            "count": len(items),
            "current_authorization": items[-1] if items else None,
        }

    @app.post(
        "/apu-write-commands/{command_id}/apply",
        dependencies=[Depends(require_editor_key)],
    )
    def apply_apu_write(
        command_id: str,
        human_actor: str | None = Header(default=None, alias="X-Pantheon-Human-Actor"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        actor = (human_actor or "").strip()
        if not actor:
            raise HTTPException(status_code=422, detail="X-Pantheon-Human-Actor is required")
        try:
            receipt = with_connection(
                lambda conn: apu_write_preparation.apply_authorized_write_command(
                    conn,
                    command_id=command_id,
                    applied_by=actor,
                    idempotency_key=idempotency_key or "",
                )
            )
        except Exception as exc:
            raise _translate(exc) from exc
        return {
            "status": receipt["status"],
            "receipt": receipt,
            "application_authorized": True,
            "command_applied": True,
            "apu_mutated": True,
            "stable_identity_confirmed": False,
            "evidence_admitted": False,
            "memory_promoted": False,
            "work_issue_closed": False,
            "decision_request_resolved": False,
            "project_claim_mutated": False,
            "external_effect_authorized": False,
        }
