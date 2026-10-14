"""Read-only filesystem workspace projection into Cockpit Card Collections.

This module observes explicitly configured filesystem roots and emits ephemeral
Card projections. It does not create a Folder owner, persist Cards, infer
Project/Category/Source/Document/Knowledge identity, parse file contents or
change authorization/governance state.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import stat as stat_module
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Mapping
from urllib.parse import quote, urlencode


class WorkspaceCollectionReadError(ValueError):
    """The configured workspace or requested collection cannot be projected safely."""


class WorkspaceNotFound(WorkspaceCollectionReadError):
    """The requested opaque workspace reference is not configured."""


class WorkspacePathNotFound(WorkspaceCollectionReadError):
    """The requested relative workspace path does not exist."""


class WorkspacePathNotDirectory(WorkspaceCollectionReadError):
    """A collection read targeted an entry that is not a directory."""


class WorkspacePathNotFile(WorkspaceCollectionReadError):
    """An exact file observation targeted an entry that is not a regular file."""


class WorkspaceFileChanged(WorkspaceCollectionReadError):
    """The exact file changed while a byte-basis observation was being computed."""


class WorkspaceConfigurationError(WorkspaceCollectionReadError):
    """The server-side workspace mapping is invalid."""


_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:(?:/|$)")


def parse_workspace_roots_config(raw_config: str | None) -> dict[str, str]:
    """Parse the deployment-owned JSON mapping without inventing any roots."""
    if raw_config is None or not raw_config.strip():
        return {}
    try:
        payload = json.loads(raw_config)
    except (TypeError, json.JSONDecodeError) as exc:
        raise WorkspaceConfigurationError(
            "MVP_WORKSPACE_ROOTS_JSON must be a JSON object"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkspaceConfigurationError(
            "MVP_WORKSPACE_ROOTS_JSON must be a JSON object"
        )

    configured: dict[str, str] = {}
    for raw_ref, raw_root in payload.items():
        if not isinstance(raw_ref, str) or not isinstance(raw_root, str) or not raw_root.strip():
            raise WorkspaceConfigurationError(
                "MVP_WORKSPACE_ROOTS_JSON values must map workspace refs to non-empty paths"
            )
        configured[raw_ref] = raw_root
    return configured


def prepare_workspace_roots(
    workspace_roots: Mapping[str, str | Path] | None,
) -> dict[str, Path]:
    """Resolve the explicit server-owned workspace mapping once at composition time."""
    prepared: dict[str, Path] = {}
    for raw_ref, raw_root in (workspace_roots or {}).items():
        ref = str(raw_ref).strip()
        if not ref or ref in {".", ".."} or "/" in ref or "\\" in ref:
            raise WorkspaceConfigurationError(
                f"invalid workspace_ref: {raw_ref!r}"
            )
        if ref in prepared:
            raise WorkspaceConfigurationError(f"duplicate workspace_ref: {ref!r}")
        try:
            root = Path(raw_root).resolve()
        except (TypeError, ValueError) as exc:
            raise WorkspaceConfigurationError(
                f"invalid configured workspace root: {ref!r}"
            ) from exc
        if not root.exists() or not root.is_dir():
            raise WorkspaceConfigurationError(
                f"configured workspace root is not an existing directory: {ref!r}"
            )
        prepared[ref] = root
    return prepared


def normalize_relative_path(relative_path: str | None) -> str:
    """Normalize one client-supplied relative POSIX path without broadening scope.

    This intentionally mirrors the existing Task Contract source-path invariant:
    no backslashes, absolute paths or ``..`` traversal. The root collection uses
    the empty string as its relative path.
    """
    if relative_path in (None, ""):
        return ""
    if not isinstance(relative_path, str):
        raise WorkspaceCollectionReadError("workspace path must be a string")
    if "\x00" in relative_path:
        raise WorkspaceCollectionReadError("workspace path contains a NUL byte")
    if "\\" in relative_path or _WINDOWS_DRIVE.match(relative_path):
        raise WorkspaceCollectionReadError(
            f"workspace path is not a relative POSIX path: {relative_path!r}"
        )
    path = PurePosixPath(relative_path)
    if path.is_absolute():
        raise WorkspaceCollectionReadError(
            f"workspace path is not relative: {relative_path!r}"
        )
    if ".." in path.parts:
        raise WorkspaceCollectionReadError(
            f"workspace path traverses outside the configured root: {relative_path!r}"
        )
    normalized = path.as_posix()
    return "" if normalized == "." else normalized


def _reject_hidden_components(relative_path: str) -> None:
    """Keep exact reads inside the same visible namespace as collection navigation."""
    for part in PurePosixPath(relative_path).parts if relative_path else ():
        if part == "_VAULT.md" or part.startswith("."):
            raise WorkspacePathNotFound(
                f"workspace path is not exposed by the read projection: {relative_path!r}"
            )


def _reject_symlink_components(root: Path, relative_path: str) -> None:
    """Keep ordinary projection reads symlink-free."""
    current = root
    for part in PurePosixPath(relative_path).parts if relative_path else ():
        current = current / part
        if current.is_symlink():
            raise WorkspaceCollectionReadError(
                f"workspace symlink entries are not exposed: {relative_path!r}"
            )


def _resolve_entry(root: Path, relative_path: str) -> Path:
    _reject_hidden_components(relative_path)
    _reject_symlink_components(root, relative_path)
    target = (root / relative_path).resolve()
    root_real = root.resolve()
    if not target.is_relative_to(root_real):
        raise WorkspaceCollectionReadError(
            f"workspace path resolves outside the configured root: {relative_path!r}"
        )
    if not target.exists():
        raise WorkspacePathNotFound(
            f"workspace path does not exist: {relative_path!r}"
        )
    return target


def _resolve_directory(root: Path, relative_path: str) -> Path:
    """Resolve a normalized path under one root and require a real directory."""
    target = _resolve_entry(root, relative_path)
    if not target.is_dir():
        raise WorkspacePathNotDirectory(
            f"workspace collection target is not a directory: {relative_path!r}"
        )
    return target


def _resolve_file(root: Path, relative_path: str) -> Path:
    """Resolve one visible regular file for cheap, reconstructible observation."""
    if not relative_path:
        raise WorkspacePathNotFile("workspace file path is required")
    target = _resolve_entry(root, relative_path)
    if not target.is_file():
        raise WorkspacePathNotFile(
            f"workspace entry is not a regular file: {relative_path!r}"
        )
    return target


def _entry_id(workspace_ref: str, relative_path: str) -> str:
    digest = hashlib.sha256(
        f"{workspace_ref}\0{relative_path}".encode("utf-8")
    ).hexdigest()
    return f"workspace-entry:{digest}"


def _child_collection_href(workspace_ref: str, relative_path: str) -> str:
    encoded_ref = quote(workspace_ref, safe="")
    query = urlencode({"path": relative_path})
    return f"/cockpit/workspace-collections/{encoded_ref}?{query}"


def _media_type(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _file_kind(path: Path, media_type: str) -> str:
    if media_type == "application/pdf" or path.suffix.casefold() == ".pdf":
        return "pdf"
    return "file"


def _relative_child_path(parent: str, name: str) -> str:
    return PurePosixPath(parent, name).as_posix() if parent else PurePosixPath(name).as_posix()


def _adjacent_document_sidecar(path: Path, relative_path: str) -> dict:
    """Observe the per-source info sidecar; do not parse or infer a binding."""
    sidecar_name = f"{path.stem}.yaml"
    if path.name.casefold() == sidecar_name.casefold():
        return {
            "state": "unsupported_source_collision",
            "relative_path": None,
            "parsed": False,
            "identity_mapping_resolved": False,
        }

    sidecar = path.parent / sidecar_name
    if sidecar.is_symlink():
        state = "unsupported_symlink"
        sidecar_ref = None
    elif sidecar.is_file():
        state = "present"
        parent = PurePosixPath(relative_path).parent
        sidecar_ref = PurePosixPath(parent, sidecar_name).as_posix()
        if sidecar_ref == f"./{sidecar_name}":
            sidecar_ref = sidecar_name
    else:
        state = "absent"
        sidecar_ref = None
    return {
        "state": state,
        "relative_path": sidecar_ref,
        "parsed": False,
        "identity_mapping_resolved": False,
    }


def _metadata_from_stat(path: Path, relative_path: str, stat: os.stat_result) -> dict:
    media_type = _media_type(path)
    return {
        "filename": path.name,
        "extension": path.suffix.casefold(),
        "media_type": media_type,
        "byte_size": stat.st_size,
        "file_kind": _file_kind(path, media_type),
        "filesystem_modified_at": datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
        "adjacent_document_sidecar": _adjacent_document_sidecar(path, relative_path),
    }


def _basic_file_metadata(path: Path, relative_path: str) -> dict:
    """Return cheap reconstructible facts suitable for ordinary Card navigation."""
    try:
        observed_stat = path.stat()
    except OSError as exc:
        raise WorkspaceCollectionReadError(
            f"workspace file cannot be inspected: {path.name!r}"
        ) from exc
    return _metadata_from_stat(path, relative_path, observed_stat)


def _stat_identity(stat: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    )


def _secure_open_workspace_file(root: Path, relative_path: str) -> int:
    """Open each path component relative to the configured root with no-follow semantics."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise WorkspaceCollectionReadError(
            "exact workspace observation requires O_NOFOLLOW and O_DIRECTORY support"
        )
    _reject_hidden_components(relative_path)
    parts = PurePosixPath(relative_path).parts
    if not parts:
        raise WorkspacePathNotFile("workspace file path is required")

    root_fd: int | None = None
    directory_fds: list[int] = []
    try:
        root_fd = os.open(
            root,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        parent_fd = root_fd
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent_fd,
            )
            directory_fds.append(next_fd)
            parent_fd = next_fd
        file_fd = os.open(
            parts[-1],
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        file_stat = os.fstat(file_fd)
        if not stat_module.S_ISREG(file_stat.st_mode):
            os.close(file_fd)
            raise WorkspacePathNotFile(
                f"workspace entry is not a regular file: {relative_path!r}"
            )
        return file_fd
    except FileNotFoundError as exc:
        raise WorkspacePathNotFound(
            f"workspace path does not exist: {relative_path!r}"
        ) from exc
    except OSError as exc:
        raise WorkspaceCollectionReadError(
            f"workspace file cannot be opened without following links: {relative_path!r}"
        ) from exc
    finally:
        for descriptor in reversed(directory_fds):
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)


def _exact_file_metadata(root: Path, relative_path: str) -> dict:
    """Return metadata and digest from one stable descriptor, then verify path identity."""
    entry_path = root / relative_path
    digest = hashlib.sha256()
    file_fd = _secure_open_workspace_file(root, relative_path)
    try:
        with os.fdopen(file_fd, "rb", closefd=True) as stream:
            before = os.fstat(stream.fileno())
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise WorkspaceCollectionReadError(
            f"workspace file cannot be hashed safely: {relative_path!r}"
        ) from exc

    if _stat_identity(before) != _stat_identity(after):
        raise WorkspaceFileChanged(
            f"workspace file changed while hashing: {relative_path!r}"
        )

    verify_fd = _secure_open_workspace_file(root, relative_path)
    try:
        current = os.fstat(verify_fd)
    finally:
        os.close(verify_fd)
    if _stat_identity(after) != _stat_identity(current):
        raise WorkspaceFileChanged(
            f"workspace file was replaced while hashing: {relative_path!r}"
        )

    observed = _metadata_from_stat(entry_path, relative_path, after)
    observed["digest_sha256"] = digest.hexdigest()
    return observed


def observe_workspace_file(
    workspace_roots: Mapping[str, Path],
    workspace_ref: str,
    relative_path: str,
    *,
    include_digest: bool = False,
) -> dict:
    """Observe one exact visible file without promoting it to a governed object."""
    root = workspace_roots.get(workspace_ref)
    if root is None:
        raise WorkspaceNotFound(f"unknown workspace_ref: {workspace_ref!r}")
    normalized = normalize_relative_path(relative_path)
    if include_digest:
        observed = _exact_file_metadata(root, normalized)
    else:
        entry = _resolve_file(root, normalized)
        observed = _basic_file_metadata(entry, normalized)
    return {
        "workspace_ref": workspace_ref,
        "relative_path": normalized,
        "workspace_entry_id": _entry_id(workspace_ref, normalized),
        "workspace_file": observed,
        "observation_persisted": False,
        "content_parsed": False,
        "governed_identity": False,
    }


def _workspace_card(
    *,
    workspace_ref: str,
    relative_path: str,
    name: str,
    kind: str,
    file_entry: Path | None = None,
) -> dict:
    entity_id = _entry_id(workspace_ref, relative_path)
    is_directory = kind == "directory"
    card = {
        "entity_id": entity_id,
        "entity_type": "workspace_entry",
        "role": "container" if is_directory else "entity",
        "family": "information",
        "presentation_family": "information",
        "category": "Dossier" if is_directory else "Fichier",
        "title": name,
        "summary": (
            "Dossier du workspace — projection en lecture seule"
            if is_directory
            else "Fichier du workspace — projection en lecture seule"
        ),
        "status": "neutral",
        "type_tags": [],
        "subject_tags": [],
        "limits": [],
        "available_actions": [],
        "back": [
            ["Workspace", workspace_ref],
            ["Chemin relatif", relative_path],
            ["Nature", "Dossier" if is_directory else "Fichier"],
        ],
        "workspace_ref": workspace_ref,
        "relative_path": relative_path,
        "workspace_entry_kind": kind,
    }
    if is_directory:
        card["child_collection"] = {
            "state": "available",
            "collection_id": f"children:{entity_id}",
            "load_action": {
                "kind": "collection_read",
                "href": _child_collection_href(workspace_ref, relative_path),
            },
            "can_add": False,
            "create_action": None,
        }
    elif file_entry is not None:
        observed = _basic_file_metadata(file_entry, relative_path)
        sidecar = observed["adjacent_document_sidecar"]
        if observed["file_kind"] == "pdf":
            card["category"] = "PDF"
            card["summary"] = "PDF du workspace — observation locale reconstructible"
        card["workspace_file"] = observed
        card["qualification"] = {
            "status": "workspace_observation_only",
            "identity_mapping": "not_resolved_by_workspace_projection",
            "automatic_document_admission": False,
        }
        card["authority"] = {
            "governed_identity": False,
            "is_evidence": False,
            "is_memory": False,
            "is_persisted": False,
        }
        card["back"].extend(
            [
                ["Type MIME", observed["media_type"]],
                ["Taille (octets)", str(observed["byte_size"])],
                ["Modifié (filesystem)", observed["filesystem_modified_at"]],
                ["Infos YAML adjacentes", sidecar["state"]],
            ]
        )
    return card


def get_workspace_catalog(workspace_roots: Mapping[str, Path]) -> dict:
    """Project configured workspace references without exposing physical roots."""
    items = [
        _workspace_card(
            workspace_ref=workspace_ref,
            relative_path="",
            name=workspace_ref,
            kind="directory",
        )
        for workspace_ref in sorted(workspace_roots, key=lambda value: (value.casefold(), value))
    ]
    return {
        "collection": {
            "collection_id": "children:space:workspace",
            "parent_entity_id": "space:workspace",
            "state": "loaded" if items else "empty",
            "items": items,
            "can_add": False,
        },
        "cards_are_projections": True,
    }


def get_workspace_collection(
    workspace_roots: Mapping[str, Path],
    workspace_ref: str,
    relative_path: str | None = "",
) -> dict:
    """Project the direct children of one explicitly configured workspace directory."""
    root = workspace_roots.get(workspace_ref)
    if root is None:
        raise WorkspaceNotFound(f"unknown workspace_ref: {workspace_ref!r}")

    normalized = normalize_relative_path(relative_path)
    directory = _resolve_directory(root, normalized)

    projected: list[tuple[int, str, str, dict]] = []
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        raise WorkspaceCollectionReadError(
            f"workspace directory cannot be listed: {normalized!r}"
        ) from exc

    for entry in entries:
        name = entry.name
        if name == "_VAULT.md" or name.startswith(".") or entry.is_symlink():
            continue
        try:
            if entry.is_dir():
                kind = "directory"
                kind_order = 0
                file_entry = None
            elif entry.is_file():
                kind = "file"
                kind_order = 1
                file_entry = entry
            else:
                continue
        except OSError as exc:
            raise WorkspaceCollectionReadError(
                f"workspace entry cannot be inspected: {name!r}"
            ) from exc

        child_path = _relative_child_path(normalized, name)
        card = _workspace_card(
            workspace_ref=workspace_ref,
            relative_path=child_path,
            name=name,
            kind=kind,
            file_entry=file_entry,
        )
        projected.append((kind_order, name.casefold(), name, card))

    projected.sort(key=lambda item: item[:3])
    items = [item[3] for item in projected]
    parent_entity_id = _entry_id(workspace_ref, normalized)
    return {
        "collection": {
            "collection_id": f"children:{parent_entity_id}",
            "parent_entity_id": parent_entity_id,
            "state": "loaded" if items else "empty",
            "items": items,
            "can_add": False,
        },
        "cards_are_projections": True,
        "observation_persisted": False,
        "content_parsed": False,
        "hindsight_required": False,
        "non_equivalences": [
            "workspace path != governed identity",
            "file observed != Document admitted",
            "manifest present != identity mapping resolved",
            "PDF observed != PDF content understood",
            "projection != persistence",
        ],
    }
