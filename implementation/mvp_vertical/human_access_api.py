"""OIDC-authenticated, server-scoped human collaboration projection.

The `/me` surface exposes only resources granted to the verified local principal.
It does not replace professional owners and does not make UI visibility an
authorization source.
"""

from __future__ import annotations

import mimetypes
import re
from datetime import datetime
from typing import Callable

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import (
    agency_data,
    document_revision_discussion,
    human_access,
    human_collaboration_projection,
    human_revision_upload,
    project_document_admission,
    project_document_comparison,
    project_document_currentness,
    project_documents,
    source_intake,
    storage_retention,
)


REMOTE_MANAGEABLE_ACTIONS = {
    "project.read",
    "document.read",
    "document.revision.submit",
    "document.comment",
}


class RevisionAdmissionBody(BaseModel):
    source_id: str = Field(min_length=1, max_length=300)
    source_document_id: str = Field(min_length=1, max_length=300)
    source_version: int = Field(ge=1)
    revision_label: str | None = Field(default=None, max_length=200)
    supersedes_version_id: str | None = Field(default=None, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=300)


class RevisionCommentBody(BaseModel):
    body: str = Field(min_length=1, max_length=20000)
    parent_comment_id: str | None = Field(default=None, max_length=300)
    anchor_ref: str | None = Field(default=None, max_length=2000)


class ProjectAccessGrantBody(BaseModel):
    principal_ref: str = Field(min_length=1, max_length=300)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=300)
    action: str = Field(min_length=1, max_length=100)
    valid_until: datetime | None = None
    reason: str | None = Field(default=None, max_length=2000)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def _download_filename(document_id: str, version_seq: int, media_type: str | None) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", document_id).strip("-.") or "document"
    stem = stem[:120]
    extension = mimetypes.guess_extension(media_type or "") or ".bin"
    return f"{stem}-v{version_seq}{extension}"


def install_human_access_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    oidc_verifier: human_access.TokenVerifier | None = None,
    revision_upload_config: human_revision_upload.RevisionUploadConfig | None = None,
    revision_upload_docling=None,
) -> None:
    """Install principal-scoped human collaboration surfaces.

    Existing shared API keys remain a compatibility path on their existing
    internal routes. They are not accepted by this OIDC-only surface.
    """
    if oidc_verifier is None:
        try:
            oidc_verifier = human_access.OidcJwtVerifier.from_env_optional()
        except human_access.AccessConfigurationError as exc:
            raise RuntimeError(str(exc)) from exc
    app.state.oidc_human_verifier = oidc_verifier

    if revision_upload_config is None:
        try:
            revision_upload_config = human_revision_upload.RevisionUploadConfig.from_env_optional()
        except human_revision_upload.RevisionUploadConfigurationError as exc:
            raise RuntimeError(str(exc)) from exc
    app.state.revision_upload_config = revision_upload_config
    app.state.revision_upload_docling = revision_upload_docling

    def require_principal(
        authorization: str | None = Header(default=None),
    ) -> human_access.PrincipalContext:
        token = _bearer_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="OIDC bearer token is required")
        verifier = app.state.oidc_human_verifier
        if verifier is None:
            raise HTTPException(status_code=503, detail="OIDC human access is not configured")
        try:
            claims = verifier.verify(token)
        except human_access.AuthenticationFailed as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except human_access.AccessConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        try:
            return with_connection(
                lambda conn: human_access.resolve_principal_context(conn, claims)
            )
        except human_access.PrincipalNotBound as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except human_access.PrincipalDisabled as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except human_access.HumanAccessError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    def scoped(operation):
        try:
            return with_connection(operation)
        except human_access.AccessDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except (
            agency_data.ProjectNotFound,
            project_documents.ProjectDocumentNotFound,
            project_document_admission.SourceNotAdmissible,
            source_intake.SourceNotFound,
            document_revision_discussion.RevisionDiscussionNotFound,
            document_revision_discussion.RevisionDiscussionScopeError,
            human_access.GrantConflict,
        ) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            project_documents.IdempotencyConflict,
            project_documents.DuplicateCaptureConflict,
            project_documents.SupersessionConflict,
            project_document_admission.SourceAlreadyAdmitted,
            project_document_admission.AdmissionIdempotencyConflict,
            source_intake.SourceIdempotencyConflict,
            human_revision_upload.RevisionUploadConflict,
            storage_retention.StorageBindingConflict,
            storage_retention.RetainedLocationUnavailable,
            storage_retention.RetainedObjectCorrupt,
            document_revision_discussion.RevisionDiscussionIdempotencyConflict,
            document_revision_discussion.CrossRevisionReply,
            project_document_comparison.CrossDocumentComparison,
            project_document_comparison.RevisionStructureUnavailable,
            project_document_comparison.RevisionStructureAmbiguous,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except human_revision_upload.RevisionUploadConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except (
            human_access.HumanAccessError,
            human_revision_upload.RevisionUploadRejected,
            human_revision_upload.RevisionUploadError,
            project_documents.ProjectDocumentError,
            project_document_admission.ProjectDocumentAdmissionError,
            project_document_currentness.ProjectDocumentCurrentnessError,
            project_document_comparison.ProjectDocumentComparisonError,
            source_intake.SourceIntakeError,
            storage_retention.StorageRetentionError,
            document_revision_discussion.RevisionDiscussionError,
        ) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def require_project_read(conn, principal_ref: str, project_id: str) -> None:
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project",
            resource_id=project_id,
            action="project.read",
        )

    def require_document_read(
        conn,
        *,
        principal_ref: str,
        project_id: str,
        document_id: str,
    ) -> dict:
        require_project_read(conn, principal_ref, project_id)
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.read",
        )
        document = project_documents.get_document(conn, document_id)
        if document["parent_project_id"] != project_id:
            raise human_access.AccessDenied("Project Document is outside the requested Project scope")
        return document

    def require_exact_revision(
        conn,
        *,
        principal_ref: str,
        project_id: str,
        document_id: str,
        version_id: str,
    ) -> tuple[dict, dict]:
        document = require_document_read(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            document_id=document_id,
        )
        revision = project_documents.get_revision(conn, version_id)
        if revision["document_id"] != document_id:
            raise project_documents.ProjectDocumentNotFound(
                "Project Document revision is outside the requested document scope"
            )
        return document, revision

    def require_project_access_manager(conn, principal_ref: str, project_id: str) -> None:
        require_project_read(conn, principal_ref, project_id)
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project",
            resource_id=project_id,
            action="project.access.manage",
        )

    @app.get("/me")
    def me(
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        return {
            "principal": principal.as_dict(),
            "authority": dict(human_access.AUTHORITY),
        }

    @app.get("/me/projects")
    def my_projects(
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        projects = scoped(
            lambda conn: human_access.list_accessible_projects(conn, principal.principal_ref)
        )
        return {
            "principal_ref": principal.principal_ref,
            "scope_match": "direct_project_read_grants",
            "projects": projects,
            "authority": dict(human_access.AUTHORITY),
        }

    @app.get("/me/projects/{project_id}")
    def my_project(
        project_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            require_project_read(conn, principal.principal_ref, project_id)
            return agency_data.get_project(conn, project_id)

        project = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project": project,
            "authority": dict(human_access.AUTHORITY),
        }

    @app.get("/me/projects/{project_id}/portal")
    def my_project_portal(
        project_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        return scoped(
            lambda conn: human_collaboration_projection.project_portal_projection(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
            )
        )

    @app.get("/me/projects/{project_id}/access/grants")
    def list_project_access_grants(
        project_id: str,
        include_inactive: bool = True,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            require_project_access_manager(conn, principal.principal_ref, project_id)
            return human_access.list_project_grants(
                conn,
                project_id=project_id,
                include_inactive=include_inactive,
            )

        grants = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "grants": grants,
            "remote_manageable_actions": sorted(REMOTE_MANAGEABLE_ACTIONS),
            "authority": dict(human_access.AUTHORITY),
        }

    @app.post("/me/projects/{project_id}/access/grants", status_code=201)
    def grant_project_access(
        project_id: str,
        body: ProjectAccessGrantBody,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        if body.action not in REMOTE_MANAGEABLE_ACTIONS:
            raise HTTPException(
                status_code=422,
                detail="remote project access administration cannot delegate project.access.manage",
            )

        def operation(conn):
            with conn.transaction():
                require_project_access_manager(conn, principal.principal_ref, project_id)
                if body.resource_type == "project_document" and not human_access.has_access(
                    conn,
                    principal_ref=body.principal_ref,
                    project_id=project_id,
                    resource_type="project",
                    resource_id=project_id,
                    action="project.read",
                ):
                    raise human_access.HumanAccessError(
                        "target principal must already hold active project.read before document grants"
                    )
                return human_access.grant_access(
                    conn,
                    principal_ref=body.principal_ref,
                    project_id=project_id,
                    resource_type=body.resource_type,
                    resource_id=body.resource_id,
                    action=body.action,
                    granted_by=principal.principal_ref,
                    reason=body.reason,
                    valid_until=body.valid_until,
                )

        grant = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "effect": "technical_project_access_granted",
            "grant": grant,
            "authority": dict(human_access.AUTHORITY),
        }

    @app.post("/me/projects/{project_id}/access/grants/{grant_id}/revoke")
    def revoke_project_access(
        project_id: str,
        grant_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            with conn.transaction():
                require_project_access_manager(conn, principal.principal_ref, project_id)
                grant = human_access.get_grant(conn, grant_id)
                if grant["project_id"] != project_id:
                    raise human_access.AccessDenied(
                        "human resource grant is outside the requested Project scope"
                    )
                if grant["action"] == "project.access.manage":
                    raise human_access.HumanAccessError(
                        "remote project access administration cannot revoke project.access.manage"
                    )
                return human_access.revoke_grant(conn, grant_id=grant_id)

        grant = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "effect": "technical_project_access_revoked",
            "grant": grant,
            "authority": dict(human_access.AUTHORITY),
        }

    @app.get("/me/projects/{project_id}/documents")
    def my_project_documents(
        project_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        documents = scoped(
            lambda conn: human_access.list_accessible_documents(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
            )
        )
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "scope_match": "exact_document_read_grants",
            "documents": documents,
            "authority": dict(human_access.AUTHORITY),
        }

    @app.get("/me/projects/{project_id}/documents/{document_id}")
    def my_project_document(
        project_id: str,
        document_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            document = require_document_read(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
            )
            revisions = project_documents.list_revisions(conn, document_id)
            return document, revisions

        document, revisions = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "document": document,
            "revisions": revisions,
            "authority": dict(human_access.AUTHORITY),
        }

    @app.get(
        "/me/projects/{project_id}/documents/{document_id}/currentness/{purpose}"
    )
    def get_project_document_currentness(
        project_id: str,
        document_id: str,
        purpose: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            require_document_read(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
            )
            return project_document_currentness.resolve_currentness(
                conn,
                document_id=document_id,
                purpose=purpose,
            )

        return scoped(operation)

    @app.get(
        "/me/projects/{project_id}/documents/{document_id}/comparison"
    )
    def compare_project_document_revisions(
        project_id: str,
        document_id: str,
        before_version_id: str,
        after_version_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            require_exact_revision(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
                version_id=before_version_id,
            )
            require_exact_revision(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
                version_id=after_version_id,
            )
            return project_document_comparison.compare_revisions(
                conn,
                before_version_id=before_version_id,
                after_version_id=after_version_id,
            )

        return scoped(operation)

    @app.get(
        "/me/projects/{project_id}/documents/{document_id}/revisions/{version_id}/content"
    )
    def get_project_document_revision_content(
        project_id: str,
        document_id: str,
        version_id: str,
        download: bool = False,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ):
        config = app.state.revision_upload_config
        if config is None:
            raise HTTPException(
                status_code=503,
                detail="retained document content is not configured",
            )

        def operation(conn):
            _, revision = require_exact_revision(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
                version_id=version_id,
            )
            try:
                path = storage_retention.resolve_retained_version_path(
                    conn,
                    document_id=revision["source_document_id"],
                    version=int(revision["source_version"]),
                    retention_root=config.retention_root,
                    storage_provider_ref=config.retention_provider_ref,
                    verify=True,
                )
            except storage_retention.StorageRetentionError as exc:
                raise HTTPException(
                    status_code=409,
                    detail="exact retained content is unavailable or failed verification",
                ) from exc
            return {
                "path": path,
                "media_type": revision.get("media_type") or "application/octet-stream",
                "version_seq": int(revision["version_seq"]),
            }

        resolved = scoped(operation)
        return FileResponse(
            path=resolved["path"],
            media_type=resolved["media_type"],
            filename=_download_filename(
                document_id,
                resolved["version_seq"],
                resolved["media_type"],
            ),
            content_disposition_type="attachment" if download else "inline",
            headers={
                "Cache-Control": "private, no-store",
                "X-Pantheon-Revision": version_id,
            },
        )

    @app.get(
        "/me/projects/{project_id}/documents/{document_id}/revisions/{version_id}/comments"
    )
    def list_project_document_revision_comments(
        project_id: str,
        document_id: str,
        version_id: str,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            require_exact_revision(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
                version_id=version_id,
            )
            return document_revision_discussion.list_comments(conn, version_id)

        comments = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "document_id": document_id,
            "document_version_id": version_id,
            "comments": comments,
            "authority": dict(document_revision_discussion.AUTHORITY),
        }

    @app.post(
        "/me/projects/{project_id}/documents/{document_id}/revisions/{version_id}/comments",
        status_code=201,
    )
    def create_project_document_revision_comment(
        project_id: str,
        document_id: str,
        version_id: str,
        body: RevisionCommentBody,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        key = (idempotency_key or "").strip()
        if len(key) < 8:
            raise HTTPException(
                status_code=422,
                detail="Idempotency-Key of at least 8 characters is required",
            )

        def operation(conn):
            with conn.transaction():
                require_exact_revision(
                    conn,
                    principal_ref=principal.principal_ref,
                    project_id=project_id,
                    document_id=document_id,
                    version_id=version_id,
                )
                human_access.require_access(
                    conn,
                    principal_ref=principal.principal_ref,
                    project_id=project_id,
                    resource_type="project_document",
                    resource_id=document_id,
                    action="document.comment",
                )
                return document_revision_discussion.create_comment(
                    conn,
                    document_version_id=version_id,
                    body=body.body,
                    parent_comment_id=body.parent_comment_id,
                    anchor_ref=body.anchor_ref,
                    created_by=principal.principal_ref,
                    idempotency_key=key,
                )

        comment = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "document_id": document_id,
            "document_version_id": version_id,
            "effect": "document_revision_comment_created",
            "comment": comment,
            "authority": dict(document_revision_discussion.AUTHORITY),
        }

    @app.post("/me/projects/{project_id}/documents/{document_id}/revisions", status_code=201)
    def submit_project_document_revision(
        project_id: str,
        document_id: str,
        body: RevisionAdmissionBody,
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        def operation(conn):
            # Access checks are reads and therefore start a psycopg transaction.
            # Own the outer transaction here so the nested A2 owner savepoints
            # cannot be rolled back merely because with_connection closes later.
            with conn.transaction():
                require_document_read(
                    conn,
                    principal_ref=principal.principal_ref,
                    project_id=project_id,
                    document_id=document_id,
                )
                human_access.require_access(
                    conn,
                    principal_ref=principal.principal_ref,
                    project_id=project_id,
                    resource_type="project_document",
                    resource_id=document_id,
                    action="document.revision.submit",
                )
                return project_document_admission.admit_source_as_revision(
                    conn,
                    source_id=body.source_id,
                    document_id=document_id,
                    source_document_id=body.source_document_id,
                    source_version=body.source_version,
                    revision_label=body.revision_label,
                    supersedes_version_id=body.supersedes_version_id,
                    actor=principal.principal_ref,
                    actor_kind="human",
                    idempotency_key=body.idempotency_key,
                )

        result = scoped(operation)
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "effect": "project_document_revision_admission",
            "access_authority": dict(human_access.AUTHORITY),
            "result": result,
        }

    @app.post(
        "/me/projects/{project_id}/documents/{document_id}/revision-uploads",
        status_code=201,
    )
    def upload_project_document_revision(
        project_id: str,
        document_id: str,
        file: UploadFile = File(...),
        revision_label: str | None = Form(default=None),
        supersedes_version_id: str | None = Form(default=None),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        principal: human_access.PrincipalContext = Depends(require_principal),
    ) -> dict:
        config = app.state.revision_upload_config
        if config is None:
            raise HTTPException(
                status_code=503,
                detail="contextual revision upload storage is not configured",
            )
        key = (idempotency_key or "").strip()
        if len(key) < 8:
            raise HTTPException(
                status_code=422,
                detail="Idempotency-Key of at least 8 characters is required",
            )
        result = scoped(
            lambda conn: human_revision_upload.upload_revision(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                document_id=document_id,
                stream=file.file,
                original_filename=file.filename,
                idempotency_key=key,
                config=config,
                revision_label=revision_label,
                supersedes_version_id=supersedes_version_id,
                docling=app.state.revision_upload_docling,
            )
        )
        return {
            "principal_ref": principal.principal_ref,
            "project_id": project_id,
            "document_id": document_id,
            "effect": "contextual_project_document_revision_upload",
            "result": result,
        }
