"""Bounded HTTP projection of the Pantheon policy service.

This internal-network adapter is read-only. It is not an execution runtime,
approval engine, evidence store, memory engine or connector gateway. All policy
meaning lives in :mod:`pantheon_mcp.service`.
"""

from __future__ import annotations

import hmac
import os
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from .http_middleware import BodySizeLimitMiddleware, RequestIdMiddleware
from .repo import RepoNotFound
from .service import POLICY_CONTRACT, PantheonPolicyService

DEFAULT_MAX_BODY_BYTES = 256 * 1024

_SIMPLE_GET_OPERATIONS = (
    ("/meta", "meta"),
    ("/consultation", "consultation_catalog"),
    ("/sources", "list_sources"),
    ("/doctor", "run_doctor"),
)

_SIMPLE_POST_OPERATIONS = (
    ("/policy/requests:classify", "classify_request"),
    ("/policy/decisions:validate", "validate_decision"),
    ("/observations/capabilities:qualify", "qualify_capability_status"),
    ("/candidates/task-contracts:prepare", "prepare_task_contract"),
    ("/candidates/evidence-packs:prepare", "prepare_evidence_pack"),
    ("/validations/passports", "validate_passport"),
    ("/validations/apu-dossiers", "validate_apu_dossier"),
    ("/verifications/install", "verify_install"),
    ("/verifications/observability", "verify_observability"),
    ("/verifications/backup", "verify_backup"),
    ("/verifications/exposure", "verify_exposure"),
    ("/verifications/update", "verify_update"),
)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


def _trace(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    result = dict(payload)
    result.setdefault("request_id", _request_id(request))
    return result


def _compatibility_gap(
    operation: str, replacement: list[str], request: Request
) -> dict[str, Any]:
    return {
        "contract": POLICY_CONTRACT,
        "operation": operation,
        "request_id": _request_id(request),
        "result": "contract_not_defined",
        "authority_effect": "none",
        "authorization_effect": "none",
        "write_effect": False,
        "execution_effect": False,
        "replacement": replacement,
        "message": (
            "The legacy route has no canonical object contract. Use the explicit "
            "operation instead of inferring snapshot or context semantics."
        ),
    }


def create_app(
    *,
    service: PantheonPolicyService | None = None,
    api_key: str | None = None,
    max_body_bytes: int | None = None,
    enable_docs: bool | None = None,
) -> FastAPI:
    """Create the HTTP adapter with injectable dependencies for tests."""
    docs_enabled = (
        _env_flag("PANTHEON_POLICY_ENABLE_DOCS") if enable_docs is None else enable_docs
    )
    body_limit = max_body_bytes or int(
        os.getenv("PANTHEON_POLICY_MAX_BODY_BYTES", str(DEFAULT_MAX_BODY_BYTES))
    )
    app = FastAPI(
        title="Pantheon Policy API",
        version="1.0.0-candidate",
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.state.service = service
    app.state.api_key = (
        api_key if api_key is not None else os.getenv("PANTHEON_POLICY_API_KEY", "")
    )
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=body_limit)
    app.add_middleware(RequestIdMiddleware)

    def get_service() -> PantheonPolicyService:
        if app.state.service is None:
            app.state.service = PantheonPolicyService()
        return app.state.service

    def require_api_key(authorization: str | None = Header(default=None)) -> None:
        expected = app.state.api_key
        if not expected:
            raise HTTPException(
                status_code=503,
                detail="Pantheon policy API key is not configured",
            )
        if not hmac.compare_digest(_bearer_token(authorization), expected):
            raise HTTPException(status_code=401, detail="invalid policy API key")

    @app.exception_handler(RepoNotFound)
    async def repo_not_found(request: Request, exc: RepoNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "contract": POLICY_CONTRACT,
                "request_id": _request_id(request),
                "result": "repository_unavailable",
                "message": str(exc),
                "authority_effect": "none",
                "authorization_effect": "none",
            },
        )

    @app.get("/livez")
    def livez() -> dict[str, Any]:
        return {"status": "alive", "service": "pantheon-policy-api"}

    @app.get("/readyz", response_model=None)
    def readyz() -> Any:
        try:
            state = get_service().repository_state()
        except (RepoNotFound, OSError) as exc:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": str(exc)},
            )
        return {
            "status": "ready",
            "repository_accessible": state["repository_accessible"],
            "repository": state["repository"],
            "warning": "ready != safe; healthy != authorized",
        }

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "mode": "read_only",
            "service": "pantheon-policy-api",
            "warning": "healthy != safe; runtime success != evidence",
        }

    protected = [Depends(require_api_key)]

    def register_get_operation(path: str, method_name: str) -> None:
        def endpoint(request: Request) -> dict[str, Any]:
            method = getattr(get_service(), method_name)
            return _trace(method(), request)

        endpoint.__name__ = f"http_get_{method_name}"
        app.add_api_route(
            path,
            endpoint,
            methods=["GET"],
            dependencies=protected,
        )

    def register_post_operation(path: str, method_name: str) -> None:
        def endpoint(body: dict[str, Any], request: Request) -> dict[str, Any]:
            method = getattr(get_service(), method_name)
            return _trace(method(body), request)

        endpoint.__name__ = f"http_post_{method_name}"
        app.add_api_route(
            path,
            endpoint,
            methods=["POST"],
            dependencies=protected,
        )

    for route, method in _SIMPLE_GET_OPERATIONS:
        register_get_operation(route, method)
    for route, method in _SIMPLE_POST_OPERATIONS:
        register_post_operation(route, method)

    @app.post("/verifications/profiles:load", dependencies=protected)
    def load_verification_profile(
        body: dict[str, Any], request: Request
    ) -> dict[str, Any]:
        payload = get_service().load_verification_preset(body)
        payload["operation"] = "verification.profile.load"
        payload["source_mode"] = "provided_verification_profile_candidate"
        payload["object_term"] = "verification_profile"
        payload["schema_identifier"] = "verification_preset"
        payload["schema_identifier_legacy"] = True
        return _trace(payload, request)

    @app.post(
        "/verifications/presets:load",
        dependencies=protected,
        deprecated=True,
    )
    def legacy_load_verification_preset(
        body: dict[str, Any], request: Request
    ) -> dict[str, Any]:
        payload = get_service().load_verification_preset(body)
        payload["compatibility_route"] = True
        payload["deprecated"] = True
        payload["replacement"] = "/verifications/profiles:load"
        payload["message"] = (
            "Deprecated compatibility alias for the legacy verification_preset "
            "schema identifier; it is not the retired installation preset model."
        )
        return _trace(payload, request)

    @app.get("/repository/state", dependencies=protected)
    def repository_state(request: Request) -> dict[str, Any]:
        payload = dict(get_service().repository_state())
        payload.pop("repo_path", None)
        return _trace(payload, request)

    @app.get("/sources/{key}", dependencies=protected)
    def read_source(key: str, request: Request) -> dict[str, Any]:
        return _trace(get_service().read_doctrine(key), request)

    @app.get("/architecture/{topic}", dependencies=protected)
    def explain_architecture(topic: str, request: Request) -> dict[str, Any]:
        return _trace(get_service().explain_architecture(topic), request)

    @app.post("/policy/preflights:evaluate", dependencies=protected)
    def evaluate_preflight(body: dict[str, Any], request: Request) -> dict[str, Any]:
        return _trace(get_service().evaluate_preflight(body), request)

    @app.post("/policy/external-actions:check", dependencies=protected)
    def check_external_action(body: dict[str, Any], request: Request) -> dict[str, Any]:
        payload = get_service().check_external_action(str(body.get("description", "")))
        return _trace(payload, request)

    @app.post("/context-packs:plan", dependencies=protected)
    def plan_context_pack(body: dict[str, Any], request: Request) -> dict[str, Any]:
        return _trace(get_service().plan_context_pack(body), request)

    @app.post("/context-packs:validate", dependencies=protected)
    def validate_context_pack(body: dict[str, Any], request: Request) -> dict[str, Any]:
        return _trace(get_service().validate_context_pack(body), request)

    @app.post("/domain/approval/classify", dependencies=protected)
    def legacy_approval_classify(
        body: dict[str, Any], request: Request
    ) -> dict[str, Any]:
        response = get_service().classify_request(body)
        response["compatibility_route"] = True
        response["replacement"] = "/policy/requests:classify"
        return _trace(response, request)

    @app.get("/runtime/context-pack", dependencies=protected)
    def legacy_context_pack(request: Request) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content=_compatibility_gap(
                "legacy.context_pack",
                ["POST /context-packs:plan", "POST /context-packs:validate"],
                request,
            ),
        )

    @app.get("/domain/snapshot", dependencies=protected)
    def legacy_snapshot(request: Request) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content=_compatibility_gap(
                "legacy.domain_snapshot",
                [
                    "GET /repository/state",
                    "POST /observations/capabilities:qualify",
                ],
                request,
            ),
        )

    return app


app = create_app()


def run() -> None:
    """Run the internal policy API with uvicorn."""
    import uvicorn

    uvicorn.run(
        "pantheon_mcp.http_api:app",
        host=os.getenv("PANTHEON_POLICY_HOST", "0.0.0.0"),
        port=int(os.getenv("PANTHEON_POLICY_PORT", "8000")),
        reload=False,
        access_log=_env_flag("PANTHEON_POLICY_ACCESS_LOG", False),
    )


if __name__ == "__main__":
    run()
