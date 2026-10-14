"""Bounded human-authored note editing for one exact Workspace source.

This module owns only one low-consequence fragment inside an adjacent
``<source-basename>.yaml`` info sidecar. It does not adopt a full document
manifest schema, infer a Document identity, qualify the source, write Evidence,
or authorize Hermes.

The managed fragment is delimited so unrelated YAML bytes/comments can remain
untouched instead of round-tripping an unknown future info carrier through
PyYAML.
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import stat as stat_module
import uuid
from pathlib import Path, PurePosixPath
from typing import Mapping

import yaml

from . import workspace_collection_read


class WorkspaceHumanNoteError(ValueError):
    """The human-note operation cannot be performed without widening ownership."""


class WorkspaceHumanNoteConflict(WorkspaceHumanNoteError):
    """The caller's sidecar basis or source binding is stale/conflicting."""


_START_MARKER = "# >>> Pantheon workspace info"
_END_MARKER = "# <<< Pantheon workspace info"
_START_RE = re.compile(r"(?m)^# >>> Pantheon workspace (?:info|note)\r?\n")
_END_RE = re.compile(r"(?m)^# <<< Pantheon workspace (?:info|note)(?:\r?\n|$)")
_DOCUMENT_END_RE = re.compile(r"(?m)^\.\.\.[ \t]*(?:#.*)?(?:\r?\n|$)")
_NAMESPACE = "pantheon_workspace"


def _sidecar_name(source_relative_path: str) -> str:
    source = PurePosixPath(source_relative_path)
    name = source.stem
    if not name.strip():
        raise WorkspaceHumanNoteError("workspace source basename is required for its info sidecar")
    if source.suffix.casefold() == ".yaml":
        raise WorkspaceHumanNoteError(
            "YAML workspace sources cannot use the same basename Infos sidecar"
        )
    return f"{name}.yaml"


def _sidecar_relative_path(source_relative_path: str) -> str:
    parent = PurePosixPath(source_relative_path).parent
    sidecar_name = _sidecar_name(source_relative_path)
    value = PurePosixPath(parent, sidecar_name).as_posix()
    return sidecar_name if value == f"./{sidecar_name}" else value


def _secure_open_directory(root: Path, relative_path: str) -> int:
    """Open one existing workspace directory using openat/no-follow traversal."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise WorkspaceHumanNoteError(
            "workspace note editing requires O_NOFOLLOW and O_DIRECTORY support"
        )
    normalized = workspace_collection_read.normalize_relative_path(relative_path)
    parts = PurePosixPath(normalized).parts if normalized else ()
    for part in parts:
        if part == "_VAULT.md" or part.startswith("."):
            raise WorkspaceHumanNoteError("hidden workspace paths are not writable")

    opened: list[int] = []
    try:
        current = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        opened.append(current)
        for part in parts:
            current = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=current,
            )
            opened.append(current)
        return opened.pop()
    except FileNotFoundError as exc:
        raise WorkspaceHumanNoteError("workspace note parent directory does not exist") from exc
    except OSError as exc:
        raise WorkspaceHumanNoteError(
            "workspace note parent cannot be opened without following links"
        ) from exc
    finally:
        for descriptor in reversed(opened):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _open_sidecar(parent_fd: int, sidecar_name: str) -> int | None:
    try:
        fd = os.open(sidecar_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.EMLINK}:
            raise WorkspaceHumanNoteError(f"{sidecar_name} symlinks are not writable") from exc
        raise WorkspaceHumanNoteError(f"{sidecar_name} cannot be opened safely") from exc
    observed = os.fstat(fd)
    if not stat_module.S_ISREG(observed.st_mode):
        os.close(fd)
        raise WorkspaceHumanNoteError(f"{sidecar_name} is not a regular file")
    return fd


def _read_fd(fd: int, sidecar_name: str) -> bytes:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
        return b"".join(chunks)
    except OSError as exc:
        raise WorkspaceHumanNoteError(f"{sidecar_name} cannot be read safely") from exc


def _read_sidecar_bytes(parent_fd: int, sidecar_name: str) -> bytes | None:
    fd = _open_sidecar(parent_fd, sidecar_name)
    if fd is None:
        return None
    try:
        return _read_fd(fd, sidecar_name)
    finally:
        os.close(fd)


def _manifest_digest(raw: bytes | None) -> str | None:
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def _capture_existing_metadata(parent_fd: int, sidecar_name: str, expected_digest: str) -> dict:
    """Capture access metadata from the same inode whose bytes match the write basis."""
    fd = _open_sidecar(parent_fd, sidecar_name)
    if fd is None:
        raise WorkspaceHumanNoteConflict(f"{sidecar_name} disappeared before replacement")
    try:
        raw = _read_fd(fd, sidecar_name)
        if _manifest_digest(raw) != expected_digest:
            raise WorkspaceHumanNoteConflict(
                f"{sidecar_name} changed while access metadata was being captured"
            )
        observed = os.fstat(fd)
        if not all(hasattr(os, name) for name in ("listxattr", "getxattr", "setxattr")):
            raise WorkspaceHumanNoteError(
                f"platform cannot preserve {sidecar_name} extended access metadata"
            )
        try:
            xattrs = tuple((name, os.getxattr(fd, name)) for name in os.listxattr(fd))
        except OSError as exc:
            raise WorkspaceHumanNoteError(
                f"{sidecar_name} extended access metadata cannot be read safely"
            ) from exc
        return {
            "mode": stat_module.S_IMODE(observed.st_mode),
            "uid": observed.st_uid,
            "gid": observed.st_gid,
            "xattrs": xattrs,
        }
    finally:
        os.close(fd)


def _decode_manifest(raw: bytes | None, sidecar_name: str) -> tuple[str, dict]:
    if raw is None:
        return "", {}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WorkspaceHumanNoteError(f"{sidecar_name} must be UTF-8") from exc
    try:
        value = yaml.safe_load(text) if text.strip() else {}
    except yaml.YAMLError as exc:
        raise WorkspaceHumanNoteError(f"{sidecar_name} is invalid YAML") from exc
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise WorkspaceHumanNoteError(f"{sidecar_name} root must be a mapping")
    return text, value


def _managed_range(text: str, sidecar_name: str) -> tuple[int, int] | None:
    starts = list(_START_RE.finditer(text))
    ends = list(_END_RE.finditer(text))
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or starts[0].start() >= ends[0].start():
        raise WorkspaceHumanNoteError(f"{sidecar_name} has an invalid Pantheon info fragment")
    return starts[0].start(), ends[0].end()


def _note_state(raw: bytes | None, source_relative_path: str, sidecar_name: str) -> dict:
    text, manifest = _decode_manifest(raw, sidecar_name)
    managed_range = _managed_range(text, sidecar_name)
    namespace = manifest.get(_NAMESPACE)
    if namespace is not None and not isinstance(namespace, dict):
        raise WorkspaceHumanNoteError("pantheon_workspace must be a mapping")
    if namespace is not None and managed_range is None:
        raise WorkspaceHumanNoteConflict(
            f"{sidecar_name} already owns pantheon_workspace outside the managed info fragment"
        )
    namespace = namespace or {}
    source_file = namespace.get("source_file")
    legacy_source_path = namespace.get("source_path")
    note = namespace.get("human_note")
    if source_file is not None and not isinstance(source_file, str):
        raise WorkspaceHumanNoteError("pantheon_workspace.source_file must be a string")
    if legacy_source_path is not None and not isinstance(legacy_source_path, str):
        raise WorkspaceHumanNoteError("pantheon_workspace.source_path must be a string")
    if source_file is None and legacy_source_path:
        source_file = PurePosixPath(legacy_source_path).name
    if note is not None and not isinstance(note, str):
        raise WorkspaceHumanNoteError("pantheon_workspace.human_note must be a string")

    expected_source_file = PurePosixPath(source_relative_path).name
    if source_file is None:
        binding_state = "unbound"
    elif source_file == expected_source_file:
        binding_state = "bound"
    else:
        binding_state = "mismatch"

    return {
        "text": text,
        "manifest": manifest,
        "managed_range": managed_range,
        "source_file": source_file,
        "human_note": note or "",
        "binding_state": binding_state,
    }


def _render_fragment(source_relative_path: str, human_note: str) -> str:
    payload = {
        _NAMESPACE: {
            "source_file": PurePosixPath(source_relative_path).name,
            "human_note": human_note,
        }
    }
    body = yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip("\n")
    return f"{_START_MARKER}\n{body}\n{_END_MARKER}\n"


def _append_fragment(text: str, replacement: str) -> str:
    """Append inside the existing YAML document, before an explicit ``...`` end marker."""
    document_ends = list(_DOCUMENT_END_RE.finditer(text))
    if document_ends:
        marker = document_ends[-1]
        prefix = text[: marker.start()]
        separator = "" if not prefix or prefix.endswith(("\n", "\r")) else "\n"
        return prefix + separator + replacement + text[marker.start() :]
    separator = "" if text.endswith(("\n", "\r")) else "\n"
    return text + separator + replacement


def _replace_fragment(text: str, managed_range: tuple[int, int] | None, replacement: str) -> str:
    if managed_range is not None:
        start, end = managed_range
        return text[:start] + replacement + text[end:]
    if not replacement:
        return text
    if not text:
        return replacement
    return _append_fragment(text, replacement)


def _apply_existing_metadata(fd: int, metadata: dict, sidecar_name: str) -> None:
    try:
        current = os.fstat(fd)
        if current.st_uid != metadata["uid"] or current.st_gid != metadata["gid"]:
            os.fchown(fd, metadata["uid"], metadata["gid"])
        os.fchmod(fd, metadata["mode"])
        for name, value in metadata["xattrs"]:
            os.setxattr(fd, name, value)

        verified = os.fstat(fd)
        if (
            verified.st_uid != metadata["uid"]
            or verified.st_gid != metadata["gid"]
            or stat_module.S_IMODE(verified.st_mode) != metadata["mode"]
        ):
            raise WorkspaceHumanNoteError(
                f"{sidecar_name} ownership or mode could not be preserved"
            )
        actual_xattrs = {name: os.getxattr(fd, name) for name in os.listxattr(fd)}
        expected_xattrs = dict(metadata["xattrs"])
        if actual_xattrs != expected_xattrs:
            raise WorkspaceHumanNoteError(
                f"{sidecar_name} extended access metadata could not be preserved"
            )
    except WorkspaceHumanNoteError:
        raise
    except OSError as exc:
        raise WorkspaceHumanNoteError(
            f"{sidecar_name} access metadata could not be preserved"
        ) from exc


def _atomic_replace(parent_fd: int, sidecar_name: str, raw: bytes, metadata: dict | None) -> None:
    temp_name = f".{sidecar_name}.pantheon-{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd: int | None = None
    try:
        create_mode = metadata["mode"] if metadata is not None else 0o600
        fd = os.open(temp_name, flags, create_mode, dir_fd=parent_fd)
        if metadata is not None:
            _apply_existing_metadata(fd, metadata, sidecar_name)
        offset = 0
        while offset < len(raw):
            written = os.write(fd, raw[offset:])
            if written <= 0:
                raise WorkspaceHumanNoteError(f"{sidecar_name} temporary write made no progress")
            offset += written
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(
            temp_name,
            sidecar_name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        os.fsync(parent_fd)
    except WorkspaceHumanNoteError:
        raise
    except OSError as exc:
        raise WorkspaceHumanNoteError(f"{sidecar_name} could not be replaced atomically") from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _context(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
) -> tuple[str, str, int]:
    try:
        observation = workspace_collection_read.observe_workspace_file(
            workspace_roots,
            workspace_ref,
            relative_path,
            include_digest=False,
        )
    except workspace_collection_read.WorkspaceCollectionReadError as exc:
        raise WorkspaceHumanNoteError(str(exc)) from exc
    normalized = observation["relative_path"]
    root = workspace_roots.get(workspace_ref)
    if root is None:
        raise WorkspaceHumanNoteError(f"unknown workspace_ref: {workspace_ref!r}")
    parent = PurePosixPath(normalized).parent.as_posix()
    if parent == ".":
        parent = ""
    return normalized, _sidecar_name(normalized), _secure_open_directory(Path(root), parent)


def read_workspace_human_note(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
) -> dict:
    """Read the one managed human note without inferring document identity."""
    normalized, sidecar_name, parent_fd = _context(workspace_roots, workspace_ref, relative_path)
    try:
        raw = _read_sidecar_bytes(parent_fd, sidecar_name)
        state = _note_state(raw, normalized, sidecar_name)
        return {
            "workspace_ref": workspace_ref,
            "relative_path": normalized,
            "sidecar_relative_path": _sidecar_relative_path(normalized),
            "manifest_state": "present" if raw is not None else "absent",
            "manifest_digest": _manifest_digest(raw),
            "binding_state": state["binding_state"],
            "human_note": state["human_note"],
            "managed_fragment": state["managed_range"] is not None,
            "governed_identity": False,
            "is_evidence": False,
        }
    finally:
        os.close(parent_fd)


def write_workspace_human_note(
    workspace_roots: Mapping[str, str | Path],
    workspace_ref: str,
    relative_path: str,
    *,
    human_note: str,
    expected_manifest_digest: str | None,
) -> dict:
    """Apply one explicit human note with optimistic sidecar-digest protection."""
    if not isinstance(human_note, str):
        raise WorkspaceHumanNoteError("human_note must be a string")
    note = human_note.rstrip()
    normalized, sidecar_name, parent_fd = _context(workspace_roots, workspace_ref, relative_path)
    try:
        raw = _read_sidecar_bytes(parent_fd, sidecar_name)
        current_digest = _manifest_digest(raw)
        if current_digest != expected_manifest_digest:
            raise WorkspaceHumanNoteConflict(
                f"{sidecar_name} changed since it was read; refresh the note before saving"
            )
        state = _note_state(raw, normalized, sidecar_name)
        if state["binding_state"] == "mismatch":
            raise WorkspaceHumanNoteConflict(
                f"{sidecar_name} Pantheon note is bound to another workspace source"
            )

        replacement = _render_fragment(normalized, note) if note else ""
        updated_text = _replace_fragment(state["text"], state["managed_range"], replacement)
        updated_raw = updated_text.encode("utf-8")
        if updated_raw == (raw or b""):
            return read_workspace_human_note(workspace_roots, workspace_ref, normalized)

        latest = _read_sidecar_bytes(parent_fd, sidecar_name)
        if _manifest_digest(latest) != current_digest:
            raise WorkspaceHumanNoteConflict(
                f"{sidecar_name} changed while the note was being prepared"
            )

        if not updated_text.strip():
            if raw is not None:
                try:
                    os.unlink(sidecar_name, dir_fd=parent_fd)
                    os.fsync(parent_fd)
                except FileNotFoundError as exc:
                    raise WorkspaceHumanNoteConflict(
                        f"{sidecar_name} disappeared while the note was being saved"
                    ) from exc
                except OSError as exc:
                    raise WorkspaceHumanNoteError(f"{sidecar_name} could not be removed") from exc
        else:
            metadata = (
                _capture_existing_metadata(parent_fd, sidecar_name, current_digest)
                if raw is not None and current_digest is not None
                else None
            )
            _atomic_replace(parent_fd, sidecar_name, updated_raw, metadata)
    finally:
        os.close(parent_fd)

    return read_workspace_human_note(workspace_roots, workspace_ref, normalized)
