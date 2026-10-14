"""Read-only snapshot helpers for qualification harnesses.

The snapshot observes tracked worktree material without treating Git links as
ordinary files. It is qualification support only: a clean snapshot or clean
status is not Evidence, authorization, deployment truth or professional
currentness.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path


class GitMaterialSnapshotError(RuntimeError):
    pass


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _index_entries(repo: Path) -> list[tuple[str, str, str]]:
    raw = subprocess.check_output(
        ["git", "-C", str(repo), "ls-files", "-s", "-z"],
    )
    entries: list[tuple[str, str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_id, stage = metadata.decode("ascii").split()
        except ValueError as exc:
            raise GitMaterialSnapshotError("unexpected git ls-files entry") from exc
        if stage != "0":
            raise GitMaterialSnapshotError(
                f"unmerged index entry is not a stable qualification baseline: {raw_path!r}"
            )
        path = raw_path.decode("utf-8", errors="surrogateescape")
        entries.append((mode, object_id, path))
    return entries


def snapshot_tracked_material(repo: str | Path) -> dict[str, dict[str, str]]:
    """Return a deterministic snapshot of tracked worktree material.

    Ordinary files are hashed from the bytes currently present in the worktree.
    Symlinks hash their link target text rather than following the target.
    Gitlinks/submodules record the exact index object id and are deliberately not
    opened as filesystem files; `git status` remains the complementary detector
    for a checked-out submodule whose HEAD or worktree changed.
    """

    root = Path(repo).resolve()
    result: dict[str, dict[str, str]] = {}
    for mode, object_id, relative_path in _index_entries(root):
        path = root / relative_path
        if mode == "160000":
            result[relative_path] = {
                "kind": "gitlink",
                "index_object_id": object_id,
            }
            continue
        if mode == "120000":
            try:
                target = os.readlink(path)
            except OSError as exc:
                raise GitMaterialSnapshotError(
                    f"cannot read tracked symlink: {relative_path}"
                ) from exc
            payload = os.fsencode(target)
            result[relative_path] = {
                "kind": "symlink",
                "sha256": _sha256(payload),
            }
            continue
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise GitMaterialSnapshotError(
                f"cannot read tracked file: {relative_path}"
            ) from exc
        result[relative_path] = {
            "kind": "file",
            "sha256": _sha256(payload),
        }
    return result


def porcelain_status(repo: str | Path) -> list[str]:
    """Return Git porcelain status lines, including untracked material."""

    root = Path(repo).resolve()
    raw = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        text=True,
    )
    return raw.splitlines()
