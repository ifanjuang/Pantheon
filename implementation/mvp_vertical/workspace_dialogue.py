"""Read and continue Hermes qualification turns for one Workspace source.

A dialogue is a projection over immutable handoffs, Work Issues and Hermes result
candidates. This module does not create a chat owner, persist conversational
truth, admit Evidence or authorize execution. A rework creates a fresh read-only
handoff candidate against the current exact source bytes.
"""

from __future__ import annotations

import json
import re
from typing import Mapping
from urllib.parse import parse_qs, unquote, urlparse

import psycopg

from . import (
    agency_data,
    hermes_handoff_store,
    hermes_result_candidate,
    work_issues,
    workspace_collection_read,
    workspace_qualification,
)


class WorkspaceDialogueError(ValueError):
    pass


class WorkspaceDialogueConflict(WorkspaceDialogueError):
    pass


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_PRIOR_SUMMARY = 1_800
_MAX_PRIOR_PAYLOAD = 1_200


def _workspace_source_parts(source_ref: str) -> tuple[str, str, str]:
    parsed = urlparse(str(source_ref or ""))
    if parsed.scheme != "workspace" or not parsed.netloc:
        raise WorkspaceDialogueConflict("prior handoff does not carry a Workspace source reference")
    workspace_ref = unquote(parsed.netloc)
    try:
        relative_path = workspace_collection_read.normalize_relative_path(
            unquote(parsed.path.lstrip("/"))
        )
    except workspace_collection_read.WorkspaceCollectionReadError as exc:
        raise WorkspaceDialogueConflict("prior Workspace source reference has an invalid path") from exc
    digest_values = parse_qs(parsed.query).get("sha256") or []
    digest = digest_values[0].casefold() if len(digest_values) == 1 else ""
    if not _SHA256_RE.fullmatch(digest):
        raise WorkspaceDialogueConflict("prior Workspace source reference has no exact SHA-256 basis")
    return workspace_ref, relative_path, digest


def _bounded_text(value: object, limit: int) -> tuple[str, bool]:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text, False
    return text[:limit].rstrip() + "\n[truncated for bounded rework context]", True


def _bounded_payload(candidate: dict | None) -> tuple[str, bool]:
    if not candidate:
        return "", False
    payload = candidate.get("candidate_payload")
    if not isinstance(payload, dict) or not payload:
        return "", False
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(raw) <= _MAX_PRIOR_PAYLOAD:
        return raw, False
    return (
        "[prior structured candidate payload omitted from prompt because it exceeds the bounded context; "
        f"result_candidate_id={candidate.get('result_candidate_id')}]",
        True,
    )


def _project_scope(
    conn: psycopg.Connection,
    *,
    project_id: str,
    workspace_ref: str,
    relative_path: str,
    handoff_id: str,
) -> tuple[dict, str, str]:
    project_id = str(project_id or "").strip()
    if not project_id:
        raise WorkspaceDialogueError("project_id is required and must be selected explicitly")
    try:
        agency_data.get_project(conn, project_id)
    except agency_data.ProjectNotFound as exc:
        raise WorkspaceDialogueError(str(exc)) from exc

    try:
        normalized_path = workspace_collection_read.normalize_relative_path(relative_path)
    except workspace_collection_read.WorkspaceCollectionReadError as exc:
        raise WorkspaceDialogueError(str(exc)) from exc
    try:
        handoff = hermes_handoff_store.get_handoff_snapshot(conn, handoff_id)
    except hermes_handoff_store.HandoffSubmissionError as exc:
        raise WorkspaceDialogueError(str(exc)) from exc

    if handoff.get("case_ref") != project_id:
        raise WorkspaceDialogueConflict("prior handoff belongs to another Project")
    if handoff.get("root_entity_type") != "project" or handoff.get("root_entity_id") != f"project:{project_id}":
        raise WorkspaceDialogueConflict("prior handoff root does not match the explicit Project")

    context_pack = handoff.get("context_pack") or {}
    refs = [ref for ref in context_pack.get("source_refs") or [] if str(ref).startswith("workspace://")]
    if len(refs) != 1:
        raise WorkspaceDialogueConflict("prior handoff must carry exactly one Workspace source reference")
    prior_workspace_ref, prior_path, prior_digest = _workspace_source_parts(str(refs[0]))
    if prior_workspace_ref != workspace_ref or prior_path != normalized_path:
        raise WorkspaceDialogueConflict("prior handoff is bound to another Workspace source")
    return handoff, prior_digest, normalized_path


def read_workspace_dialogue_turn(
    conn: psycopg.Connection,
    *,
    workspace_roots: Mapping[str, object],
    project_id: str,
    workspace_ref: str,
    relative_path: str,
    handoff_id: str,
) -> dict:
    """Project one stored qualification turn without requiring current source bytes."""
    # `workspace_roots` remains in the public seam because the same request shape
    # is used by rework. Historical read deliberately does not dereference it.
    _ = workspace_roots
    handoff, prior_digest, normalized_path = _project_scope(
        conn,
        project_id=project_id,
        workspace_ref=workspace_ref,
        relative_path=relative_path,
        handoff_id=handoff_id,
    )
    try:
        work_projection = work_issues.get_issue(conn, handoff["work_issue_id"])
    except work_issues.WorkIssueError as exc:
        raise WorkspaceDialogueError(str(exc)) from exc

    runs: list[dict] = []
    latest_result: dict | None = None
    for stored_run in work_projection.get("hermes_runs") or []:
        run = dict(stored_run)
        try:
            candidate = hermes_result_candidate.get_result_candidate_for_run(
                conn,
                str(run.get("run_id") or ""),
            )
        except hermes_result_candidate.HermesResultCandidateError as exc:
            raise WorkspaceDialogueError(str(exc)) from exc
        run["result_candidate"] = candidate
        runs.append(run)
        if run.get("normalized_return"):
            latest_result = {
                "run_id": run.get("run_id"),
                "normalized_return": run.get("normalized_return"),
                "result_candidate": candidate,
            }

    if any(run.get("status") == "running" for run in runs):
        turn_state = "running"
    elif latest_result is not None:
        turn_state = "returned"
    else:
        turn_state = "submitted"

    return {
        "kind": "workspace_hermes_dialogue_turn",
        "handoff_id": handoff["handoff_id"],
        "work_issue_id": handoff["work_issue_id"],
        "project_id": project_id,
        "workspace_ref": workspace_ref,
        "relative_path": normalized_path,
        "source_basis_sha256": prior_digest,
        "turn_state": turn_state,
        "work_issue": work_projection.get("work_issue"),
        "runs": runs,
        "latest_result": latest_result,
        "candidate_only": True,
        "is_evidence": False,
        "professional_truth": False,
        "non_equivalences": [
            "dialogue projection != chat authority",
            "Hermes result candidate != Evidence",
            "Hermes result candidate != professional truth",
            "source path != governed identity",
        ],
    }


def _prior_rework_context(turn: dict, instruction: str) -> tuple[str, bool]:
    latest = turn.get("latest_result") or {}
    normalized_return = latest.get("normalized_return") or {}
    summary, summary_truncated = _bounded_text(
        normalized_return.get("summary"),
        _MAX_PRIOR_SUMMARY,
    )
    candidate = latest.get("result_candidate")
    payload_text, payload_truncated = _bounded_payload(candidate)
    result_ref = candidate.get("result_candidate_id") if candidate else "none"
    result_digest = candidate.get("result_digest") if candidate else "none"
    sections = [
        "This is a targeted rework of a previous Hermes qualification candidate for the same Workspace source.",
        "The previous result remains a candidate only: it is not Evidence, professional truth, approval or currentness.",
        f"Prior handoff: {turn['handoff_id']}",
        f"Prior result candidate: {result_ref}",
        f"Prior result digest: {result_digest}",
        "Re-read the exact current PDF bytes. Preserve previous conclusions only when the current source still supports them.",
        "Return a complete replacement candidate rather than a patch, and explicitly state what was rechecked or changed.",
    ]
    if summary:
        sections.extend(["Previous candidate summary:", summary])
    if payload_text:
        sections.extend(["Previous structured candidate context:", payload_text])
    sections.extend(["Human rework instruction:", instruction.strip()])
    return "\n".join(sections), summary_truncated or payload_truncated


def build_workspace_rework_preview(
    conn: psycopg.Connection,
    *,
    workspace_roots: Mapping[str, object],
    project_id: str,
    workspace_ref: str,
    relative_path: str,
    prior_handoff_id: str,
    instruction: str,
) -> dict:
    """Build a fresh read-only qualification preview using one prior candidate as bounded context."""
    instruction = str(instruction or "").strip()
    if len(instruction) < 3:
        raise WorkspaceDialogueError("rework instruction must contain at least 3 characters")
    if len(instruction) > 2_000:
        raise WorkspaceDialogueError("rework instruction exceeds 2000 characters")

    turn = read_workspace_dialogue_turn(
        conn,
        workspace_roots=workspace_roots,
        project_id=project_id,
        workspace_ref=workspace_ref,
        relative_path=relative_path,
        handoff_id=prior_handoff_id,
    )
    if turn.get("latest_result") is None:
        raise WorkspaceDialogueConflict("prior handoff has no Hermes return to rework yet")

    prior_instruction, context_truncated = _prior_rework_context(turn, instruction)
    try:
        preview = workspace_qualification.build_workspace_qualification_preview(
            conn,
            workspace_roots=workspace_roots,
            project_id=project_id,
            workspace_ref=workspace_ref,
            relative_path=relative_path,
            prepare_markdown=False,
            user_instruction=prior_instruction,
        )
    except workspace_qualification.WorkspaceQualificationError as exc:
        raise WorkspaceDialogueError(str(exc)) from exc

    latest = turn["latest_result"] or {}
    candidate = latest.get("result_candidate") or {}
    return {
        **preview,
        "dialogue_kind": "workspace_pdf_targeted_rework",
        "prior_handoff_id": prior_handoff_id,
        "prior_result_candidate_id": candidate.get("result_candidate_id"),
        "prior_result_digest": candidate.get("result_digest"),
        "prior_context_truncated": context_truncated,
        "human_rework_instruction": instruction,
        "automatic_acceptance": False,
        "execution_authorized": False,
        "non_equivalences": [
            *preview["non_equivalences"],
            "prior candidate context != truth",
            "rework preview != execution admission",
            "new handoff != mutation of prior Work Issue",
        ],
    }
