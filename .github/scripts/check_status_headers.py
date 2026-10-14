#!/usr/bin/env python3
"""Read-only governance check: every governance Markdown file declares a Status header.

Baseline policy, dated 2026-06-11: when GOVERNANCE_BASE_REF is set, violations
already present on that ref are treated as baseline exceptions. The check fails
only on violations added outside that baseline.

Use --list to print checked files and detected statuses without changing files.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DOCS_PREFIX = "docs/governance"

# Families observed in the corpus and aligned with AUTHORITY_INDEX.md vocabulary.
ACCEPTED_FAMILIES = (
    "canonical",
    "active doctrine",
    "active support",
    "support doctrine",
    "support review",
    "candidate",
    "to verify",
    "validation-only",
    "external reference",
    "reference",
    "implementation artifact",
    "voluntarily absent",
    "volontairement absent",
    "obsolete",
    "refused",
    "stub",
    "example",
    "illustrative",
)


def git_lines(ref: str, rel: str) -> list[str]:
    try:
        raw = subprocess.check_output(["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return []
    return raw.splitlines()


def git_docs(ref: str | None) -> list[str]:
    if ref is None:
        root = ROOT / DOCS_PREFIX
        return sorted(
            p.relative_to(ROOT).as_posix()
            for p in root.rglob("*.md")
            if p.name.lower() != "readme.md"
        )
    try:
        raw = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref, DOCS_PREFIX], cwd=ROOT, text=True)
    except subprocess.CalledProcessError:
        return []
    return sorted(p for p in raw.splitlines() if p.endswith(".md") and not p.lower().endswith("/readme.md"))


def read_lines(rel: str, ref: str | None) -> list[str]:
    if ref is None:
        return (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return git_lines(ref, rel)


def detect_status(lines: list[str]) -> tuple[int | None, str | None]:
    for idx, line in enumerate(lines[:10], start=1):
        if line.strip().lower().startswith("status:"):
            return idx, line.split(":", 1)[1].strip()
    return None, None


def violations(ref: str | None) -> dict[str, str]:
    found: dict[str, str] = {}
    for rel in git_docs(ref):
        line_no, status = detect_status(read_lines(rel, ref))
        if status is None:
            found[f"{rel}|missing-status"] = f"{rel}: missing Status: line in first 10 lines"
            continue
        if not any(token in status.lower() for token in ACCEPTED_FAMILIES):
            found[f"{rel}|unsupported-status|{status.lower()}"] = f"{rel}:{line_no}: unsupported Status value: {status!r}"
    return found


def current_rows() -> list[str]:
    rows: list[str] = []
    for rel in git_docs(None):
        line_no, status = detect_status(read_lines(rel, None))
        rows.append(f"{rel}:{line_no or '?'}: {status or '<missing>'}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    base_ref = os.environ.get("GOVERNANCE_BASE_REF") or None
    current = violations(None)
    baseline = violations(base_ref) if base_ref and base_ref != "HEAD" else {}
    new_keys = sorted(set(current) - set(baseline))

    if args.list:
        print("\n".join(current_rows()))
        if base_ref:
            print(f"\nBaseline ref: {base_ref} ({len(baseline)} exception(s))")

    if new_keys:
        print("Status header check failed:", file=sys.stderr)
        if base_ref:
            print(f"Baseline ref: {base_ref}; existing baseline violations are ignored.", file=sys.stderr)
        for key in new_keys:
            print(f"- {current[key]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
