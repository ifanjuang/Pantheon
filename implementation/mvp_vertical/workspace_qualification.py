"""Prepare a read-only Hermes qualification handoff for one exact Workspace PDF.

This module bridges a filesystem observation into the existing Hermes handoff
candidate path without creating a Document, Source, Evidence or workspace owner.
The selected Project is explicit; it is never inferred from the filesystem path.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Mapping
from urllib.parse import quote

import psycopg

from . import agency_data, hermes_handoff_preview, workspace_collection_read


class WorkspaceQualificationError(ValueError):
    pass


def _workspace_source_ref(observation: dict) -> str:
    workspace_ref = quote(str(observation["workspace_ref"]), safe="")
    relative_path = quote(str(observation["relative_path"]), safe="/")
    digest = str(observation["workspace_file"]["digest_sha256"])
    return f"workspace://{workspace_ref}/{relative_path}?sha256={digest}"


def _qualification_question(
    *,
    observation: dict,
    prepare_markdown: bool,
    user_instruction: str | None,
) -> str:
    file_info = observation["workspace_file"]
    path = observation["relative_path"]
    digest = file_info["digest_sha256"]
    markdown_instruction = (
        "Also prepare a Markdown representation candidate suitable for an Obsidian note, "
        "but do not write or overwrite any workspace file."
        if prepare_markdown
        else "Do not prepare or write a Markdown representation unless it is necessary to explain the result."
    )
    extra = (user_instruction or "").strip()
    extra_line = f"\nAdditional human instruction: {extra}" if extra else ""
    return (
        "Qualify the exact workspace PDF named below as a read-only candidate. "
        "Inspect the source only within the admitted workspace scope and return candidate metadata: "
        "document kind, full human title, issuer/reference, revision or index candidates, date candidates, "
        "issuer/author candidates, summary, essential information and compatible tag candidates. "
        "Keep multiple plausible dates/indices when ambiguous and source-locate extracted candidates by page, "
        "sheet, fragment or region when available. A detected date/index is not currentness, approval or a governed version. "
        "Do not invent a Document family/version identity, Evidence status, professional approval or purpose-specific currentness. "
        f"{markdown_instruction}\n"
        f"Workspace relative path: {path}\n"
        f"Exact SHA-256 basis: {digest}"
        f"{extra_line}"
    )


def build_workspace_qualification_preview(
    conn: psycopg.Connection,
    *,
    workspace_roots: Mapping[str, object],
    project_id: str,
    workspace_ref: str,
    relative_path: str,
    prepare_markdown: bool = False,
    user_instruction: str | None = None,
) -> dict:
    """Build one exact read-only qualification preview against the current PDF bytes."""
    project_id = str(project_id or "").strip()
    if not project_id:
        raise WorkspaceQualificationError("project_id is required and must be selected explicitly")
    try:
        agency_data.get_project(conn, project_id)
    except agency_data.ProjectNotFound as exc:
        raise WorkspaceQualificationError(str(exc)) from exc

    try:
        observation = workspace_collection_read.observe_workspace_file(
            workspace_roots,
            workspace_ref,
            relative_path,
            include_digest=True,
        )
    except workspace_collection_read.WorkspaceCollectionReadError as exc:
        raise WorkspaceQualificationError(str(exc)) from exc

    file_info = observation["workspace_file"]
    if file_info["file_kind"] != "pdf":
        raise WorkspaceQualificationError("workspace qualification V0 accepts PDF files only")

    source_ref = _workspace_source_ref(observation)
    question = _qualification_question(
        observation=observation,
        prepare_markdown=prepare_markdown,
        user_instruction=user_instruction,
    )
    envelope = {
        "root_entity": {
            "entity_id": f"project:{project_id}",
            "entity_type": "project",
        },
        "descendants": [],
        "source_refs": [source_ref],
        "tag_context": [],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    try:
        preview = hermes_handoff_preview.build_preview(
            question=question,
            card_context_envelope=envelope,
            selected_context=[],
        )
    except hermes_handoff_preview.HandoffPreviewError as exc:
        raise WorkspaceQualificationError(str(exc)) from exc

    return {
        **preview,
        "qualification_kind": "workspace_pdf_metadata",
        "workspace_observation": observation,
        "workspace_source_ref": source_ref,
        "prepare_markdown_candidate": bool(prepare_markdown),
        "question": question,
        "resolved_card_context_envelope": envelope,
        "resolved_selected_context": [],
        "automatic_document_admission": False,
        "workspace_write_requested": False,
        "markdown_write_requested": False,
        "non_equivalences": [
            *preview["non_equivalences"],
            "workspace source ref != governed Source identity",
            "workspace path != Project identity",
            "qualification candidate != Document admission",
            "prepare Markdown candidate != Markdown write authorization",
            "detected index/date != professional currentness",
        ],
    }
