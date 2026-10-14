"""Read-only access to the governance core.

The server never writes. Every read is confined to the repository root so a
crafted key or path cannot escape the governed corpus.
"""

from __future__ import annotations

import os
from pathlib import Path


class RepoNotFound(RuntimeError):
    pass


def find_repo_root() -> Path:
    """Locate the Pantheon Next repository root.

    Order: PANTHEON_REPO_PATH environment variable, then walk up from this
    module looking for CLAUDE.md (the repository marker).
    """
    env = os.environ.get("PANTHEON_REPO_PATH")
    if env:
        root = Path(env).resolve()
        if not (root / "CLAUDE.md").is_file():
            raise RepoNotFound(
                f"PANTHEON_REPO_PATH={env} does not contain CLAUDE.md"
            )
        return root
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").is_file():
            return parent
    raise RepoNotFound(
        "could not locate the Pantheon Next repository; set PANTHEON_REPO_PATH"
    )


def read_repo_text(rel_path: str, root: Path | None = None) -> str:
    """Read a file inside the repository. Rejects any path that resolves
    outside the repository root."""
    root = root or find_repo_root()
    target = (root / rel_path).resolve()
    if root != target and root not in target.parents:
        raise PermissionError(f"path escapes the repository root: {rel_path}")
    return target.read_text(encoding="utf-8")


def repo_file_exists(rel_path: str, root: Path | None = None) -> bool:
    root = root or find_repo_root()
    target = (root / rel_path).resolve()
    if root != target and root not in target.parents:
        return False
    return target.is_file()
