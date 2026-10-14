"""Read-only consumer of the producer-owned Workspace project catalogue.

This module never scans the NAS. It reads the persisted producer projection and
resolves one exact project directory against server-side configured roots.
Filesystem location remains routing state, not governed Project identity.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping


MAX_CATALOGUE_BYTES = 4 * 1024 * 1024
ROOT_KINDS = frozenset({"AFFAIRES", "ARCHIVES_PROJET"})


class ProjectCatalogueError(ValueError):
    pass


class ProjectCatalogueUnavailable(ProjectCatalogueError):
    pass


class ProjectDestinationNotFound(ProjectCatalogueError):
    pass


class ProjectDestinationConflict(ProjectCatalogueError):
    pass


class ArchivedProjectWriteRequiresConfirmation(ProjectCatalogueError):
    pass


class ProjectDestinationUnsafe(ProjectCatalogueError):
    pass


def load_project_catalogue(state_db: Path) -> dict[str, Any]:
    path = state_db.expanduser()
    if not path.is_file():
        raise ProjectCatalogueUnavailable(f"workspace producer index is absent: {path}")
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)
        try:
            connection.execute("PRAGMA query_only=ON")
            row = connection.execute(
                "SELECT value FROM workspace_meta WHERE key='project_catalogue'"
            ).fetchone()
        finally:
            connection.close()
    except (OSError, sqlite3.Error) as exc:
        raise ProjectCatalogueUnavailable(
            "workspace project catalogue is unavailable"
        ) from exc
    if row is None:
        raise ProjectCatalogueUnavailable(
            "workspace project catalogue is absent from producer projection"
        )
    raw = str(row[0])
    if len(raw.encode("utf-8")) > MAX_CATALOGUE_BYTES:
        raise ProjectCatalogueUnavailable("workspace project catalogue exceeds read bound")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProjectCatalogueUnavailable(
            "workspace project catalogue is invalid JSON"
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("projects"), list):
        raise ProjectCatalogueUnavailable("workspace project catalogue shape is invalid")
    if payload.get("read_only") is not True or payload.get("bounded") is not True:
        raise ProjectCatalogueUnavailable(
            "workspace project catalogue posture is invalid"
        )
    if payload.get("truncated") is True:
        raise ProjectCatalogueUnavailable(
            "workspace project catalogue is truncated; automatic routing fails closed"
        )
    return payload


def _configured_roots(values: Mapping[str, str | Path]) -> dict[str, Path]:
    output: dict[str, Path] = {}
    for root_kind, raw_path in values.items():
        kind = str(root_kind or "").strip().upper()
        if kind not in ROOT_KINDS:
            continue
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            raise ProjectDestinationUnsafe(
                f"configured {kind} root must be absolute"
            )
        output[kind] = path.resolve(strict=False)
    return output


def resolve_project_destination(
    catalogue: dict[str, Any],
    *,
    project_name: str,
    root_paths: Mapping[str, str | Path],
    allow_archived_write: bool = False,
) -> dict[str, Any]:
    name = str(project_name or "").strip()
    if not name:
        raise ProjectDestinationNotFound("project_name is required")
    projects = catalogue.get("projects")
    if not isinstance(projects, list):
        raise ProjectCatalogueUnavailable("workspace project catalogue shape is invalid")

    exact = [
        item
        for item in projects
        if isinstance(item, dict) and str(item.get("name") or "") == name
    ]
    if not exact:
        raise ProjectDestinationNotFound(
            f"project is not present in the current producer catalogue: {name}"
        )
    if len(exact) != 1:
        raise ProjectDestinationConflict(
            f"project name is ambiguous in the current producer catalogue: {name}"
        )
    selected = exact[0]
    if selected.get("routing_status") != "valid":
        raise ProjectDestinationConflict(
            f"project routing is not valid in the current producer catalogue: {name}"
        )
    if selected.get("available") is not True:
        raise ProjectCatalogueUnavailable(
            f"project destination is not currently available: {name}"
        )

    state = str(selected.get("state") or "")
    root_kind = str(selected.get("root_kind") or "")
    if root_kind not in ROOT_KINDS:
        raise ProjectCatalogueUnavailable(
            f"project root_kind is not supported: {root_kind}"
        )
    if state == "active":
        if selected.get("automatic_routing_allowed") is not True:
            raise ProjectDestinationConflict(
                f"active project is not eligible for automatic routing: {name}"
            )
    elif state == "archived":
        if not allow_archived_write:
            raise ArchivedProjectWriteRequiresConfirmation(
                f"archived project requires explicit write confirmation/reactivation: {name}"
            )
        if selected.get("write_requires_confirmation") is not True:
            raise ProjectCatalogueUnavailable(
                "archived catalogue entry lacks the expected write-confirmation posture"
            )
    else:
        raise ProjectCatalogueUnavailable(f"unknown project state: {state}")

    roots = _configured_roots(root_paths)
    root = roots.get(root_kind)
    if root is None:
        raise ProjectCatalogueUnavailable(
            f"server root is not configured for {root_kind}"
        )
    relative = Path(str(selected.get("relative_root") or ""))
    if (
        not relative.parts
        or relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) != 1
    ):
        raise ProjectDestinationUnsafe(
            "catalogue relative_root must be exactly one child directory"
        )
    candidate = root / relative
    if candidate.is_symlink():
        raise ProjectDestinationUnsafe("project destination may not be a symlink")
    destination = candidate.resolve(strict=False)
    if not destination.is_relative_to(root):
        raise ProjectDestinationUnsafe("resolved project destination escaped configured root")
    if not destination.is_dir():
        raise ProjectCatalogueUnavailable(
            f"catalogued project directory is not currently available: {name}"
        )

    return {
        "name": name,
        "state": state,
        "root_kind": root_kind,
        "relative_root": str(relative),
        "path": destination,
        "automatic_routing_allowed": selected.get("automatic_routing_allowed") is True,
        "write_requires_confirmation": selected.get("write_requires_confirmation") is True,
        "governed_project_identity_asserted": False,
    }
