"""Human attention, HumanResponse and Decision record API.

Decision Request creation and legacy resolution require the editor key and a
human actor. Questions record governed information as HumanResponse; validation,
approval and arbitration record Decisions. A separate authenticated resolution
route composes the same editor gate with the existing OIDC principal verifier;
a verified identity is not by itself decision authority.
"""

from __future__ import annotations

import hmac
from datetime import datetime
from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from . import apu_cross_family, decision_requests, decision_signing, human_access


DecisionType = Literal["question", "validation", "approval", "arbitration"]
Priority = Literal["low", "normal", "high", "urgent"]
ResponseMode = Literal[
    "decision_value", "single_option", "multiple_options", "free_text"
]
DecisionValue = Literal[
    "approve", "refuse", "request_revision", "request_more_evidence"
]
ApprovalLevel = Literal["C0", "C1", "C2", "C3", "C4", "C5"]
IdentityAssurance = Literal["declared"]
RequestStatus = Literal["pending", "resolved", "cancelled"]


class DigestBody(BaseModel):
    algorithm: Literal["sha256"] = "sha256"
    value: str = Field(pattern=r"^[a-f0-9]{64}$")


class DecisionOptionBody(BaseModel):
    option_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    label: str = Field(min_length=1, max_length=1000)
    consequence: str = Field(min_length=1, max_length=10000)
    limitations: list[str] = Field(default_factory=list, max_length=50)


class DecisionScopeRefBody(BaseModel):
    entity_type: Literal["apu_object"]
    entity_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")


class DecisionScopeBody(BaseModel):
    scope_type: str = Field(min_length=1, max_length=200)
    scope_id: str = Field(min_length=1, max_length=500)


class DecisionRequestCreateBody(BaseModel):
    request_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    decision_type: DecisionType
    question: str = Field(min_length=1, max_length=20000)
    priority: Priority = "normal"
    response_mode: ResponseMode
    options: list[DecisionOptionBody] = Field(default_factory=list, max_length=50)
    recommendation_candidate: str | None = Field(default=None, min_length=1)
    blocking: bool = False
    project_ref: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    work_issue_ref: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    scope_refs: list[DecisionScopeRefBody] = Field(default_factory=list, max_length=50)
    conversation_ref: str | None = Field(default=None, min_length=1)
    candidate_ref: str = Field(min_length=1)
    candidate_digest: DigestBody
    approval_level: ApprovalLevel | None = None
    decision_scope: DecisionScopeBody | None = None
    expires_at: datetime | None = None
    evidence_pack_ref: str | None = Field(default=None, min_length=1)
    evidence_pack_digest: DigestBody | None = None
    source_refs: list[str] = Field(default_factory=list, max_length=200)
    evidence_gaps: list[str] = Field(default_factory=list, max_length=200)
    blocked_action: str | None = Field(default=None, max_length=20000)
    next_safe_action: str | None = Field(default=None, max_length=20000)
    decision_surface: str = Field(min_length=1, max_length=500)
    decision_owner: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=200)

    @model_validator(mode="after")
    def validate_request_shape(self):
        if self.blocking and not self.work_issue_ref:
            raise ValueError("blocking Decision Request requires work_issue_ref")
        if self.scope_refs and not self.project_ref:
            raise ValueError("APU-scoped Decision Request requires project_ref")
        if self.decision_type == "question" and self.response_mode == "decision_value":
            raise ValueError("question Decision Requests cannot use decision_value response mode")
        bound_values = (self.approval_level, self.decision_scope, self.expires_at)
        if any(value is not None for value in bound_values) and not all(
            value is not None for value in bound_values
        ):
            raise ValueError(
                "effect-bound Decision Request requires approval_level, decision_scope and expires_at together"
            )
        if self.decision_type == "question" and any(
            value is not None for value in bound_values
        ):
            raise ValueError("question Decision Requests cannot carry effect-bound fields")
        scope_keys = {(scope.entity_type, scope.entity_id) for scope in self.scope_refs}
        if len(scope_keys) != len(self.scope_refs):
            raise ValueError("Decision Request scope_refs must be unique")
        if self.response_mode in {"single_option", "multiple_options"}:
            if len(self.options) < 2:
                raise ValueError("option response mode requires at least two options")
        elif self.options:
            raise ValueError("decision_value and free_text requests cannot carry options")
        option_ids = {option.option_id for option in self.options}
        if len(option_ids) != len(self.options):
            raise ValueError("Decision option identifiers must be unique")
        if self.recommendation_candidate and self.recommendation_candidate not in option_ids:
            raise ValueError("recommendation_candidate must reference one option")
        if bool(self.evidence_pack_ref) != bool(self.evidence_pack_digest):
            raise ValueError("Evidence Pack reference and digest must be supplied together")
        return self


class ResolutionMaterial(BaseModel):
    decision_id: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    response_id: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    decision: DecisionValue | None = None
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    selected_option_ids: list[str] = Field(default_factory=list, max_length=50)
    response_text: str | None = Field(default=None, max_length=20000)
    rationale: str | None = Field(default=None, max_length=20000)


class ResolveDecisionRequestBody(ResolutionMaterial):
    # This editor-key route has no authenticated-principal source. Keep the
    # persisted assurance honest until a real identity provider is composed.
    identity_assurance: IdentityAssurance = "declared"
    authenticated_principal: None = None


class AuthenticatedResolveDecisionRequestBody(ResolutionMaterial):
    pass


class CancelDecisionRequestBody(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    rationale: str = Field(min_length=1, max_length=20000)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def install_decision_request_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_editor_key: Callable,
    require_human_actor: Callable,
) -> None:
    def execute(operation):
        try:
            return with_connection(operation)
        except (
            decision_requests.DecisionRequestNotFound,
            decision_requests.DecisionRecordNotFound,
            decision_requests.HumanResponseNotFound,
        ) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            decision_requests.StaleDecisionRequest,
            decision_requests.DecisionRequestConflict,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except decision_requests.DecisionRequestError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def require_oidc_principal(
        authorization: str | None = Header(default=None),
    ) -> human_access.PrincipalContext:
        token = _bearer_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="OIDC bearer token is required")
        verifier = getattr(app.state, "oidc_human_verifier", None)
        if verifier is None:
            raise HTTPException(status_code=503, detail="OIDC human access is not configured")
        try:
            claims = verifier.verify(token)
            return with_connection(
                lambda conn: human_access.resolve_principal_context(conn, claims)
            )
        except human_access.PrincipalNotBound as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except human_access.PrincipalDisabled as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except human_access.AuthenticationFailed as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except human_access.AccessConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except human_access.HumanAccessError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    def require_oidc_editor_gate(
        x_pantheon_editor_key: str | None = Header(
            default=None,
            alias="X-Pantheon-Editor-Key",
        ),
    ) -> None:
        expected = getattr(app.state, "editor_api_key", None)
        if not expected:
            raise HTTPException(status_code=503, detail="editor API key is not configured")
        supplied = (x_pantheon_editor_key or "").strip()
        if not supplied or not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=401, detail="invalid editor API key")

    @app.post("/decision-requests", status_code=201)
    def create_decision_request(
        body: DecisionRequestCreateBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict[str, Any]:
        values = body.model_dump()
        values["candidate_digest"] = values["candidate_digest"]["value"]
        if values.get("evidence_pack_digest"):
            values["evidence_pack_digest"] = values["evidence_pack_digest"]["value"]
        values["options"] = [option.model_dump() for option in body.options]
        values["scope_refs"] = [scope.model_dump() for scope in body.scope_refs]
        if body.decision_scope is not None:
            values["decision_scope"] = body.decision_scope.model_dump()
        projection = execute(
            lambda conn: apu_cross_family.create_decision_request(
                conn,
                created_by=actor,
                **values,
            )
        )
        return {
            "effect": "decision_request_created",
            "request_is_not_decision": True,
            "runtime_continuation_authorized": False,
            "scope_refs_are_semantic_relations": False,
            **projection,
        }

    @app.get("/decision-requests")
    def list_decision_requests(
        status: RequestStatus | None = "pending",
        project_ref: str | None = None,
        work_issue_ref: str | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        items = execute(
            lambda conn: apu_cross_family.list_requests(
                conn,
                status=status,
                project_ref=project_ref,
                work_issue_ref=work_issue_ref,
                limit=limit,
            )
        )
        return {
            "decision_requests": items,
            "attention_only_when_pending": True,
        }

    @app.get("/agency/projects/{project_id}/decision-requests")
    def list_project_decision_requests(
        project_id: str,
        status: RequestStatus | None = "pending",
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        items = execute(
            lambda conn: apu_cross_family.list_requests(
                conn,
                status=status,
                project_ref=project_id,
                limit=limit,
            )
        )
        return {
            "project_ref": project_id,
            "decision_requests": items,
            "projection_only": True,
        }

    @app.get("/agency/apu-objects/{object_id}/decision-requests")
    def list_apu_object_decision_requests(
        object_id: str,
        status: RequestStatus | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        items = execute(
            lambda conn: apu_cross_family.list_decision_requests_for_apu_object(
                conn,
                object_id=object_id,
                status=status,
                limit=limit,
            )
        )
        return {
            "apu_object_ref": object_id,
            "decision_requests": items,
            "scope_reference_only": True,
            "apu_relation_created": False,
        }

    @app.get("/work/issues/{issue_id}/blocking-decision-request")
    def get_work_issue_blocking_decision(
        issue_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        items = execute(
            lambda conn: apu_cross_family.list_requests(
                conn,
                status="pending",
                work_issue_ref=issue_id,
                limit=100,
            )
        )
        blocking = [
            item
            for item in items
            if item["decision_request"]["blocking"] is True
        ]
        return {
            "work_issue_ref": issue_id,
            "blocking_decision_request": blocking[0] if blocking else None,
            "work_issue_transitioned": False,
        }

    @app.get("/decision-requests/{request_id}")
    def get_decision_request(
        request_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        return execute(lambda conn: apu_cross_family.get_request(conn, request_id))

    @app.post("/decision-requests/{request_id}/resolve")
    def resolve_decision_request(
        request_id: str,
        body: ResolveDecisionRequestBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict[str, Any]:
        values = body.model_dump()

        def resolve_with_scope(conn):
            projection = decision_requests.resolve_request(
                conn,
                request_id=request_id,
                decided_by=actor,
                **values,
            )
            return apu_cross_family.enrich_request_projection(conn, projection)

        projection = execute(resolve_with_scope)
        response_recorded = projection.get("human_response") is not None
        decision_recorded = projection.get("decision_record") is not None
        return {
            "effect": "human_response_recorded" if response_recorded else "decision_recorded",
            "human_response_recorded": response_recorded,
            "decision_recorded": decision_recorded,
            "work_issue_transitioned": False,
            "runtime_continuation_authorized": False,
            "action_executed": False,
            **projection,
        }

    @app.post("/me/decision-requests/{request_id}/resolve")
    def resolve_authenticated_decision_request(
        request_id: str,
        body: AuthenticatedResolveDecisionRequestBody,
        _authorized: None = Depends(require_oidc_editor_gate),
        principal: human_access.PrincipalContext = Depends(require_oidc_principal),
    ) -> dict[str, Any]:
        authenticated_principal = {
            "user_id": principal.principal_ref,
            "identity_provider": principal.issuer,
        }
        if principal.display_name:
            authenticated_principal["display_name"] = principal.display_name

        def resolve_with_scope(conn):
            request_projection = decision_requests.get_request(conn, request_id)
            request = request_projection["decision_request"]
            signature = None
            if (
                request["decision_type"] != "question"
                and body.decision_id
                and request.get("approval_level")
            ):
                signable = {
                    "decision_id": body.decision_id,
                    "decided_by": principal.principal_ref,
                    "approval_level": request["approval_level"],
                    "scope": request["decision_scope"],
                    "object_identity": request["candidate_ref"],
                    "content_digest": request["candidate_digest"]["value"],
                    "expires_at": request["expires_at"],
                }
                secret = decision_signing.issuer_secret(principal.principal_ref)
                if secret is not None:
                    signature = decision_signing.sign_decision(signable, secret)
            projection = decision_requests.resolve_request(
                conn,
                request_id=request_id,
                decided_by=principal.principal_ref,
                identity_assurance="authenticated",
                authenticated_principal=authenticated_principal,
                signature=signature,
                **body.model_dump(),
            )
            return apu_cross_family.enrich_request_projection(conn, projection)

        projection = execute(resolve_with_scope)
        response_recorded = projection.get("human_response") is not None
        decision_recorded = projection.get("decision_record") is not None
        return {
            "effect": "human_response_recorded" if response_recorded else "decision_recorded",
            "identity_assurance": "authenticated",
            "human_response_recorded": response_recorded,
            "decision_recorded": decision_recorded,
            "issuer_signature_recorded": bool(
                projection.get("decision_record", {}).get("signature")
            ),
            "work_issue_transitioned": False,
            "runtime_continuation_authorized": False,
            "action_executed": False,
            **projection,
        }

    @app.post("/decision-requests/{request_id}/cancel")
    def cancel_decision_request(
        request_id: str,
        body: CancelDecisionRequestBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict[str, Any]:
        def cancel_with_scope(conn):
            projection = decision_requests.cancel_request(
                conn,
                request_id=request_id,
                cancelled_by=actor,
                **body.model_dump(),
            )
            return apu_cross_family.enrich_request_projection(conn, projection)

        projection = execute(cancel_with_scope)
        return {
            "effect": "decision_request_cancelled",
            "human_response_recorded": False,
            "decision_recorded": False,
            "runtime_continuation_authorized": False,
            **projection,
        }

    @app.get("/human-responses/{response_id}")
    def get_human_response(
        response_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        return execute(lambda conn: decision_requests.get_response(conn, response_id))

    @app.get("/decisions/{decision_id}")
    def get_decision_record(
        decision_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        return execute(lambda conn: apu_cross_family.get_decision(conn, decision_id))
