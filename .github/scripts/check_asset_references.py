#!/usr/bin/env python3
"""Read-only governance check: local references in shipped assets must resolve.

``check_internal_links.py`` scans Markdown under ``docs/governance/`` only. The
26 HTML pages and the CSS they load are published from ``docs/`` and were
covered by nothing, so a card or a call-to-action could point at a file that
does not exist and stay green through every CI run.

This check resolves every *local* reference in the HTML, CSS and JavaScript we
publish:

- HTML ``src=`` / ``href=`` attributes;
- CSS ``url(...)`` and ``@import``;
- JavaScript relative module specifiers.

External URLs, fragments, ``data:`` payloads and template placeholders such as
``${expr}`` are ignored: they are not repository paths. The script never
modifies files and contacts nothing.

Baseline policy, matching the sibling checks: when ``GOVERNANCE_BASE_REF`` is
set, findings already present on that ref are treated as baseline exceptions so
the check fails only on newly introduced breakage.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SUFFIXES = {".html", ".css", ".js"}

HTML_REF = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", re.IGNORECASE)
CSS_IMPORT = re.compile(r"""@import\s+['"]([^'"]+)['"]""", re.IGNORECASE)
JS_SPECIFIER = re.compile(
    r"""(?:\bfrom|\bimport|\bnew\s+Worker)\s*\(?\s*["'](\.[^"']*)["']""",
)

# A reference we must not treat as a repository path.
IGNORED_PREFIXES = (
    "http://",
    "https://",
    "//",
    "data:",
    "mailto:",
    "tel:",
    "javascript:",
    "#",
    "?",
)


def tracked_files(ref: str | None) -> set[str]:
    args = ["git", "ls-files"] if ref is None else ["git", "ls-tree", "-r", "--name-only", ref]
    try:
        raw = subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return set()
    return set(raw.split())


def read(rel: str, ref: str | None) -> str:
    if ref is None:
        path = ROOT / rel
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return ""


def references(rel: str, text: str) -> list[tuple[int, str]]:
    suffix = Path(rel).suffix.lower()
    if suffix == ".html":
        patterns = (HTML_REF,)
    elif suffix == ".css":
        patterns = (CSS_URL, CSS_IMPORT)
    else:
        patterns = (JS_SPECIFIER,)

    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            for match in pattern.finditer(line):
                found.append((number, match.group(1).strip()))
    return found


def is_repository_path(target: str) -> bool:
    if not target or target.startswith(IGNORED_PREFIXES):
        return False
    # Template placeholders (`${repo + x}`) and encoded SVG fragments (`%23n`)
    # are produced at runtime, not shipped files.
    if "${" in target or target.startswith("%23"):
        return False
    return True


def resolve(rel: str, target: str) -> str | None:
    """Repository-relative path a reference points at, or None if it escapes."""
    # Tailscale Serve mounts the Workspace Cockpit below /workspace/ while
    # the local server serves these same files from its static root.
    if target == "/workspace/":
        return "implementation/workspace_cockpit/static/index.html"
    if target.startswith("/workspace/"):
        candidate = ROOT / "implementation/workspace_cockpit/static" / target[len("/workspace/"):]
    else:
        base = (ROOT / rel).parent
        candidate = (ROOT / target.lstrip("/")) if target.startswith("/") else (base / target)
    try:
        return candidate.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None


def scan(ref: str | None) -> dict[str, str]:
    tracked = tracked_files(ref)
    found: dict[str, str] = {}

    for rel in sorted(tracked):
        if Path(rel).suffix.lower() not in SUFFIXES:
            continue
        text = read(rel, ref)
        if not text:
            continue
        for number, raw in references(rel, text):
            target = raw.split("#", 1)[0].split("?", 1)[0]
            if not is_repository_path(target):
                continue
            resolved = resolve(rel, target)
            if resolved is None:
                # Key omits the line number so unrelated edits do not resurrect
                # a baseline finding.
                found[f"{rel}|{raw}"] = f"{rel}:{number}: reference escapes the repository: {raw}"
            elif resolved not in tracked and not (ROOT / resolved).exists():
                found[f"{rel}|{raw}"] = f"{rel}:{number}: unresolved reference {raw} -> {resolved}"
    return found


def main() -> int:
    base = os.environ.get("GOVERNANCE_BASE_REF") or None
    current = scan(None)
    baseline = scan(base) if base and base != "HEAD" else {}
    new_keys = sorted(set(current) - set(baseline))

    if new_keys:
        print("Asset reference check failed:", file=sys.stderr)
        if base:
            print(f"Baseline ref: {base}; existing baseline findings are ignored.", file=sys.stderr)
        for key in new_keys:
            print(f"- {current[key]}", file=sys.stderr)
        return 1

    checked = sum(1 for rel in tracked_files(None) if Path(rel).suffix.lower() in SUFFIXES)
    print(f"OK: local references resolve across {checked} HTML/CSS/JS files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
