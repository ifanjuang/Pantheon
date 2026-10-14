"""Bounded Document/Knowledge API and mobile editor surface."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import quote, urlencode

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import decision_requests, knowledge, store
from .contract import ContractError, resolve_source_within
from .policy_gate import HttpPolicyClient, PolicyClient

PREVIEW_TTL_SECONDS = 300
MOBILE_EDITOR = Path(__file__).resolve().parent / "mobile_editor"


class PublishKnowledgeBody(BaseModel):
    knowledge_id: str
    title: str
    family: Literal["referentiels", "responsabilite", "methodologie", "techniques", "reglementations"]
    markdown: str
    source_chunk_refs: list[str]
    created_by: str
    actor_kind: Literal["human", "hermes", "system"] = "human"
    idempotency_key: str
    expected_version: int = 0
    review_status: Literal["generated_unreviewed", "needs_review", "reviewed", "superseded"] = "generated_unreviewed"
    # Only meaningful, and only required, alongside review_status="reviewed":
    # the immutable reference of the human decision the chokepoint validates.
    human_decision_ref: str | None = Field(default=None, min_length=2, max_length=500)


class ReviseKnowledgeBody(BaseModel):
    markdown: str
    expected_version: int = Field(ge=1)
    actor: str
    actor_kind: Literal["human", "hermes", "system"] = "human"
    idempotency_key: str
    review_status: Literal["generated_unreviewed", "needs_review", "reviewed", "superseded"] | None = None


class EditRequestBody(BaseModel):
    request_id: str
    instruction_kind: Literal["rewrite", "expand", "simplify", "verify", "move_to_lot"]
    instruction: str
    base_version: int = Field(ge=1)
    selection_start: int = Field(ge=0)
    selection_end: int = Field(ge=0)
    selected_text: str
    requested_by: str
    idempotency_key: str
    replacement_markdown: str | None = None


class RecompileRequestBody(BaseModel):
    request_id: str
    requested_by: str
    idempotency_key: str


class EditProposalBody(BaseModel):
    replacement_markdown: str
    source_chunk_refs: list[str] | None = None


class ApplyEditBody(BaseModel):
    actor: str
    actor_kind: Literal["human", "hermes", "system"] = "human"
    idempotency_key: str
    # Required when Pantheon policy enforcement is active; ignored otherwise.
    human_decision_ref: str | None = Field(default=None, min_length=2, max_length=500)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def _signature(secret: str, document_id: str, expires: int) -> str:
    payload = f"{document_id}:{expires}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def create_app(
    *,
    connect_fn: Callable = store.connect,
    document_root: str | Path | None = None,
    api_key: str | None = None,
    editor_api_key: str | None = None,
    hermes_api_key: str | None = None,
    public_url: str | None = None,
    policy_client: PolicyClient | None = None,
    policy_enforcement: str | None = None,
) -> FastAPI:
    """Create the API with injectable effects for tests and deployment."""
    app = FastAPI(
        title="Pantheon Document Card API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.connect_fn = connect_fn
    root_value = document_root if document_root is not None else os.getenv("MVP_DOCUMENT_ROOT")
    app.state.document_root = Path(root_value).resolve() if root_value else None
    app.state.api_key = api_key if api_key is not None else os.getenv("MVP_COCKPIT_API_KEY", "")
    app.state.editor_api_key = (
        editor_api_key if editor_api_key is not None else os.getenv("MVP_EDITOR_API_KEY", "")
    )
    app.state.hermes_api_key = (
        hermes_api_key if hermes_api_key is not None else os.getenv("MVP_HERMES_API_KEY", "")
    )
    if (
        app.state.editor_api_key
        and app.state.hermes_api_key
        and hmac.compare_digest(app.state.editor_api_key, app.state.hermes_api_key)
    ):
        raise ValueError("MVP_EDITOR_API_KEY and MVP_HERMES_API_KEY must be distinct")
    app.state.public_url = (
        public_url if public_url is not None else os.getenv("MVP_COCKPIT_PUBLIC_URL", "")
    ).rstrip("/")

    # Same fail-closed arrangement as cockpit_shell.create_cockpit_app: an
    # unconfigured decision point refuses the gated routes below rather than
    # letting them fall back to local-guards-only, and staying disabled is an
    # explicitly named posture, never a default. When cockpit_shell wraps this
    # app it recomputes and overwrites these same two attributes from the same
    # env vars, which is a harmless no-op — this makes the app self-sufficient
    # when create_app is used on its own.
    app.state.policy_enforcement = (
        policy_enforcement
        if policy_enforcement is not None
        else os.getenv("MVP_POLICY_ENFORCEMENT", "required")
    ).strip().lower()
    if app.state.policy_enforcement not in {"required", "disabled"}:
        raise ValueError(
            "MVP_POLICY_ENFORCEMENT must be 'required' or 'disabled'; "
            f"got {app.state.policy_enforcement!r}"
        )
    if policy_client is not None:
        app.state.policy_client = policy_client
    else:
        policy_base_url = os.getenv("MVP_POLICY_API_URL", "").strip()
        policy_api_key = os.getenv("MVP_POLICY_API_KEY", "").strip()
        app.state.policy_client = (
            HttpPolicyClient(policy_base_url, policy_api_key)
            if policy_base_url and policy_api_key
            else None
        )

    def require_api_key(authorization: str | None = Header(default=None)) -> None:
        supplied = _bearer_token(authorization)
        expected = [key for key in (app.state.api_key, app.state.editor_api_key) if key]
        if not expected:
            raise HTTPException(status_code=503, detail="read API key is not configured")
        if not any(hmac.compare_digest(supplied, key) for key in expected):
            raise HTTPException(status_code=401, detail="invalid read API key")

    def require_editor_key(authorization: str | None = Header(default=None)) -> None:
        expected = app.state.editor_api_key
        if not expected:
            raise HTTPException(status_code=503, detail="editor API key is not configured")
        if not hmac.compare_digest(_bearer_token(authorization), expected):
            raise HTTPException(status_code=401, detail="invalid editor API key")

    def require_hermes_key(authorization: str | None = Header(default=None)) -> None:
        expected = app.state.hermes_api_key
        if not expected:
            raise HTTPException(status_code=503, detail="Hermes API key is not configured")
        if not hmac.compare_digest(_bearer_token(authorization), expected):
            raise HTTPException(status_code=401, detail="invalid Hermes API key")

    def require_policy_client() -> PolicyClient | None:
        """Return the decision point, or refuse this consequential Knowledge write."""
        if app.state.policy_enforcement == "disabled":
            return None
        client = app.state.policy_client
        if client is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Pantheon policy decision point is not configured; a "
                    "consequential Knowledge write cannot be admitted. Set "
                    "MVP_POLICY_API_URL and MVP_POLICY_API_KEY, or declare "
                    "MVP_POLICY_ENFORCEMENT=disabled explicitly."
                ),
            )
        return client

    def with_connection(operation):
        conn = app.state.connect_fn()
        try:
            return operation(conn)
        finally:
            conn.close()

    @app.get("/health")
    def health() -> dict:
        editor_enabled = bool(app.state.editor_api_key)
        preview_secret_configured = bool(app.state.api_key or app.state.editor_api_key)
        return {
            "status": "ok",
            "mode": "bounded_read_write" if editor_enabled else "read_only",
            "preview_effect": "none",
            "write_surface": "bounded_document_knowledge_writes" if editor_enabled else "disabled",
            "document_root_configured": app.state.document_root is not None,
            "read_api_key_configured": preview_secret_configured,
            "editor_mode": "bounded_read_write" if editor_enabled else "disabled",
            "signed_knowledge_update_gate": (
                "configured" if bool(getattr(app.state, "update_signing_secret", "")) else "not_configured"
            ),
            "hermes_edit_binding": "polling_ready" if app.state.hermes_api_key else "disabled",
        }

    @app.get("/projects/{parent_project_id}/documents")
    def project_documents(
        parent_project_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        cards = with_connection(
            lambda conn: store.list_document_cards(conn, parent_project_id)
        )
        return {"parent_project_id": parent_project_id, "documents": cards}

    @app.get("/documents/{document_id}")
    def document_card(
        document_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        try:
            return with_connection(lambda conn: store.get_document_card_by_id(conn, document_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/documents/{document_id}/chunks")
    def document_chunks(
        document_id: str,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        content_type: Literal[
            "heading", "paragraph", "list", "table", "figure_caption", "page_fragment"
        ] | None = Query(default=None),
        flagged_only: bool = Query(default=False),
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        try:
            return with_connection(
                lambda conn: store.get_document_chunks(
                    conn,
                    document_id,
                    limit=limit,
                    offset=offset,
                    content_type=content_type,
                    flagged_only=flagged_only,
                )
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/projects/{parent_project_id}/knowledge")
    def project_knowledge(
        parent_project_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        cards = with_connection(
            lambda conn: knowledge.list_knowledge_cards(conn, parent_project_id)
        )
        return {"parent_project_id": parent_project_id, "knowledge": cards}

    @app.get("/knowledge/{knowledge_id}")
    def knowledge_card(
        knowledge_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        try:
            return with_connection(lambda conn: knowledge.get_knowledge_card(conn, knowledge_id))
        except knowledge.KnowledgeNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/knowledge/{knowledge_id}/markdown", response_class=PlainTextResponse)
    def knowledge_markdown(
        knowledge_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> PlainTextResponse:
        try:
            markdown = with_connection(
                lambda conn: knowledge.get_knowledge_markdown(conn, knowledge_id)
            )
        except knowledge.KnowledgeNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PlainTextResponse(
            markdown,
            media_type="text/markdown; charset=utf-8",
            headers={"X-Pantheon-Knowledge": "generated", "Cache-Control": "private, no-cache"},
        )

    @app.get("/knowledge/{knowledge_id}/sources")
    def knowledge_sources(
        knowledge_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        try:
            return with_connection(
                lambda conn: knowledge.get_knowledge_source_state(conn, knowledge_id)
            )
        except knowledge.KnowledgeNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except knowledge.KnowledgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/knowledge/{knowledge_id}/recompile-context")
    def knowledge_recompile_context(
        knowledge_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        try:
            return with_connection(
                lambda conn: knowledge.build_knowledge_recompile_context(
                    conn, knowledge_id
                )
            )
        except knowledge.KnowledgeNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except knowledge.KnowledgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/documents/{document_id}/knowledge-impacts")
    def document_knowledge_impacts(
        document_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        try:
            return with_connection(
                lambda conn: knowledge.list_document_knowledge_impacts(conn, document_id)
            )
        except knowledge.KnowledgeNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except knowledge.KnowledgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def knowledge_write(operation):
        try:
            return with_connection(operation)
        except (knowledge.KnowledgeNotFound, decision_requests.DecisionRecordNotFound) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except decision_requests.DecisionRequestError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except knowledge.KnowledgeGatePolicyUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except (knowledge.StaleKnowledgeWrite, knowledge.IdempotencyConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except knowledge.KnowledgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/documents/{document_id}/knowledge", status_code=201)
    def publish_knowledge(
        document_id: str,
        body: PublishKnowledgeBody,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        # Not a blanket Depends(require_policy_client): most publications are
        # candidate (generated_unreviewed, needs_review) and make no
        # professional claim, so they need no decision point configured at
        # all. Only a request that claims review_status="reviewed" is
        # refused when enforcement is required and none is configured — the
        # same fail-closed posture, narrowed to the one claim it protects.
        policy_client = app.state.policy_client
        if (
            body.review_status == "reviewed"
            and app.state.policy_enforcement == "required"
            and policy_client is None
        ):
            raise HTTPException(
                status_code=503,
                detail=(
                    "Pantheon policy decision point is not configured; "
                    "publishing Knowledge as already reviewed cannot be "
                    "admitted. Set MVP_POLICY_API_URL and MVP_POLICY_API_KEY, "
                    "or declare MVP_POLICY_ENFORCEMENT=disabled explicitly."
                ),
            )
        fields = body.model_dump()
        decision_ref = fields.pop("human_decision_ref")

        def publish(conn):
            canonical_decision = {}
            if body.review_status == "reviewed" and policy_client is not None:
                # Finish the read-only Decision lookup before the Knowledge
                # persistence owner starts its own top-level transaction.
                with conn.transaction():
                    canonical_decision = decision_requests.policy_decision_payload(
                        conn, decision_ref or "", expectation={}
                    )
            return knowledge.publish_knowledge(
                conn,
                document_id=document_id,
                policy_client=policy_client,
                decision_payload=canonical_decision,
                **fields,
            )

        return knowledge_write(publish)

    @app.put("/knowledge/{knowledge_id}")
    def revise_knowledge(
        knowledge_id: str,
        body: ReviseKnowledgeBody,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        """Retired direct write; use the project-scoped signed UPDATE gate."""
        raise HTTPException(
            status_code=410,
            detail=(
                "direct Knowledge revision is retired; use the project-scoped "
                "signed update preview/apply routes"
            ),
        )

    @app.post("/knowledge/{knowledge_id}/recompile-requests", status_code=202)
    def request_knowledge_recompile(
        knowledge_id: str,
        body: RecompileRequestBody,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        return knowledge_write(
            lambda conn: knowledge.create_recompile_request(
                conn, knowledge_id=knowledge_id, **body.model_dump()
            )
        )

    @app.post("/knowledge/{knowledge_id}/edit-requests", status_code=202)
    def request_intelligent_edit(
        knowledge_id: str,
        body: EditRequestBody,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        return knowledge_write(
            lambda conn: knowledge.create_edit_request(
                conn, knowledge_id=knowledge_id, **body.model_dump()
            )
        )

    @app.put("/edit-requests/{request_id}/proposal")
    def complete_intelligent_edit(
        request_id: str,
        body: EditProposalBody,
        _authorized: None = Depends(require_hermes_key),
    ) -> dict:
        return knowledge_write(
            lambda conn: knowledge.complete_edit_request(
                conn,
                request_id=request_id,
                replacement_markdown=body.replacement_markdown,
                replacement_source_chunk_refs=body.source_chunk_refs,
            )
        )

    @app.get("/edit-requests/{request_id}/recompile-context")
    def intelligent_edit_recompile_context(
        request_id: str,
        _authorized: None = Depends(require_hermes_key),
    ) -> dict:
        return knowledge_write(
            lambda conn: knowledge.get_recompile_context_for_request(
                conn, request_id
            )
        )

    @app.get("/edit-requests/{request_id}/recompile-review")
    def intelligent_edit_recompile_review(
        request_id: str,
        _authorized: None = Depends(require_editor_key),
    ) -> dict:
        return knowledge_write(
            lambda conn: knowledge.get_recompile_candidate(conn, request_id)
        )

    @app.get("/edit-requests")
    def intelligent_edit_queue(
        status: Literal[
            "queued_for_hermes", "proposed", "applied", "conflict", "rejected"
        ] = "queued_for_hermes",
        limit: int = 100,
        _authorized: None = Depends(require_hermes_key),
    ) -> dict:
        return {
            "edit_requests": knowledge_write(
                lambda conn: knowledge.list_edit_requests(conn, status=status, limit=limit)
            )
        }

    @app.post("/edit-requests/{request_id}/apply")
    def apply_intelligent_edit(
        request_id: str,
        body: ApplyEditBody,
        _authorized: None = Depends(require_editor_key),
        policy_client: PolicyClient | None = Depends(require_policy_client),
    ) -> dict:
        fields = body.model_dump()
        decision_ref = fields.pop("human_decision_ref")

        def apply_edit(conn):
            canonical_decision = {}
            if policy_client is not None:
                # Keep the canonical Decision read separate from the Knowledge
                # apply transaction. Otherwise psycopg would leave an implicit
                # transaction open and the owner transaction would be a savepoint.
                with conn.transaction():
                    canonical_decision = decision_requests.policy_decision_payload(
                        conn, decision_ref or "", expectation={}
                    )
            return knowledge.apply_edit_request(
                conn,
                request_id=request_id,
                policy_client=policy_client,
                decision_payload=canonical_decision,
                **fields,
            )

        return knowledge_write(apply_edit)

    @app.get("/documents/{document_id}/markdown", response_class=PlainTextResponse)
    def document_markdown(
        document_id: str,
        _authorized: None = Depends(require_api_key),
    ) -> PlainTextResponse:
        try:
            markdown = with_connection(lambda conn: store.get_document_markdown(conn, document_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PlainTextResponse(
            markdown,
            media_type="text/markdown; charset=utf-8",
            headers={"X-Pantheon-Derived": "true", "Cache-Control": "no-store"},
        )

    @app.get("/documents/{document_id}/preview-link")
    def preview_link(
        document_id: str,
        request: Request,
        _authorized: None = Depends(require_api_key),
    ) -> dict:
        if app.state.document_root is None:
            raise HTTPException(status_code=503, detail="document root is not configured")
        try:
            with_connection(lambda conn: store.get_document_source(conn, document_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        secret = app.state.api_key or app.state.editor_api_key
        if not secret:
            raise HTTPException(status_code=503, detail="preview signing secret is not configured")
        expires = int(time.time()) + PREVIEW_TTL_SECONDS
        signature = _signature(secret, document_id, expires)
        base_url = app.state.public_url or str(request.base_url).rstrip("/")
        query = urlencode({"expires": expires, "signature": signature})
        url = f"{base_url}/previews/{quote(document_id, safe='')}/original?{query}"
        return {
            "url": url,
            "expires_at": expires,
            "ttl_seconds": PREVIEW_TTL_SECONDS,
            "disposition": "inline",
        }

    @app.get("/previews/{document_id}/original")
    def original_preview(document_id: str, expires: int, signature: str) -> FileResponse:
        secret = app.state.api_key or app.state.editor_api_key
        now = int(time.time())
        if not secret or expires < now or expires > now + PREVIEW_TTL_SECONDS + 5:
            raise HTTPException(status_code=401, detail="expired preview link")
        expected = _signature(secret, document_id, expires)
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="invalid preview signature")
        if app.state.document_root is None:
            raise HTTPException(status_code=503, detail="document root is not configured")
        try:
            dossier, source_ref = with_connection(
                lambda conn: store.get_document_source(conn, document_id)
            )
            path = resolve_source_within(app.state.document_root, source_ref, dossier)
        except (KeyError, ContractError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not path.is_file():
            raise HTTPException(status_code=404, detail="original document is unavailable")
        media_type = with_connection(
            lambda conn: store.get_document_card_by_id(conn, document_id)["media_type"]
        )
        return FileResponse(
            path,
            media_type=media_type,
            filename=path.name,
            content_disposition_type="inline",
            headers={"Cache-Control": "private, no-store, max-age=0"},
        )

    if MOBILE_EDITOR.is_dir():
        app.mount("/editor", StaticFiles(directory=MOBILE_EDITOR, html=True), name="mobile-editor")

    return app


app = create_app()


def run() -> None:
    """Run the internal cockpit API with uvicorn."""
    import uvicorn

    uvicorn.run(
        "mvp_vertical.cockpit_api:app",
        host=os.getenv("MVP_COCKPIT_HOST", "127.0.0.1"),
        port=int(os.getenv("MVP_COCKPIT_PORT", "8081")),
        reload=False,
    )


if __name__ == "__main__":
    run()
