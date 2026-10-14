"""Cockpit APIs for explicit Workspace qualification, dialogue and bounded notes."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import (
    hermes_handoff_store,
    workspace_dialogue,
    workspace_human_note,
    workspace_markdown_write,
    workspace_qualification,
)


class WorkspaceQualificationPreviewBody(BaseModel):
    project_id: str = Field(min_length=1, max_length=300)
    workspace_ref: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(min_length=1, max_length=4096)
    prepare_markdown: bool = False
    user_instruction: str | None = Field(default=None, max_length=2_000)


class WorkspaceQualificationSubmitBody(WorkspaceQualificationPreviewBody):
    expected_preview_digest: str = Field(min_length=32, max_length=128)
    expected_task_contract_ref: str = Field(min_length=16, max_length=200)
    expected_context_pack_ref: str = Field(min_length=16, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)


class WorkspaceDialogueReadBody(BaseModel):
    project_id: str = Field(min_length=1, max_length=300)
    workspace_ref: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(min_length=1, max_length=4096)
    handoff_id: str = Field(min_length=8, max_length=200)


class WorkspaceReworkPreviewBody(BaseModel):
    project_id: str = Field(min_length=1, max_length=300)
    workspace_ref: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(min_length=1, max_length=4096)
    prior_handoff_id: str = Field(min_length=8, max_length=200)
    instruction: str = Field(min_length=3, max_length=2_000)


class WorkspaceReworkSubmitBody(WorkspaceReworkPreviewBody):
    expected_preview_digest: str = Field(min_length=32, max_length=128)
    expected_task_contract_ref: str = Field(min_length=16, max_length=200)
    expected_context_pack_ref: str = Field(min_length=16, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)


class WorkspaceHumanNoteReadBody(BaseModel):
    workspace_ref: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(min_length=1, max_length=4096)


class WorkspaceHumanNoteWriteBody(WorkspaceHumanNoteReadBody):
    human_note: str = Field(max_length=20_000)
    expected_manifest_digest: str | None = Field(default=None, min_length=64, max_length=64)


class WorkspaceMarkdownReadBody(BaseModel):
    workspace_ref: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(min_length=1, max_length=4096)


class WorkspaceMarkdownCreateBody(WorkspaceMarkdownReadBody):
    content: str = Field(max_length=500_000)


class WorkspaceMarkdownPatchBody(WorkspaceMarkdownReadBody):
    expected_digest: str = Field(min_length=64, max_length=64)
    old_text: str = Field(min_length=1, max_length=200_000)
    new_text: str = Field(max_length=200_000)


def install_workspace_qualification_routes(
    app: FastAPI,
    *,
    workspace_roots: Mapping[str, str | Path],
    with_connection: Callable,
    require_read_key: Callable,
    require_editor_key: Callable,
    require_human_actor: Callable,
) -> None:
    """Mount Workspace interaction seams without adding a new document/chat owner."""

    def prepare(body: WorkspaceQualificationPreviewBody) -> dict:
        try:
            return with_connection(
                lambda conn: workspace_qualification.build_workspace_qualification_preview(
                    conn,
                    workspace_roots=workspace_roots,
                    project_id=body.project_id,
                    workspace_ref=body.workspace_ref,
                    relative_path=body.relative_path,
                    prepare_markdown=body.prepare_markdown,
                    user_instruction=body.user_instruction,
                )
            )
        except workspace_qualification.WorkspaceQualificationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def prepare_rework(body: WorkspaceReworkPreviewBody) -> dict:
        try:
            return with_connection(
                lambda conn: workspace_dialogue.build_workspace_rework_preview(
                    conn,
                    workspace_roots=workspace_roots,
                    project_id=body.project_id,
                    workspace_ref=body.workspace_ref,
                    relative_path=body.relative_path,
                    prior_handoff_id=body.prior_handoff_id,
                    instruction=body.instruction,
                )
            )
        except workspace_dialogue.WorkspaceDialogueConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_dialogue.WorkspaceDialogueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def ensure_fresh(
        current: dict,
        *,
        expected_preview_digest: str,
        expected_task_contract_ref: str,
        expected_context_pack_ref: str,
        label: str,
    ) -> None:
        stale = (
            current["preview_digest"] != expected_preview_digest
            or current["task_contract"]["task_contract_ref"] != expected_task_contract_ref
            or current["context_pack"]["context_pack_ref"] != expected_context_pack_ref
        )
        if stale:
            raise HTTPException(
                status_code=409,
                detail=f"{label} preview is stale; the source or request basis changed, prepare it again",
            )

    def submit_current(current: dict, *, actor: str, idempotency_key: str) -> dict:
        try:
            return with_connection(
                lambda conn: hermes_handoff_store.submit_handoff(
                    conn,
                    actor=actor,
                    idempotency_key=idempotency_key,
                    question=current["question"],
                    preview=current,
                    card_context_envelope=current["resolved_card_context_envelope"],
                    selected_context=current["resolved_selected_context"],
                    include_declared_descendants=False,
                )
            )
        except hermes_handoff_store.HandoffIdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except hermes_handoff_store.HandoffSubmissionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/cockpit/workspace-qualifications/preview")
    def preview_workspace_qualification(
        body: WorkspaceQualificationPreviewBody,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        return prepare(body)

    @app.post("/cockpit/workspace-qualifications/submit", status_code=201)
    def submit_workspace_qualification(
        body: WorkspaceQualificationSubmitBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        current = prepare(
            WorkspaceQualificationPreviewBody(
                project_id=body.project_id,
                workspace_ref=body.workspace_ref,
                relative_path=body.relative_path,
                prepare_markdown=body.prepare_markdown,
                user_instruction=body.user_instruction,
            )
        )
        ensure_fresh(
            current,
            expected_preview_digest=body.expected_preview_digest,
            expected_task_contract_ref=body.expected_task_contract_ref,
            expected_context_pack_ref=body.expected_context_pack_ref,
            label="workspace qualification",
        )
        result = submit_current(current, actor=actor, idempotency_key=body.idempotency_key)
        return {
            **result,
            "qualification_kind": current["qualification_kind"],
            "workspace_observation": current["workspace_observation"],
            "workspace_source_ref": current["workspace_source_ref"],
            "prepare_markdown_candidate": current["prepare_markdown_candidate"],
            "execution_authorized": False,
            "workspace_write_requested": False,
            "markdown_write_requested": False,
            "non_equivalences": [
                "qualification submitted != Hermes run started",
                "Work Issue created != execution authorized",
                "prepare Markdown candidate != workspace write",
                "qualification candidate != Document admission",
            ],
        }

    @app.post("/cockpit/workspace-dialogue/read")
    def read_workspace_dialogue(
        body: WorkspaceDialogueReadBody,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        try:
            return with_connection(
                lambda conn: workspace_dialogue.read_workspace_dialogue_turn(
                    conn,
                    workspace_roots=workspace_roots,
                    project_id=body.project_id,
                    workspace_ref=body.workspace_ref,
                    relative_path=body.relative_path,
                    handoff_id=body.handoff_id,
                )
            )
        except workspace_dialogue.WorkspaceDialogueConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_dialogue.WorkspaceDialogueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/cockpit/workspace-dialogue/rework/preview")
    def preview_workspace_rework(
        body: WorkspaceReworkPreviewBody,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        return prepare_rework(body)

    @app.post("/cockpit/workspace-dialogue/rework/submit", status_code=201)
    def submit_workspace_rework(
        body: WorkspaceReworkSubmitBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        current = prepare_rework(
            WorkspaceReworkPreviewBody(
                project_id=body.project_id,
                workspace_ref=body.workspace_ref,
                relative_path=body.relative_path,
                prior_handoff_id=body.prior_handoff_id,
                instruction=body.instruction,
            )
        )
        ensure_fresh(
            current,
            expected_preview_digest=body.expected_preview_digest,
            expected_task_contract_ref=body.expected_task_contract_ref,
            expected_context_pack_ref=body.expected_context_pack_ref,
            label="workspace rework",
        )
        result = submit_current(current, actor=actor, idempotency_key=body.idempotency_key)
        return {
            **result,
            "dialogue_kind": current["dialogue_kind"],
            "prior_handoff_id": current["prior_handoff_id"],
            "prior_result_candidate_id": current["prior_result_candidate_id"],
            "prior_result_digest": current["prior_result_digest"],
            "prior_context_truncated": current["prior_context_truncated"],
            "human_rework_instruction": current["human_rework_instruction"],
            "workspace_observation": current["workspace_observation"],
            "workspace_source_ref": current["workspace_source_ref"],
            "execution_authorized": False,
            "automatic_acceptance": False,
            "workspace_write_requested": False,
            "markdown_write_requested": False,
            "non_equivalences": [
                "rework submitted != Hermes run started",
                "new handoff != mutation of prior Work Issue",
                "prior result candidate != truth",
                "Work Issue created != execution authorized",
            ],
        }

    @app.post("/cockpit/workspace-notes/read")
    def read_workspace_note(
        body: WorkspaceHumanNoteReadBody,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        try:
            return workspace_human_note.read_workspace_human_note(
                workspace_roots,
                body.workspace_ref,
                body.relative_path,
            )
        except workspace_human_note.WorkspaceHumanNoteConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_human_note.WorkspaceHumanNoteError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/cockpit/workspace-notes/write")
    def write_workspace_note(
        body: WorkspaceHumanNoteWriteBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        try:
            result = workspace_human_note.write_workspace_human_note(
                workspace_roots,
                body.workspace_ref,
                body.relative_path,
                human_note=body.human_note,
                expected_manifest_digest=body.expected_manifest_digest,
            )
        except workspace_human_note.WorkspaceHumanNoteConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_human_note.WorkspaceHumanNoteError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            **result,
            "written_by": actor,
            "workspace_write": True,
            "automatic_document_admission": False,
            "is_evidence": False,
            "non_equivalences": [
                "human note persisted != Document admission",
                "human note persisted != Evidence",
                "sidecar present != governed identity",
            ],
        }

    @app.post("/cockpit/workspace-markdown/read")
    def read_workspace_markdown(
        body: WorkspaceMarkdownReadBody,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        try:
            return workspace_markdown_write.read_workspace_markdown(
                workspace_roots,
                body.workspace_ref,
                body.relative_path,
            )
        except workspace_markdown_write.WorkspaceMarkdownWriteConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_markdown_write.WorkspaceMarkdownWriteError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/cockpit/workspace-markdown/create", status_code=201)
    def create_workspace_markdown(
        body: WorkspaceMarkdownCreateBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        try:
            result = workspace_markdown_write.create_workspace_markdown(
                workspace_roots,
                body.workspace_ref,
                body.relative_path,
                content=body.content,
            )
        except workspace_markdown_write.WorkspaceMarkdownWriteConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_markdown_write.WorkspaceMarkdownWriteError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            **result,
            "written_by": actor,
            "workspace_write": True,
            "automatic_document_admission": False,
            "is_evidence": False,
            "non_equivalences": [
                "workspace Markdown persisted != Document admission",
                "workspace Markdown persisted != Evidence",
                "workspace path != governed identity",
                "workspace write != Hindsight write",
            ],
        }

    @app.post("/cockpit/workspace-markdown/patch")
    def patch_workspace_markdown(
        body: WorkspaceMarkdownPatchBody,
        _authorized: None = Depends(require_editor_key),
        actor: str = Depends(require_human_actor),
    ) -> dict:
        try:
            result = workspace_markdown_write.patch_workspace_markdown(
                workspace_roots,
                body.workspace_ref,
                body.relative_path,
                expected_digest=body.expected_digest,
                old_text=body.old_text,
                new_text=body.new_text,
            )
        except workspace_markdown_write.WorkspaceMarkdownWriteConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except workspace_markdown_write.WorkspaceMarkdownWriteError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            **result,
            "written_by": actor,
            "workspace_write": True,
            "automatic_document_admission": False,
            "is_evidence": False,
            "non_equivalences": [
                "workspace Markdown persisted != Document admission",
                "workspace Markdown persisted != Evidence",
                "workspace path != governed identity",
                "workspace write != Hindsight write",
            ],
        }
