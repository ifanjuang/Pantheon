#!/usr/bin/env python3
"""Read-only governance check: authority-bearing docs are visible in the authority map.

The authority map is AUTHORITY_INDEX.md plus the sub-indexes under
docs/governance/authority/ that it registers (AUTHORITY_INDEX_DECOMPOSITION_PLAN.md).
A governance doc counts as indexed when it is named in a Markdown table row of
the master index or of any registered sub-index, or when a grouped row covers it.
Prose mentions do not count: indexing is a deliberate row, not a passing
reference. The master index alone still defines the authority vocabulary;
sub-indexes only list placement.

Coverage policy after Pantheon-Next#787 convergence:
- every current-authority governance document (Status beginning with
  ``canonical`` or ``active``) must be indexed now; current-authority gaps are
  not grandfathered by GOVERNANCE_BASE_REF;
- candidate coverage keeps the historical baseline policy: when
  GOVERNANCE_BASE_REF is set, candidate or missing-path violations already
  present on that exact base remain baseline exceptions and only new violations
  fail the check.

This closes the staged owner-debt guard introduced during Pantheon-Next#787: once an owner is
current authority, its Authority Index placement must be explicit and reviewable.

Sub-index policy, dated 2026-07-05 (decomposition plan step PR C, explicitly
approved): a sub-index under docs/governance/authority/ that is itself
registered in AUTHORITY_INDEX.md (its path appears in the master file)
extends the coverage corpus. An unregistered file under authority/ extends
nothing: the master index remains the sole interpreter and the single
registration point.

The script never modifies files.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
from pantheon_mcp.authority_index import (  # noqa: E402
    PATH_RE,
    grouped_covers,
    load_authority_catalog,
)

DOCS_PREFIX = "docs/governance"
INDEX_REL = "docs/governance/AUTHORITY_INDEX.md"
SUBINDEX_DIR = "docs/governance/authority"
FUTURE_OR_GROUPED = {
    "docs/governance/DATA_PLATFORM_*.md",
    "docs/governance/reference_reviews/",
    "docs/governance/rites/",
    "templates/",
    "examples/",
    "schemas/",
    "tests/",
    "operations/",
    "platform/",
    "Docker*",
    ".env*",
}


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


def git_docs(ref: str | None) -> list[str]:
    if ref is None:
        root = ROOT / DOCS_PREFIX
        return sorted(p.relative_to(ROOT).as_posix() for p in root.rglob("*.md"))
    try:
        raw = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", ref, DOCS_PREFIX],
            cwd=ROOT,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return sorted(p for p in raw.splitlines() if p.endswith(".md"))


def read_lines(rel: str, ref: str | None) -> list[str]:
    if ref is None:
        return (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return git_text(ref, rel).splitlines()


def file_exists(rel: str, ref: str | None) -> bool:
    if ref is None:
        return (ROOT / rel).exists()
    try:
        subprocess.check_output(
            ["git", "cat-file", "-e", f"{ref}:{rel}"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def detect_status(lines: list[str]) -> str | None:
    for line in lines[:10]:
        if line.strip().lower().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return None


def current_authority_docs(ref: str | None) -> list[str]:
    rows: list[str] = []
    for rel in git_docs(ref):
        status = detect_status(read_lines(rel, ref))
        if not status:
            continue
        normalized = status.lower()
        if normalized.startswith("canonical") or normalized.startswith("active"):
            rows.append(rel)
    return rows


def candidate_docs(ref: str | None) -> list[str]:
    rows: list[str] = []
    for rel in git_docs(ref):
        if rel.lower().endswith("/readme.md"):
            continue
        status = detect_status(read_lines(rel, ref))
        if status and "candidate" in status.lower():
            rows.append(rel)
    return rows


def master_rows(ref: str | None) -> str:
    """Markdown table-row lines of the master index only."""
    return "\n".join(
        line for line in read_lines(INDEX_REL, ref) if line.lstrip().startswith("|")
    )


def registered_subindexes(ref: str | None) -> list[str]:
    """Registered sub-indexes that are allowed to extend coverage."""
    if ref is None:
        return load_authority_catalog(ROOT)["registered_subindexes"]
    cited = {m.group(1).strip() for m in PATH_RE.finditer(master_rows(ref))}
    prefix = SUBINDEX_DIR + "/"
    return sorted(
        p
        for p in cited
        if p.startswith(prefix) and p.endswith(".md") and file_exists(p, ref)
    )


def index_text(ref: str | None) -> str:
    """Combined table rows of the master index and registered sub-indexes."""
    rows: list[str] = []
    for rel in [INDEX_REL, *registered_subindexes(ref)]:
        for line in read_lines(rel, ref):
            if line.lstrip().startswith("|"):
                rows.append(line)
    return "\n".join(rows)


def indexed_paths(ref: str | None) -> set[str]:
    if ref is None:
        return set(load_authority_catalog(ROOT)["coverage_paths"])
    return {m.group(1).strip() for m in PATH_RE.finditer(index_text(ref))}


def _grouped_covers(groups: set[str], rel: str) -> bool:
    """Return whether a registered directory/glob row covers ``rel``."""
    return grouped_covers(groups, rel)


def violations(ref: str | None) -> dict[str, str]:
    paths = indexed_paths(ref)
    group_root = DOCS_PREFIX + "/"
    groups = {
        p
        for p in paths
        if (p.endswith("/") or "*" in p) and p.startswith(group_root) and p != group_root
    }
    found: dict[str, str] = {}

    for rel in current_authority_docs(ref):
        if rel not in paths and not _grouped_covers(groups, rel):
            found[f"current-authority-not-indexed|{rel}"] = (
                f"current-authority doc not indexed in the authority map: {rel}"
            )

    for rel in candidate_docs(ref):
        if rel not in paths and not _grouped_covers(groups, rel):
            found[f"candidate-not-indexed|{rel}"] = (
                f"candidate doc not indexed in the authority map: {rel}"
            )

    for target in sorted(paths):
        if target in FUTURE_OR_GROUPED or "*" in target:
            continue
        if target.endswith("/"):
            if ref is None:
                ok = (ROOT / target).is_dir()
            else:
                ok = target in FUTURE_OR_GROUPED
            if not ok:
                found[f"missing-dir|{target}"] = (
                    f"authority map references missing directory: {target}"
                )
        elif not file_exists(target, ref):
            found[f"missing-path|{target}"] = (
                f"authority map references missing path: {target}"
            )
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    base_ref = os.environ.get("GOVERNANCE_BASE_REF") or None
    current = violations(None)
    baseline = violations(base_ref) if base_ref and base_ref != "HEAD" else {}
    failing_keys = sorted(
        key
        for key in current
        if key.startswith("current-authority-not-indexed|") or key not in baseline
    )

    if args.list:
        print("Current-authority docs:")
        print("\n".join(current_authority_docs(None)))
        print("\nCandidate docs:")
        print("\n".join(candidate_docs(None)))
        print("\nIndexed paths:")
        print("\n".join(sorted(indexed_paths(None))))
        if base_ref:
            print(f"\nBaseline ref: {base_ref} ({len(baseline)} exception(s))")

    if failing_keys:
        print("Authority index coverage check failed:", file=sys.stderr)
        if base_ref:
            print(
                "Baseline candidate/missing-path violations remain ignored; "
                "current-authority coverage is enforced without grandfathering.",
                file=sys.stderr,
            )
        for key in failing_keys:
            print(f"- {current[key]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
