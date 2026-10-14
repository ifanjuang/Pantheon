#!/usr/bin/env python3
"""Fail-closed check for the repository packaging and release contract."""

from __future__ import annotations

import os
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[a-zA-Z0-9.+-]*)?$")
CHANGELOG_VERSION_RE = re.compile(r"^##\s+([0-9][^\s]*)", re.MULTILINE)


def check_contract(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    root_config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    mcp_config = tomllib.loads(
        (root / "mcp-server/pyproject.toml").read_text(encoding="utf-8")
    )
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_match = CHANGELOG_VERSION_RE.search(changelog)

    if "project" in root_config or "build-system" in root_config:
        problems.append(
            "root pyproject.toml must configure tools only; root packaging is disabled"
        )
    rejection_shim = (root / "setup.py").read_text(encoding="utf-8")
    if "root is non-distributable" not in rejection_shim:
        problems.append("setup.py must explicitly reject fallback root packaging")
    dev_requirements = (root / "requirements-dev.txt").read_text(encoding="utf-8")
    if "pytest" not in dev_requirements or "governance-ci.txt" not in dev_requirements:
        problems.append("requirements-dev.txt must declare root test dependencies")
    if not VERSION_RE.fullmatch(version):
        problems.append(f"VERSION is not a supported package version: {version!r}")

    changelog_version = changelog_match.group(1) if changelog_match else None
    if changelog_version != version:
        problems.append(
            f"CHANGELOG head {changelog_version!r} does not match VERSION {version!r}"
        )

    project = mcp_config.get("project", {})
    if project.get("name") != "pantheon-mcp-server":
        problems.append("mcp-server is not named pantheon-mcp-server")
    if project.get("version") != version:
        problems.append(
            f"MCP metadata version {project.get('version')!r} does not match "
            f"VERSION {version!r}"
        )
    if project.get("license") != "MIT":
        problems.append("MCP license must use the SPDX string 'MIT'")
    if mcp_config.get("tool", {}).get("setuptools", {}).get("packages") != [
        "pantheon_mcp"
    ]:
        problems.append("MCP wheel must retain an explicit pantheon_mcp package list")

    ref_type = os.environ.get("GITHUB_REF_TYPE")
    ref_name = os.environ.get("GITHUB_REF_NAME")
    if ref_type == "tag" and ref_name != f"v{version}":
        problems.append(
            f"published tag {ref_name!r} must equal the current version tag v{version}"
        )
    return problems


def main() -> int:
    problems = check_contract()
    if problems:
        print("Packaging contract check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    publication = (
        f"published tag v{version}"
        if os.environ.get("GITHUB_REF_TYPE") == "tag"
        else "unreleased repository checkpoint"
    )
    print(
        "OK: root is non-distributable; MCP metadata, changelog and VERSION "
        f"agree on {version} ({publication})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
