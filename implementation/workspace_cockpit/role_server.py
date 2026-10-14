#!/usr/bin/env python3
"""Credentialed, transient Role relay sidecar for the filesystem Cockpit."""

from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException

from mvp_vertical.hermes_role_trace_relay import (
    HermesRoleTraceRelay,
    HermesRoleTraceRelayError,
    HermesRunsRoleEventSource,
    install_role_trace_routes,
)


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"required configuration is missing: {name}")
    return value


def _token(authorization: str | None) -> str:
    return authorization.removeprefix("Bearer ").strip() if authorization and authorization.startswith("Bearer ") else ""


def create_app(
    *,
    source: HermesRunsRoleEventSource | None = None,
    relay: HermesRoleTraceRelay | None = None,
    attach_key: str | None = None,
    read_key: str | None = None,
) -> FastAPI:
    source = source or HermesRunsRoleEventSource(
        _required("HERMES_ROLE_TRACE_BASE_URL"),
        _required("HERMES_ROLE_TRACE_API_KEY"),
    )
    relay = relay or HermesRoleTraceRelay()
    attach_key = attach_key if attach_key is not None else _required("ROLE_TRACE_ATTACH_KEY")
    read_key = read_key if read_key is not None else _required("ROLE_TRACE_READ_KEY")
    app = FastAPI(title="Pantheon transient Role relay", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.latest_run_id = None

    def require(expected: str, authorization: str | None) -> None:
        if not hmac.compare_digest(_token(authorization), expected):
            raise HTTPException(status_code=401, detail="invalid Role relay key")

    def require_attach(authorization: str | None = Header(default=None)) -> None:
        require(attach_key, authorization)

    def require_read(authorization: str | None = Header(default=None)) -> None:
        require(read_key, authorization)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "persistence": "none", "authority_effect": "none"}

    @app.post("/internal/role-traces/{run_id}/attach", status_code=202)
    async def attach(run_id: str, _authorized: None = Depends(require_attach)) -> dict:
        try:
            attached = await relay.start_hermes_source(run_id, source)
        except HermesRoleTraceRelayError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        app.state.latest_run_id = run_id
        return {"run_id": run_id, "attached": attached, "authority_effect": "none"}

    @app.get("/internal/role-traces/latest")
    async def latest(_authorized: None = Depends(require_read)) -> dict:
        run_id = app.state.latest_run_id
        if not run_id:
            raise HTTPException(status_code=404, detail="no Role trace has been attached")
        return relay.snapshot(run_id)

    install_role_trace_routes(
        app,
        relay=relay,
        require_read_key=require_read,
        route_prefix="/internal",
    )
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.getenv("ROLE_TRACE_PORT", "8190")))
