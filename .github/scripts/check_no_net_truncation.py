#!/usr/bin/env python3
"""Generic tripwire: a long governance doc must not be silently truncated.

`check_no_truncation.py` protects a small, hand-curated MANIFEST of files by
absolute length and end-sentinel. This check generalizes the *class* of defect
it was built for — a connector returning a partial read that is written back as
a full-file replacement, silently dropping the tail — to *every* long
governance Markdown file, without needing each one enumerated in advance.

It compares each modified `docs/governance/**/*.md` file against the PR base
(GOVERNANCE_BASE_REF). A file that was long at the base and loses a large,
disproportionate share of its lines is flagged as a probable truncation.

The intent is to catch the *additive-commit-that-secretly-deletes* shape: an
edit whose purpose is to add (index a doc, add a section) but whose net effect
is a big deletion — intent and effect disagree.

It does not edit, fix or rewrite anything. It only reports.

Deliberate shrinks (a real split, a real removal) are legitimate. Acknowledge
them explicitly by adding the file's repo-relative path to
`.github/scripts/truncation_ack.txt`; that edit is itself a reviewable signal.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = "docs/governance"
ACK_FILE = ROOT / ".github" / "scripts" / "truncation_ack.txt"

# A file only qualifies as a "long curated doc" once it crosses this length at
# the base ref; short notes churn freely and are out of scope.
MIN_LONG_LINES = 200
# Flag only when BOTH hold: a large absolute drop AND a large proportional drop.
# Requiring both avoids firing on ordinary section edits while still catching
# the 094d0a9-style tail loss (369 -> 268: -101 lines, -27%).
MIN_ABSOLUTE_DROP = 80
MAX_KEPT_RATIO = 0.75  # current must keep > 75% of base lines, else suspect


def git_lines(ref: str, rel: str) -> int | None:
    """Line count of `rel` at `ref`, or None if it does not exist there."""
    try:
        out = subprocess.check_output(
            ["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None
    return len(out.splitlines())


def modified_md_paths(base: str) -> list[str]:
    """Repo-relative governance .md files modified between base and the tree."""
    try:
        raw = subprocess.check_output(
            ["git", "diff", "--name-status", base, "--", AREA],
            cwd=ROOT, text=True,
        )
    except subprocess.CalledProcessError:
        return []
    paths: list[str] = []
    for row in raw.splitlines():
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        # Only modifications can truncate. Additions have no base length;
        # whole-file deletions (D) and renames (R) are explicit, visible acts.
        if status.startswith("M") and path.endswith(".md"):
            paths.append(path)
    return paths


def load_ack() -> set[str]:
    if not ACK_FILE.exists():
        return set()
    acked: set[str] = set()
    for line in ACK_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            acked.add(line)
    return acked


def main() -> int:
    base = os.environ.get("GOVERNANCE_BASE_REF")
    if not base or base == "HEAD":
        print("OK: no base ref; net-truncation check is a no-op for this run.")
        return 0

    ack = load_ack()
    failures: list[str] = []

    for rel in modified_md_paths(base):
        if rel in ack:
            continue
        base_lines = git_lines(base, rel)
        if base_lines is None or base_lines < MIN_LONG_LINES:
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        cur_lines = len(path.read_text(encoding="utf-8").splitlines())
        drop = base_lines - cur_lines
        if drop >= MIN_ABSOLUTE_DROP and cur_lines <= base_lines * MAX_KEPT_RATIO:
            pct = round(100 * drop / base_lines)
            failures.append(
                f"{rel}: {base_lines} -> {cur_lines} lines "
                f"(-{drop}, -{pct}%); probable truncation"
            )

    if failures:
        print("FAIL: long governance files lost a large share of their lines:")
        for f in failures:
            print(f"  {f}")
        print("")
        print("A connector that returns a partial read of a long file must not be")
        print("used as full-file replacement content. Edit long files in place")
        print("(anchored replacement), or restore a lost tail from git history.")
        print("")
        print("If the shrink is deliberate (a real split or removal), add the")
        print("file's repo-relative path to .github/scripts/truncation_ack.txt")
        print("in the same PR.")
        return 1

    print("OK: no long governance file shows a truncation-shaped net deletion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
