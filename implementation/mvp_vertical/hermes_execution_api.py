"""API boundary for execution admission and external Hermes runtime callbacks.

The Cockpit may admit/revoke one exact handoff. An external Hermes-side binding may
reserve one immutable launch snapshot, then Hermes may report its own start/return
and read only the exact admitted context while that run is active.

No pending-work listing, scheduler, queue, Pantheon-side dispatch endpoint, global
Agency Data access or provider routing exists here.
"""

from __future__ import annotations

import hmac
import inspect
from typing import Any, Callable, Literal

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import (
    hermes_active_context,
    hermes_execution,
    hermes_launch_context,
    hermes_result_candidate,
    hermes_runtime_return,
    hermes_scoped_context,
    work_issues,
)
from .app_lifecycle import install_post_start_initializer


class ExecutionAdmissionBody(BaseModel):
    ttl_seconds: int = Field(ge=hermes_execution.MIN_TTL_SECONDS, le=hermes_execution.MAX_TTL_SECONDS)
    idempotency_key: str = Field(min_length=8, max_length=200)


class ExecutionRevocationBody(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class HermesLaunchReservationBody(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)


class HermesEphemeralContextMaterializeBody(BaseModel):
    launch_reservation_id: str = Field(min_length=1, max_length=300)


class HermesRuntimeStartBody(BaseModel):
    run_id: str = Field(min_length=1, max_length=300)
    expected_issue_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    launch_reservation_id: str | None = Field(default=None, min_length=1, max_length=300)


class HermesNormalizedReturn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["result_candidate", "partial", "failed", "capability_gap"]
    summary: str = Field(min_length=1, max_length=20_000)
    trace_refs: list[str] = Field(min_length=1, max_length=500)
    result_refs: list[str] = Field(default_factory=list, max_length=500)
    evidence_candidate_refs: list[str] = Field(default_factory=list, max_length=500)
    execution_trace_summary: dict[str, Any] | None = None


class HermesResultCandidateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_type: str = Field(min_length=1, max_length=200)
    candidate_payload: dict[str, Any] = Field(default_factory=dict)
    confidence_note: str | None = Field(default=None, max_length=10_000)
    known_limits: list[str] = Field(default_factory=list, max_length=500)
    open_questions: list[str] = Field(default_factory=list, max_length=500)
    source_refs: list[str] = Field(default_factory=list, max_length=500)
    missing_evidence: list[str] = Field(default_factory=list, max_length=500)


class HermesRuntimeReturnBody(BaseModel):
    normalized_return: HermesNormalizedReturn
    result_candidate: HermesResultCandidateBody | None = None
    execution_result: dict[str, Any] | None = None
    expected_issue_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def install_hermes_execution_routes(
    app: FastAPI,
    *,
    require_editor_key: Callable,
    require_human_actor: Callable,
    with_connection: Callable | None = None,
) -> None:
    def use_connection(operation):
        if with_connection is not None:
            return with_connection(operation)
        conn = app.state.connect_fn()
        try:
            return operation(conn)
        finally:
            conn.close()

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
                detail="X-Pantheon-Hermes-Actor is required for a Hermes runtime request",
            )
        return x_pantheon_hermes_actor.strip()

    async def notify_runtime_start(run_id: str) -> None:
        """Notify an optional display observer after canonical start recording."""

        observer = getattr(app.state, "hermes_runtime_start_observer", None)
        if observer is None:
            return
        try:
            outcome = observer(run_id)
            if inspect.isawaitable(outcome):
                await outcome
        except Exception as exc:
            # Presentation failure must never roll back or reinterpret the
            # already-recorded external runtime start.
            app.state.hermes_runtime_start_observer_error = type(exc).__name__

    connect_fn = getattr(app.state, "connect_fn", None)
    if (
        getattr(connect_fn, "__module__", "") == "mvp_vertical.cockpit_shell"
        and getattr(connect_fn, "__name__", "") == "connect_cockpit"
    ):
        def initialize_execution_admission_schema() -> None:
            conn = connect_fn()
            try:
                for migration in hermes_execution.MIGRATIONS:
                    conn.execute(migration.read_text(encoding="utf-8"))
                conn.execute(hermes_result_candidate.MIGRATION.read_text(encoding="utf-8"))
                conn.commit()
            finally:
                conn.close()

        install_post_start_initializer(app, initialize_execution_admission_schema)

    @app.post("/cockpit/hermes-handoffs/{handoff_id}/admissions", status_code=201)
    def admit_hermes_handoff(
        handoff_id: str,
        body: ExecutionAdmissionBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_execution.admit_handoff(
                    conn,
                    handoff_id=handoff_id,
                    actor=actor,
                    idempotency_key=body.idempotency_key,
                    ttl_seconds=body.ttl_seconds,
                )
            )
        except hermes_execution.AdmissionNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_execution.AdmissionConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_execution.HermesExecutionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/cockpit/hermes-execution-admissions/{admission_id}")
    def get_cockpit_admission(
        admission_id: str,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        try:
            return use_connection(lambda conn: hermes_execution.get_admission(conn, admission_id))
        except hermes_execution.AdmissionNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/cockpit/hermes-execution-admissions/{admission_id}/revocations", status_code=201)
    def revoke_hermes_admission(
        admission_id: str,
        body: ExecutionRevocationBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_execution.revoke_admission(
                    conn,
                    admission_id=admission_id,
                    actor=actor,
                    reason=body.reason,
                    idempotency_key=body.idempotency_key,
                )
            )
        except hermes_execution.AdmissionNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_execution.AdmissionConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_execution.HermesExecutionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/hermes/execution-admissions/{admission_id}")
    def get_hermes_execution_envelope(
        admission_id: str,
        _authorized: None = Depends(require_hermes_key),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_execution.get_execution_envelope(conn, admission_id)
            )
        except hermes_execution.AdmissionNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_execution.AdmissionConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post(
        "/hermes/execution-admissions/{admission_id}/launch-reservations",
        status_code=201,
    )
    def reserve_hermes_runtime_launch(
        admission_id: str,
        body: HermesLaunchReservationBody,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_launch_context.reserve_launch(
                    conn,
                    admission_id=admission_id,
                    actor=actor,
                    idempotency_key=body.idempotency_key,
                )
            )
        except hermes_launch_context.LaunchReservationNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_launch_context.LaunchReservationConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_launch_context.LaunchContextTooLarge as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except hermes_launch_context.HermesLaunchContextError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post(
        "/hermes/execution-admissions/{admission_id}/ephemeral-context/materialize",
        status_code=200,
    )
    def materialize_hermes_ephemeral_context(
        admission_id: str,
        body: HermesEphemeralContextMaterializeBody,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        del actor  # actor authenticates the external binding; materialization itself is read-only.
        try:
            return use_connection(
                lambda conn: hermes_launch_context.materialize_ephemeral_context(
                    conn,
                    admission_id=admission_id,
                    launch_reservation_id=body.launch_reservation_id,
                )
            )
        except hermes_launch_context.LaunchReservationNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_launch_context.LaunchReservationConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_launch_context.HermesLaunchContextError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/hermes/execution-admissions/{admission_id}/runs/start", status_code=201)
    def record_hermes_runtime_start(
        admission_id: str,
        body: HermesRuntimeStartBody,
        background_tasks: BackgroundTasks,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            started = use_connection(
                lambda conn: hermes_execution.record_external_runtime_start(
                    conn,
                    admission_id=admission_id,
                    run_id=body.run_id,
                    actor=actor,
                    expected_issue_version=body.expected_issue_version,
                    idempotency_key=body.idempotency_key,
                    launch_reservation_id=body.launch_reservation_id,
                )
            )
            if started.get("runtime_start_recorded") is True:
                background_tasks.add_task(notify_runtime_start, body.run_id)
            return started
        except hermes_execution.AdmissionNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            hermes_execution.AdmissionConflict,
            hermes_execution.RuntimeStartConflict,
            work_issues.StaleWrite,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (hermes_execution.HermesExecutionError, work_issues.WorkIssueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/hermes/execution-admissions/{admission_id}/runs/{run_id}/context")
    def get_hermes_scoped_context_manifest(
        admission_id: str,
        run_id: str,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_scoped_context.get_context_manifest(
                    conn,
                    admission_id=admission_id,
                    run_id=run_id,
                    actor=actor,
                )
            )
        except hermes_scoped_context.ScopedContextNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_scoped_context.ScopedContextConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_scoped_context.HermesScopedContextError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get(
        "/hermes/execution-admissions/{admission_id}/runs/{run_id}/context/entities/{entity_type}/{entity_id}"
    )
    def get_hermes_scoped_context_entity(
        admission_id: str,
        run_id: str,
        entity_type: str,
        entity_id: str,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_scoped_context.get_context_entity(
                    conn,
                    admission_id=admission_id,
                    run_id=run_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    actor=actor,
                )
            )
        except hermes_scoped_context.ScopedContextNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except hermes_scoped_context.ScopedContextConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_scoped_context.ScopedContextContentTooLarge as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except hermes_scoped_context.HermesScopedContextError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/hermes/execution-admissions/{admission_id}/active-context")
    def get_hermes_active_context_manifest(
        admission_id: str,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_active_context.get_active_context_manifest(
                    conn,
                    admission_id=admission_id,
                    actor=actor,
                )
            )
        except hermes_active_context.ActiveContextNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            hermes_active_context.ActiveContextConflict,
            hermes_scoped_context.ScopedContextConflict,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_scoped_context.HermesScopedContextError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get(
        "/hermes/execution-admissions/{admission_id}/active-context/entities/{entity_type}/{entity_id}"
    )
    def get_hermes_active_context_entity(
        admission_id: str,
        entity_type: str,
        entity_id: str,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_active_context.get_active_context_entity(
                    conn,
                    admission_id=admission_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    actor=actor,
                )
            )
        except hermes_active_context.ActiveContextNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            hermes_active_context.ActiveContextConflict,
            hermes_scoped_context.ScopedContextConflict,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_scoped_context.ScopedContextContentTooLarge as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except hermes_scoped_context.HermesScopedContextError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/hermes/execution-admissions/{admission_id}/runs/{run_id}/return", status_code=200)
    def record_hermes_runtime_return(
        admission_id: str,
        run_id: str,
        body: HermesRuntimeReturnBody,
        _authorized: None = Depends(require_hermes_key),
        actor: str = Depends(require_hermes_actor),
    ) -> dict:
        try:
            return use_connection(
                lambda conn: hermes_runtime_return.record_external_runtime_return(
                    conn,
                    admission_id=admission_id,
                    run_id=run_id,
                    normalized_return=body.normalized_return.model_dump(exclude_none=True),
                    result_candidate=(
                        body.result_candidate.model_dump()
                        if body.result_candidate is not None
                        else None
                    ),
                    execution_result=body.execution_result,
                    actor=actor,
                    expected_issue_version=body.expected_issue_version,
                    idempotency_key=body.idempotency_key,
                )
            )
        except hermes_runtime_return.HermesRuntimeReturnConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_runtime_return.HermesRuntimeReturnError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
