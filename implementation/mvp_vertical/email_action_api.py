"""Bounded Gmail/Workspace email action HTTP seam.

Exactly two user intents exist here:
- ARCHIVE: consequential persistence after server-side destination validation;
- ASK_HERMES: create bounded ephemeral context and prepare the existing handoff.

This module does not dispatch Hermes directly and never accepts a filesystem path
from the client.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal, Mapping

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import (
    email_action_adapter,
    hermes_ephemeral_context,
    source_intake,
    storage_retention,
    workspace_project_catalogue,
)


MAX_ACTION_MESSAGES = 20
MAX_RAW_BASE64_CHARS = 30 * 1024 * 1024


class HermesRootEntityBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1, max_length=500)
    entity_type: str = Field(min_length=1, max_length=200)


class EmailWorkingMessageBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_account_ref: str = Field(min_length=1, max_length=500)
    gmail_message_id: str = Field(min_length=1, max_length=500)
    gmail_thread_id: str = Field(min_length=1, max_length=500)
    raw_rfc822_base64url: str = Field(min_length=1, max_length=MAX_RAW_BASE64_CHARS)
    client_raw_sha256: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
    )
    received_at: datetime
    destination_project: str | None = Field(default=None, max_length=300)


class EmailActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Literal["ARCHIVE", "ASK_HERMES"]
    messages: list[EmailWorkingMessageBody] = Field(
        min_length=1,
        max_length=MAX_ACTION_MESSAGES,
    )
    question: str | None = Field(default=None, max_length=20_000)
    allow_archived_write: bool = False
    hermes_root_entity: HermesRootEntityBody | None = None


def _normalize_messages(
    messages: list[EmailWorkingMessageBody],
) -> list[email_action_adapter.NormalizedEmail]:
    output: list[email_action_adapter.NormalizedEmail] = []
    for item in messages:
        output.append(
            email_action_adapter.normalize_message(
                provider_account_ref=item.provider_account_ref,
                gmail_message_id=item.gmail_message_id,
                gmail_thread_id=item.gmail_thread_id,
                raw_rfc822_base64url=item.raw_rfc822_base64url,
                client_raw_sha256=item.client_raw_sha256,
            )
        )
    return output


def _raise_email_error(exc: Exception) -> None:
    if isinstance(exc, email_action_adapter.EmailTooLarge):
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    if isinstance(exc, email_action_adapter.RawEmailChecksumMismatch):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(
        exc,
        (
            email_action_adapter.RawEmailDecodeError,
            email_action_adapter.MimeLimitExceeded,
            email_action_adapter.EmailActionError,
        ),
    ):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise exc


def install_email_action_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_editor_key: Callable,
    require_human_actor: Callable,
    project_catalogue_state_db: Path | None = None,
    project_roots: Mapping[str, str | Path] | None = None,
    raw_retention_root: Path | None = None,
    raw_storage_provider_ref: str | None = None,
) -> None:
    """Install the two-intent email action seam."""

    @app.post("/cockpit/email-actions")
    def email_action(
        body: EmailActionBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict[str, Any]:
        try:
            normalized = _normalize_messages(body.messages)
        except Exception as exc:
            _raise_email_error(exc)
            raise AssertionError("unreachable")

        if body.intent == "ASK_HERMES":
            question = str(body.question or "").strip()
            if not question:
                raise HTTPException(
                    status_code=422,
                    detail="ASK_HERMES requires a non-empty question/instruction",
                )
            try:
                lease = email_action_adapter.create_ask_lease(
                    normalized,
                    actor=actor,
                )
            except hermes_ephemeral_context.EphemeralContextTooLarge as exc:
                raise HTTPException(status_code=413, detail=str(exc)) from exc
            except hermes_ephemeral_context.EphemeralContextError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

            lease_ref = {
                "lease_ref": lease["lease_ref"],
                "lease_digest": lease["lease_digest"],
            }
            if body.hermes_root_entity is None:
                return {
                    "intent": "ASK_HERMES",
                    "archive_performed": False,
                    "lease": lease,
                    "handoff_status": "governed_root_required",
                    "required_next": (
                        "select or resolve an explicit governed Hermes root; "
                        "AFFAIRES folder routing is not Project identity"
                    ),
                    "hermes_dispatched": False,
                }

            return {
                "intent": "ASK_HERMES",
                "archive_performed": False,
                "lease": lease,
                "handoff_status": "preview_request_ready",
                "handoff_preview_request": {
                    "question": question,
                    "card_context_envelope": {
                        "root_entity": body.hermes_root_entity.model_dump(),
                        "descendants": [],
                        "source_refs": [],
                        "explicit_additions": [],
                        "explicit_exclusions": [],
                        "scope_widened_implicitly": False,
                    },
                    "selected_context": [],
                    "ephemeral_context_leases": [lease_ref],
                    "include_declared_descendants": False,
                },
                "handoff_preview_endpoint": "/cockpit/hermes-handoffs/preview",
                "hermes_dispatched": False,
            }

        # ARCHIVE
        if len(body.messages) != 1:
            raise HTTPException(
                status_code=422,
                detail=(
                    "ARCHIVE currently accepts exactly one working email per request; "
                    "the Workspace client may submit selected threads independently"
                ),
            )
        message_body = body.messages[0]
        project_name = str(message_body.destination_project or "").strip()
        if not project_name:
            raise HTTPException(
                status_code=422,
                detail="ARCHIVE requires destination_project",
            )
        if (
            project_catalogue_state_db is None
            or not project_roots
            or raw_retention_root is None
            or not str(raw_storage_provider_ref or "").strip()
        ):
            raise HTTPException(
                status_code=503,
                detail="email archive backend is not fully configured",
            )

        try:
            catalogue = workspace_project_catalogue.load_project_catalogue(
                project_catalogue_state_db
            )
            destination = workspace_project_catalogue.resolve_project_destination(
                catalogue,
                project_name=project_name,
                root_paths=project_roots,
                allow_archived_write=body.allow_archived_write,
            )
        except workspace_project_catalogue.ArchivedProjectWriteRequiresConfirmation as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_project_catalogue.ProjectDestinationConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_project_catalogue.ProjectDestinationNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except workspace_project_catalogue.ProjectCatalogueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        try:
            result = with_connection(
                lambda conn: email_action_adapter.archive_email_to_authorized_root(
                    conn,
                    normalized[0],
                    destination_root=destination["path"],
                    retention_root=raw_retention_root,
                    storage_provider_ref=str(raw_storage_provider_ref),
                    actor=actor,
                    received_at=message_body.received_at,
                )
            )
        except email_action_adapter.ArchiveCollision as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except email_action_adapter.EmailActionError as exc:
            _raise_email_error(exc)
            raise AssertionError("unreachable")
        except source_intake.SourceIntakeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except storage_retention.StorageRetentionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return {
            **result,
            "destination": {
                "name": destination["name"],
                "state": destination["state"],
                "root_kind": destination["root_kind"],
                "relative_root": destination["relative_root"],
                "governed_project_identity_asserted": False,
            },
        }
