"""Setuptools build hooks for generated Pantheon contract package data.

The canonical schema source remains the monorepo-root ``schemas/`` tree. Before
building a wheel or sdist, this hook stages the complete schema tree under
``mvp_vertical/_generated_contracts``. That directory is ignored by Git and
exists solely so a built artifact can validate contracts when installed without
a repository checkout.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

PROJECT_ROOT = Path(__file__).resolve().parent
MONOREPO_ROOT = PROJECT_ROOT.parent
PACKAGE_ROOT = PROJECT_ROOT / "mvp_vertical"
GENERATED_ROOT = PACKAGE_ROOT / "_generated_contracts"
GENERATED_SCHEMAS = GENERATED_ROOT / "schemas"
MANIFEST_PATH = PACKAGE_ROOT / "contract_manifest.py"

_manifest_module = runpy.run_path(str(MANIFEST_PATH))
CONTRACT_PATHS: dict[str, str] = dict(_manifest_module["CONTRACT_PATHS"])
CANONICAL_REPOSITORY = str(_manifest_module["CANONICAL_REPOSITORY"])


def _git_run(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(MONOREPO_ROOT), *args],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _git_revision() -> str | None:
    result = _git_run("rev-parse", "HEAD")
    if result is None or result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value if len(value) == 40 else None


def _schema_tree_dirty() -> bool | None:
    result = _git_run("status", "--porcelain", "--untracked-files=all", "--", "schemas")
    if result is None or result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_existing_payload() -> None:
    manifest_path = GENERATED_ROOT / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("generated Pantheon contract manifest is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("generated Pantheon contract manifest is invalid") from exc
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or not files:
        raise RuntimeError("generated Pantheon contract manifest has no file digests")
    for relative, expected in files.items():
        path = GENERATED_ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"generated Pantheon contract payload is missing: {relative}")
        if _sha256(path) != expected:
            raise RuntimeError(f"generated Pantheon contract payload drifted: {relative}")
    missing_contracts = [
        relative for relative in CONTRACT_PATHS.values() if not (GENERATED_ROOT / relative).is_file()
    ]
    if missing_contracts:
        raise RuntimeError(
            "generated Pantheon contract payload misses declared contracts: "
            + ", ".join(missing_contracts)
        )


def _stage_contracts() -> None:
    canonical_root = MONOREPO_ROOT / "schemas"
    if not canonical_root.is_dir():
        # An sdist already carries the generated payload produced from the
        # canonical repository at sdist creation time.
        _verify_existing_payload()
        return

    shutil.rmtree(GENERATED_ROOT, ignore_errors=True)
    shutil.copytree(canonical_root, GENERATED_SCHEMAS)

    files: dict[str, str] = {}
    for path in sorted(GENERATED_SCHEMAS.rglob("*")):
        if path.is_file():
            relative = path.relative_to(GENERATED_ROOT).as_posix()
            files[relative] = _sha256(path)

    for name, relative in CONTRACT_PATHS.items():
        if not (GENERATED_ROOT / relative).is_file():
            raise RuntimeError(
                f"canonical Pantheon contract declared by {name!r} is missing: {relative}"
            )

    repository_revision = _git_revision()
    source_tree_dirty = _schema_tree_dirty()
    source_revision = repository_revision if source_tree_dirty is False else None
    manifest = {
        "kind": "pantheon_generated_contract_payload",
        "source_repository": CANONICAL_REPOSITORY,
        "source_revision": source_revision,
        "repository_revision": repository_revision,
        "source_tree_dirty": source_tree_dirty,
        "authority_transfer": False,
        "generated": True,
        "files": files,
    }
    (GENERATED_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class build_py(_build_py):
    def run(self) -> None:
        _stage_contracts()
        super().run()


class sdist(_sdist):
    def run(self) -> None:
        _stage_contracts()
        super().run()


setup(cmdclass={"build_py": build_py, "sdist": sdist})
