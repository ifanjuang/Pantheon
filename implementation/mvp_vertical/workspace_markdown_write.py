"""Bounded Markdown mutations for the synchronized Workspace filesystem.

This module is the narrow write adapter needed by the Hermes/Obsidian workspace
qualification. It writes only ordinary Markdown files inside an explicitly
configured workspace root, uses optimistic digest protection for edits, and
returns a technical receipt after exact re-read verification.

It does not authorize Hermes, infer governed identity, admit Evidence, write to
CouchDB, or write to Hindsight. LiveSync and hindsight-obsidian-sync remain
separate downstream producers.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path, PurePosixPath
from typing import Mapping

from . import workspace_collection_read, workspace_human_note


class WorkspaceMarkdownWriteError(ValueError):
    """The requested Markdown mutation cannot remain inside the bounded workspace."""


class WorkspaceMarkdownWriteConflict(WorkspaceMarkdownWriteError):
    """The caller's expected source basis no longer matches the workspace file."""


_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _digest(raw: bytes | None) -> str | None:
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def _context(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
) -> tuple[str, str, int]:
    try:
        normalized = workspace_collection_read.normalize_relative_path(relative_path)
    except workspace_collection_read.WorkspaceCollectionReadError as exc:
        raise WorkspaceMarkdownWriteError(str(exc)) from exc

    if not normalized:
        raise WorkspaceMarkdownWriteError("workspace Markdown path is required")
    pure = PurePosixPath(normalized)
    filename = pure.name
    if filename == "_VAULT.md" or filename.startswith("."):
        raise WorkspaceMarkdownWriteError("hidden or vault-control Markdown is not writable")
    if pure.suffix.casefold() != ".md":
        raise WorkspaceMarkdownWriteError("bounded workspace writes currently support .md files only")

    root = workspace_roots.get(workspace_ref)
    if root is None:
        raise WorkspaceMarkdownWriteError(f"unknown workspace_ref: {workspace_ref!r}")
    parent = pure.parent.as_posix()
    if parent == ".":
        parent = ""
    try:
        parent_fd = workspace_human_note._secure_open_directory(Path(root), parent)
    except workspace_human_note.WorkspaceHumanNoteError as exc:
        raise WorkspaceMarkdownWriteError(str(exc)) from exc
    return normalized, filename, parent_fd


def _read(parent_fd: int, filename: str) -> bytes | None:
    try:
        return workspace_human_note._read_sidecar_bytes(parent_fd, filename)
    except workspace_human_note.WorkspaceHumanNoteError as exc:
        raise WorkspaceMarkdownWriteError(str(exc)) from exc


def _decode(raw: bytes | None, filename: str) -> str | None:
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WorkspaceMarkdownWriteError(f"{filename} must be UTF-8") from exc


def _validate_expected_digest(expected_digest: str) -> None:
    if not isinstance(expected_digest, str) or not _DIGEST_RE.fullmatch(expected_digest):
        raise WorkspaceMarkdownWriteError("expected_digest must be a lowercase SHA-256 hex digest")


def _observation(
    workspace_ref: str,
    relative_path: str,
    raw: bytes | None,
    *,
    operation: str,
    basis_digest: str | None,
    changed: bool,
) -> dict:
    return {
        "workspace_ref": workspace_ref,
        "relative_path": relative_path,
        "operation": operation,
        "state": "present" if raw is not None else "absent",
        "basis_digest": basis_digest,
        "result_digest": _digest(raw),
        "byte_size": len(raw) if raw is not None else 0,
        "changed": changed,
        "verified_by_reread": True,
        "persistence_effect": "workspace_file",
        "couchdb_direct_write": False,
        "hindsight_direct_write": False,
        "governed_identity": False,
        "is_evidence": False,
        "authorized": False,
    }


def read_workspace_markdown(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
) -> dict:
    """Read one exact Markdown file and return its digest without assigning authority."""
    normalized, filename, parent_fd = _context(workspace_roots, workspace_ref, relative_path)
    try:
        raw = _read(parent_fd, filename)
        text = _decode(raw, filename)
        result = _observation(
            workspace_ref,
            normalized,
            raw,
            operation="read",
            basis_digest=_digest(raw),
            changed=False,
        )
        result["text"] = text
        return result
    finally:
        os.close(parent_fd)


def create_workspace_markdown(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
    *,
    content: str,
) -> dict:
    """Create one absent Markdown note; existing files are never overwritten."""
    if not isinstance(content, str):
        raise WorkspaceMarkdownWriteError("content must be a string")
    normalized, filename, parent_fd = _context(workspace_roots, workspace_ref, relative_path)
    try:
        if _read(parent_fd, filename) is not None:
            raise WorkspaceMarkdownWriteConflict(
                f"{filename} already exists; read it before requesting a mutation"
            )
        raw = content.encode("utf-8")
        try:
            workspace_human_note._atomic_replace(parent_fd, filename, raw, None)
        except workspace_human_note.WorkspaceHumanNoteError as exc:
            raise WorkspaceMarkdownWriteError(str(exc)) from exc
        observed = _read(parent_fd, filename)
        if observed != raw:
            raise WorkspaceMarkdownWriteError(f"{filename} create verification failed")
        return _observation(
            workspace_ref,
            normalized,
            observed,
            operation="create",
            basis_digest=None,
            changed=True,
        )
    finally:
        os.close(parent_fd)


def patch_workspace_markdown(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
    *,
    expected_digest: str,
    old_text: str,
    new_text: str,
) -> dict:
    """Replace one exact unique anchor under optimistic source-digest protection."""
    _validate_expected_digest(expected_digest)
    if not isinstance(old_text, str) or not old_text:
        raise WorkspaceMarkdownWriteError("old_text must be a non-empty string")
    if not isinstance(new_text, str):
        raise WorkspaceMarkdownWriteError("new_text must be a string")

    normalized, filename, parent_fd = _context(workspace_roots, workspace_ref, relative_path)
    try:
        raw = _read(parent_fd, filename)
        if raw is None:
            raise WorkspaceMarkdownWriteConflict(f"{filename} does not exist")
        current_digest = _digest(raw)
        if current_digest != expected_digest:
            raise WorkspaceMarkdownWriteConflict(
                f"{filename} changed since it was read; refresh before patching"
            )
        text = _decode(raw, filename)
        assert text is not None
        occurrences = text.count(old_text)
        if occurrences != 1:
            raise WorkspaceMarkdownWriteConflict(
                f"{filename} patch anchor must occur exactly once; observed {occurrences}"
            )
        updated_text = text.replace(old_text, new_text, 1)
        if updated_text == text:
            return _observation(
                workspace_ref,
                normalized,
                raw,
                operation="patch",
                basis_digest=current_digest,
                changed=False,
            )
        updated_raw = updated_text.encode("utf-8")

        latest = _read(parent_fd, filename)
        if _digest(latest) != current_digest:
            raise WorkspaceMarkdownWriteConflict(
                f"{filename} changed while the patch was being prepared"
            )
        try:
            metadata = workspace_human_note._capture_existing_metadata(
                parent_fd, filename, current_digest
            )
            workspace_human_note._atomic_replace(parent_fd, filename, updated_raw, metadata)
        except workspace_human_note.WorkspaceHumanNoteConflict as exc:
            raise WorkspaceMarkdownWriteConflict(str(exc)) from exc
        except workspace_human_note.WorkspaceHumanNoteError as exc:
            raise WorkspaceMarkdownWriteError(str(exc)) from exc

        observed = _read(parent_fd, filename)
        if observed != updated_raw:
            raise WorkspaceMarkdownWriteError(f"{filename} patch verification failed")
        return _observation(
            workspace_ref,
            normalized,
            observed,
            operation="patch",
            basis_digest=current_digest,
            changed=True,
        )
    finally:
        os.close(parent_fd)
