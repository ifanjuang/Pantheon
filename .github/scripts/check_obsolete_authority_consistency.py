#!/usr/bin/env python3
"""Fail closed when an obsolete governance document is indexed as active.

The per-file ``Status:`` header is the local status source. This check scans
existing Markdown documents under ``docs/governance/`` whose explicit header
contains ``obsolete``, ``superseded`` or ``retired``. Each such document must:

- have an exact table-row entry in the effective authority-index corpus; and
- have every exact matching row classified with one of the same retirement
  markers.

The effective corpus is the master ``AUTHORITY_INDEX.md`` plus only the
sub-indexes that the master registers. Prose references do not count. The
script is read-only and applies the repository baseline policy through
``GOVERNANCE_BASE_REF`` so pre-existing violations do not mask new drift.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = "docs/governance"
MASTER_INDEX = "docs/governance/AUTHORITY_INDEX.md"
SUBINDEX_PREFIX = "docs/governance/authority/"
RETIREMENT_RE = re.compile(r"\b(obsolete|superseded|retired)\b", re.IGNORECASE)
PATH_RE = re.compile(r"`((?:docs|schemas|templates|ai_logs|hermes)/[^`]+)`")


def git_text(ref: str, rel: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{rel}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return ""


def read_lines(rel: str, ref: str | None) -> list[str]:
    if ref is None:
        path = ROOT / rel
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    return git_text(ref, rel).splitlines()


def file_exists(rel: str, ref: str | None) -> bool:
    if ref is None:
        return (ROOT / rel).is_file()
    try:
        subprocess.check_output(
            ["git", "cat-file", "-e", f"{ref}:{rel}"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def governance_docs(ref: str | None) -> list[str]:
    if ref is None:
        return sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / DOCS_ROOT).rglob("*.md")
        )
    try:
        output = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", ref, DOCS_ROOT],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return []
    return sorted(path for path in output.splitlines() if path.endswith(".md"))


def explicit_status(lines: list[str]) -> str | None:
    for line in lines[:12]:
        if line.strip().lower().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return None


def master_table_rows(ref: str | None) -> list[str]:
    return [
        line
        for line in read_lines(MASTER_INDEX, ref)
        if line.lstrip().startswith("|")
    ]


def registered_subindexes(ref: str | None) -> list[str]:
    cited = {
        match.group(1).strip()
        for row in master_table_rows(ref)
        for match in PATH_RE.finditer(row)
    }
    return sorted(
        path
        for path in cited
        if path.startswith(SUBINDEX_PREFIX)
        and path.endswith(".md")
        and file_exists(path, ref)
    )


def effective_rows(ref: str | None) -> list[str]:
    rows = list(master_table_rows(ref))
    for rel in registered_subindexes(ref):
        rows.extend(
            line
            for line in read_lines(rel, ref)
            if line.lstrip().startswith("|")
        )
    return rows


def retired_docs(ref: str | None) -> dict[str, str]:
    found: dict[str, str] = {}
    for rel in governance_docs(ref):
        # Indexes classify other documents; their own descriptive status is not
        # an object-level retirement declaration.
        if rel == MASTER_INDEX or rel.startswith(SUBINDEX_PREFIX):
            continue
        # A template's Status line enumerates the values an authored document
        # may choose ("proposed | active doctrine | ... | superseded"). It
        # declares no status of its own, so reading one as a retirement makes
        # the template a permanently unindexable retired document.
        if Path(rel).name.startswith("_TEMPLATE"):
            continue
        status = explicit_status(read_lines(rel, ref))
        if status and RETIREMENT_RE.search(status):
            found[rel] = status
    return found


def violations(ref: str | None) -> dict[str, str]:
    rows = effective_rows(ref)
    found: dict[str, str] = {}

    for rel, status in retired_docs(ref).items():
        token = f"`{rel}`"
        matches = [row for row in rows if token in row]
        if not matches:
            found[f"retired-not-indexed|{rel}"] = (
                f"retired document is absent from the effective authority indexes: "
                f"{rel} (Status: {status})"
            )
            continue

        inconsistent = [row for row in matches if not RETIREMENT_RE.search(row)]
        if inconsistent:
            rendered = " || ".join(row.strip() for row in inconsistent)
            found[f"retired-indexed-active|{rel}"] = (
                f"retired document has an authority row without an obsolete/"
                f"superseded/retired classification: {rel}: {rendered}"
            )

    return found


def main() -> int:
    base_ref = os.environ.get("GOVERNANCE_BASE_REF") or None
    current = violations(None)
    baseline = violations(base_ref) if base_ref and base_ref != "HEAD" else {}
    new_keys = sorted(set(current) - set(baseline))

    checked = len(retired_docs(None))
    if new_keys:
        print("Obsolete authority consistency check failed:", file=sys.stderr)
        if base_ref:
            print(
                f"Baseline ref: {base_ref}; existing baseline violations are ignored.",
                file=sys.stderr,
            )
        for key in new_keys:
            print(f"- {current[key]}", file=sys.stderr)
        return 1

    print(
        "OK: obsolete authority consistency verified "
        f"for {checked} existing retired governance document(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
