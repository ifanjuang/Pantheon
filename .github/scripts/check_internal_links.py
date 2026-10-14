#!/usr/bin/env python3
"""Read-only governance check: internal path references must resolve or be explicit.

Baseline policy, dated 2026-06-11: when GOVERNANCE_BASE_REF is set, missing
references already present on that ref are treated as baseline exceptions. The
check fails only on missing references added outside that baseline.

The scanner ignores external-site citations in reference reviews and fictive paths
inside examples. API route segments such as ``/v1/hermes/...`` are not repository
paths and are ignored. The script never modifies files.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DOCS_PREFIX = "docs/governance"
REPOSITORY_PATH_PREFIXES = ("docs/", "schemas/", "templates/", "ai_logs/", "hermes/", "implementation/")
PATH_RE = re.compile(r"(?P<path>(?:docs|schemas|templates|ai_logs|hermes|implementation)/[A-Za-z0-9_./-]+)")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

EXCLUDED_PREFIXES = (
    "mcp-server/",
    "dashboard/",
    "operations/",
    "platform/",
    "examples/",
    "example/",
    "tmp/",
    "scratch/",
)

EXCLUDED_PATHS = {
    "docs/governance/ANSWER_VERIFICATION_GATE.md",
    "schemas/register_candidate.schema.yaml",
    # Deliberate non-canonical spelling shown as a counter-example under
    # "Do not use as canonical spelling" in GLOSSARY.md (canonical is hephaistos/).
    "hermes/profiles/hephaestus/",
    # Forward-looking target paths named in planning notes; not yet created.
    "docs/implementation/data-platform/",
    "docs/adapters/data-platform/",
    "schemas/evidence-memory/",
    "docs/governance/PANTHEON_EVIDENCE_MEMORY.md",
}

FICTIVE_MARKERS = (
    "example",
    "fictive",
    "fictional",
    "placeholder",
    "sample",
    "dummy",
    "toy",
)


def git_text(ref: str, rel: str) -> str:
    try:
        return subprocess.check_output(["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return ""


def git_docs(ref: str | None) -> list[str]:
    if ref is None:
        root = ROOT / DOCS_PREFIX
        return sorted(p.relative_to(ROOT).as_posix() for p in root.rglob("*.md"))
    try:
        raw = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref, DOCS_PREFIX], cwd=ROOT, text=True)
    except subprocess.CalledProcessError:
        return []
    return sorted(p for p in raw.splitlines() if p.endswith(".md"))


def read_lines(rel: str, ref: str | None) -> list[str]:
    if ref is None:
        return (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return git_text(ref, rel).splitlines()


def ref_exists(ref_path: str, base_ref: str | None) -> bool:
    if base_ref is None:
        return (ROOT / ref_path).exists()
    try:
        subprocess.check_output(["git", "cat-file", "-e", f"{base_ref}:{ref_path}"], cwd=ROOT, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def line_is_external_reference_context(rel: str, line: str) -> bool:
    if "/reference_reviews/" not in rel:
        return False
    return "http://" in line or "https://" in line or "github.com/" in line or "arxiv.org" in line


def line_is_fictive_context(line: str) -> bool:
    lower = line.lower()
    return any(marker in lower for marker in FICTIVE_MARKERS)


def path_match_is_api_route(line: str, match_start: int) -> bool:
    """Return True when a path-like token is the route segment after /v1/."""
    return line[:match_start].endswith("/v1/")


def normalize_candidate(raw: str, source_rel: str, line: str) -> str | None:
    raw = raw.strip().strip("`'\".,;:)]}")
    if not raw or raw.startswith(("http://", "https://", "mailto:", "#")):
        return None
    if line_is_external_reference_context(source_rel, line):
        return None
    if line_is_fictive_context(line):
        return None
    if any(raw.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return None
    if raw in EXCLUDED_PATHS:
        return None
    if raw.startswith("../") or raw.startswith("./"):
        candidate = (ROOT / source_rel).parent / raw
        try:
            return candidate.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return raw
    if raw.startswith(REPOSITORY_PATH_PREFIXES):
        return raw
    return None


def find_refs(rel: str, ref: str | None) -> list[tuple[int, str]]:
    refs: list[tuple[int, str]] = []
    for idx, line in enumerate(read_lines(rel, ref), start=1):
        for match in LINK_RE.finditer(line):
            found = normalize_candidate(match.group(1), rel, line)
            if found:
                refs.append((idx, found))
        for match in PATH_RE.finditer(line):
            # A route such as /v1/hermes/execution-admissions/... is an API
            # surface, not a repository path reference.
            if path_match_is_api_route(line, match.start()):
                continue
            # A path immediately followed by '*' is a glob/grouped row
            # (e.g. docs/governance/DATA_PLATFORM_*.md), not a concrete reference.
            if line[match.end():match.end() + 1] == "*":
                continue
            found = normalize_candidate(match.group("path"), rel, line)
            if found:
                refs.append((idx, found))
    return refs


def violations(ref: str | None) -> dict[str, str]:
    found: dict[str, str] = {}
    for rel in git_docs(ref):
        for line_no, target in find_refs(rel, ref):
            if not ref_exists(target, ref):
                # Key omits the line number so a baseline violation is not
                # resurrected when unrelated edits shift its line.
                key = f"{rel}|{target}"
                found[key] = f"{rel}:{line_no}: missing internal reference: {target}"
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    base_ref = os.environ.get("GOVERNANCE_BASE_REF") or None
    current = violations(None)
    baseline = violations(base_ref) if base_ref and base_ref != "HEAD" else {}
    new_keys = sorted(set(current) - set(baseline))

    if args.list:
        for message in current.values():
            print(message)
        if base_ref:
            print(f"\nBaseline ref: {base_ref} ({len(baseline)} exception(s))")

    if new_keys:
        print("Internal link/path check failed:", file=sys.stderr)
        if base_ref:
            print(f"Baseline ref: {base_ref}; existing baseline violations are ignored.", file=sys.stderr)
        for key in new_keys:
            print(f"- {current[key]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
