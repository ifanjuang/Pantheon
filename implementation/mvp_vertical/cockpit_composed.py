"""Compose the Cockpit with bounded implementation extension routes.

This module mounts implementation extensions. It does not execute rites,
authorize tasks, validate Evidence, close ZEUS or approve reviewed artifacts.
"""

from __future__ import annotations

import hmac
import json
import os
from pathlib import Path

from fastapi import Header, HTTPException

from . import (
    agency_change_candidate_review,
    agency_claims,
    agency_classification,
    agency_data,
    apu_cross_family,
    apu_mapping_reviews,
    apu_owner,
    apu_write_preparation,
    contradictory_review_store,
    decision_requests,
    document_revision_discussion,
    entity_relations,
    execution_results,
    human_access,
    information_projection,
    knowledge_edit_variants,
    project_claim_conflicts,
    project_document_admission,
    project_document_currentness,
    project_documents,
    source_intake,
    storage_retention,
    store,
    work_issue_scopes,
    work_issues,
)
from .agency_classification_api import install_agency_classification_routes
from .apu_cross_family_api import install_apu_cross_family_routes
from .apu_write_api import install_apu_write_routes
from .category_collection_read_api import install_category_collection_read_routes
from .cockpit_shell import create_cockpit_app
from .contradictory_review_api import install_contradictory_review_routes
from .decision_inbox_api import install_decision_inbox_routes
from .decision_request_api import install_decision_request_routes
from .document_structure_api import install_document_structure_routes
from .email_action_api import install_email_action_routes
from .entity_relation_api import install_entity_relation_routes
from .execution_result_api import install_execution_result_routes
from .human_access_api import install_human_access_routes
from .hermes_role_trace_relay import (
    HermesRoleTraceRelay,
    HermesRunsRoleEventSource,
    install_role_trace_routes,
)
from .knowledge_edit_variant_api import install_knowledge_edit_variant_routes
from .project_anatomy_api import install_project_anatomy_routes
from .project_change_variant_api import install_project_change_variant_routes
from .work_issue_scope_api import install_work_issue_scope_routes
from .workspace_collection_read_api import install_workspace_collection_read_routes
from .workspace_qualification_api import install_workspace_qualification_routes


def initialize_composed_schema() -> None:
    """Initialize bounded persistence once, in dependency order."""
    conn = store.connect()
    try:
        conn.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
        # The clean Project Anatomy owner exists before WorkIssue/EntityRef resolvers use it.
        conn.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(source_intake.MIGRATION.read_text(encoding="utf-8"))
        # A owns the professional document/revision seam consumed by B.
        conn.execute(project_documents.MIGRATION.read_text(encoding="utf-8"))
        # CategoryAssignment resolves only already-existing owner identities.
        conn.execute(agency_classification.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(project_document_admission.MIGRATION.read_text(encoding="utf-8"))
        # B4 read projections consume the already-merged A4 currentness owner.
        conn.execute(project_document_currentness.MIGRATION.read_text(encoding="utf-8"))
        # B2 composes the already-adopted A7 storage seam; it does not define storage here.
        conn.execute(storage_retention.MIGRATION.read_text(encoding="utf-8"))
        # B1 depends on Agency Project and professional document identities already existing.
        conn.execute(human_access.MIGRATION.read_text(encoding="utf-8"))
        # B3/B4 extend the same B1 access seam; no second authorization owner is created.
        conn.execute(human_access.ACTION_MIGRATION.read_text(encoding="utf-8"))
        conn.execute(human_access.MANAGEMENT_MIGRATION.read_text(encoding="utf-8"))
        conn.execute(document_revision_discussion.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(information_projection.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(work_issue_scopes.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(decision_requests.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(decision_requests.HUMAN_RESPONSE_MIGRATION.read_text(encoding="utf-8"))
        conn.execute(decision_requests.EFFECT_BINDING_MIGRATION.read_text(encoding="utf-8"))
        conn.execute(entity_relations.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(agency_change_candidate_review.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(contradictory_review_store.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(execution_results.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(execution_results.VARIANT_MIGRATION.read_text(encoding="utf-8"))
        # Claim provenance foreign keys are installed only after execution owners exist.
        conn.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
        # Structured candidate basis provenance extends the existing Claim owner.
        conn.execute(agency_claims.PROVENANCE_MIGRATION.read_text(encoding="utf-8"))
        # Conflict candidates depend only on already-persisted ProjectClaims.
        conn.execute(project_claim_conflicts.MIGRATION.read_text(encoding="utf-8"))
        # Cross-family links depend on DecisionRequest, ProjectClaim and APU owners.
        conn.execute(apu_cross_family.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(knowledge_edit_variants.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(apu_mapping_reviews.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(apu_write_preparation.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(apu_write_preparation.APPLICATION_MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def _role_trace_source_from_env() -> HermesRunsRoleEventSource | None:
    """Build the optional display-only Hermes reader from an explicit pair."""

    base_url = os.getenv("MVP_HERMES_ROLE_TRACE_BASE_URL", "").strip()
    api_key = os.getenv("MVP_HERMES_ROLE_TRACE_API_KEY", "").strip()
    if not base_url and not api_key:
        return None
    if not base_url or not api_key:
        raise ValueError(
            "MVP_HERMES_ROLE_TRACE_BASE_URL and MVP_HERMES_ROLE_TRACE_API_KEY "
            "must be configured together"
        )
    return HermesRunsRoleEventSource(base_url, api_key)


def _email_project_roots_from_env() -> dict[str, str] | None:
    raw = os.getenv("MVP_EMAIL_PROJECT_ROOTS_JSON", "").strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("MVP_EMAIL_PROJECT_ROOTS_JSON must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("MVP_EMAIL_PROJECT_ROOTS_JSON must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def _place_cockpit_static_mount_last(app) -> None:
    """Keep the static `/cockpit` mount behind all composed API extensions."""
    static_mount = next(
        (
            route
            for route in app.router.routes
            if getattr(route, "path", None) == "/cockpit"
            and getattr(route, "name", None) == "cockpit"
        ),
        None,
    )
    if static_mount is None:
        return
    app.router.routes.remove(static_mount)
    app.router.routes.append(static_mount)


def create_composed_cockpit_app(**kwargs):
    """Create the existing Cockpit and mount bounded extensions."""
    initialize_fn = kwargs.pop("initialize_fn", initialize_composed_schema)
    oidc_verifier = kwargs.pop("oidc_verifier", None)
    revision_upload_config = kwargs.pop("revision_upload_config", None)
    revision_upload_docling = kwargs.pop("revision_upload_docling", None)
    workspace_roots = kwargs.pop("workspace_roots", None)
    email_project_catalogue_state_db = kwargs.pop(
        "email_project_catalogue_state_db",
        None,
    )
    if email_project_catalogue_state_db is None:
        raw_state_db = os.getenv("MVP_WORKSPACE_STATE_DB", "").strip()
        email_project_catalogue_state_db = Path(raw_state_db) if raw_state_db else None

    email_project_roots = kwargs.pop("email_project_roots", None)
    if email_project_roots is None:
        email_project_roots = _email_project_roots_from_env()

    email_raw_retention_root = kwargs.pop("email_raw_retention_root", None)
    if email_raw_retention_root is None:
        raw_retention = os.getenv("MVP_EMAIL_RAW_RETENTION_ROOT", "").strip()
        email_raw_retention_root = Path(raw_retention) if raw_retention else None

    email_raw_storage_provider_ref = kwargs.pop(
        "email_raw_storage_provider_ref",
        None,
    )
    if email_raw_storage_provider_ref is None:
        email_raw_storage_provider_ref = os.getenv(
            "MVP_EMAIL_RAW_STORAGE_PROVIDER_REF",
            "",
        ).strip() or None

    role_trace_relay = kwargs.pop("role_trace_relay", None) or HermesRoleTraceRelay()
    role_trace_source = kwargs.pop("role_trace_source", None)
    if role_trace_source is None:
        role_trace_source = _role_trace_source_from_env()
    app = create_cockpit_app(initialize_fn=initialize_fn, **kwargs)
    app.state.role_trace_relay = role_trace_relay
    app.state.role_trace_source_configured = role_trace_source is not None
    if role_trace_source is not None:
        async def attach_registered_run(run_id: str) -> None:
            await role_trace_relay.start_hermes_source(run_id, role_trace_source)

        # The execution callback resolves this observer dynamically only after
        # Pantheon has recorded the exact external run as started.
        app.state.hermes_runtime_start_observer = attach_registered_run

    def with_connection(operation):
        conn = app.state.connect_fn()
        try:
            return operation(conn)
        finally:
            conn.close()

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
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

    def require_human_actor(
        x_pantheon_human_actor: str | None = Header(
            default=None,
            alias="X-Pantheon-Human-Actor",
        ),
    ) -> str:
        if not x_pantheon_human_actor or not x_pantheon_human_actor.strip():
            raise HTTPException(
                status_code=422,
                detail="X-Pantheon-Human-Actor is required for a consequential human write",
            )
        return x_pantheon_human_actor.strip()

    install_human_access_routes(
        app,
        with_connection=with_connection,
        oidc_verifier=oidc_verifier,
        revision_upload_config=revision_upload_config,
        revision_upload_docling=revision_upload_docling,
    )
    install_document_structure_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )
    install_agency_classification_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
    )
    install_category_collection_read_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )
    install_workspace_collection_read_routes(
        app,
        workspace_roots=workspace_roots,
        require_read_key=require_read_key,
    )
    install_workspace_qualification_routes(
        app,
        workspace_roots=app.state.workspace_roots,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
    )
    install_email_action_routes(
        app,
        with_connection=with_connection,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
        project_catalogue_state_db=email_project_catalogue_state_db,
        project_roots=email_project_roots,
        raw_retention_root=email_raw_retention_root,
        raw_storage_provider_ref=email_raw_storage_provider_ref,
    )
    install_role_trace_routes(
        app,
        relay=role_trace_relay,
        require_read_key=require_read_key,
    )
    install_contradictory_review_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_hermes_key=require_hermes_key,
    )
    install_execution_result_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_hermes_key=require_hermes_key,
    )
    install_project_change_variant_routes(
        app,
        with_connection=with_connection,
        require_editor_key=require_editor_key,
    )
    install_knowledge_edit_variant_routes(
        app,
        with_connection=with_connection,
        require_editor_key=require_editor_key,
    )
    install_work_issue_scope_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
    )
    install_decision_request_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
    )
    install_decision_inbox_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )
    install_entity_relation_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
        require_hermes_key=require_hermes_key,
    )
    install_apu_write_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_editor_key=require_editor_key,
    )
    install_apu_cross_family_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )
    install_project_anatomy_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )
    _place_cockpit_static_mount_last(app)
    return app


app = create_composed_cockpit_app()


def run() -> None:
    """Run the composed internal Cockpit API with uvicorn."""
    import uvicorn

    uvicorn.run(
        "mvp_vertical.cockpit_composed:app",
        host=os.getenv("MVP_COCKPIT_HOST", "127.0.0.1"),
        port=int(os.getenv("MVP_COCKPIT_PORT", "8081")),
        reload=False,
    )


if __name__ == "__main__":
    run()
