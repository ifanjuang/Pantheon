#!/usr/bin/env python3
"""Read-only governance signal: how long each candidate has been left unresolved.

The repository creates candidates far more readily than it resolves them. The
promotion rule (`AUTHORITY_INDEX.md`, B-5) is deliberate about *how* a candidate
leaves that state, and it is explicit that age alone promotes nothing. This
check separates a candidate deliberately kept as one from a candidate nobody
has revisited.

It reports; it does not fail on age. A candidate leaves the report by promotion
with a referent, by archival, or by a dated human review cited in the document
header.

A review marker cites an explicit GitHub decision referent in this
repository:

    Candidacy reviewed: 2026-08-31 (PR #123)
    Candidacy reviewed: 2026-08-31 (issue #456)

A PR or issue reference is only a durable referent. Its existence, merge state,
CI status or automation output is not a human decision. Governance still
requires the cited discussion to contain an explicit human review/decision.
This checker deliberately validates the bounded reference syntax without
turning GitHub availability or CI success into authorization.

The marker is placed in the same header block as `Status:` and restarts the
clock. A malformed line, future date or invalid referent is a failure.

Where the start date comes from
-------------------------------
Not from a hand-written date. A written start date is a claim that goes stale
silently; the commit history is a fact. For each candidate the check walks its
commits backwards and finds when the document last entered the candidate state.

This repository's history begins at its own import commit, and the predecessor
repository is retired and is not a source dependency. For a document that
arrived with that import, the true candidacy start is not observable here. Such
rows are reported as `imported` rather than given a fabricated age.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
_HEADERS_PATH = Path(__file__).resolve().parent / "check_status_headers.py"

_CANDIDATE_HEAD = re.compile(r"^(candidate\b|to[\s/]+verify\b)", re.IGNORECASE)
_TO_VERIFY_HEAD = re.compile(r"\bto[\s/]+verify\b", re.IGNORECASE)

REVIEW_MARKER = re.compile(
    r"^\s*Candidacy\s+reviewed\s*:\s*(?P<date>\S+)\s*\((?P<record>[^)]+)\)\s*$",
    re.IGNORECASE,
)
REVIEW_PREFIX = re.compile(r"^\s*Candidacy\s+reviewed\s*:", re.IGNORECASE)
GITHUB_DECISION_REF = re.compile(r"^(?:PR|issue)\s+#[1-9]\d*$", re.IGNORECASE)

HEADER_LINES = 10
DEFAULT_THRESHOLD_DAYS = 180


def _load_status_headers():
    spec = importlib.util.spec_from_file_location("_check_status_headers", _HEADERS_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HEADERS = _load_status_headers()


def status_head(status: str) -> str:
    """Return the authority-class part of a Status value."""
    head = status.split("—")[0].split(" - ")[0]
    return head.strip().rstrip(".").strip()


def is_candidate(status: str | None) -> bool:
    """True when the Status line declares the candidate / to verify class."""
    if not status:
        return False
    head = status_head(status)
    return bool(_CANDIDATE_HEAD.match(head) or _TO_VERIFY_HEAD.search(head))


def _validate_review_referent(record: str) -> str | None:
    """Validate a bounded candidacy-review referent.

    Referents are deliberately limited to a PR or issue number in this same
    repository. The checker does not infer a human decision from GitHub state;
    that semantic requirement remains governance-owned and reviewable.
    """
    if GITHUB_DECISION_REF.fullmatch(record):
        return None
    return f"'Candidacy reviewed:' referent must be 'PR #<n>' or 'issue #<n>'; got {record!r}"


def parse_review_marker(
    lines: list[str], today: dt.date
) -> tuple[dt.date | None, str | None, str | None]:
    """Return (reviewed_date, decision_referent, error) for the optional header."""
    for raw in lines[:HEADER_LINES]:
        if not REVIEW_PREFIX.match(raw):
            continue
        match = REVIEW_MARKER.match(raw)
        if not match:
            return None, None, (
                "malformed 'Candidacy reviewed:' line; expected "
                "'Candidacy reviewed: YYYY-MM-DD (<decision referent>)'"
            )
        try:
            reviewed = dt.date.fromisoformat(match.group("date"))
        except ValueError:
            return None, None, (
                f"'Candidacy reviewed:' date is not ISO 8601: {match.group('date')!r}"
            )
        if reviewed > today:
            return None, None, (
                f"'Candidacy reviewed:' date is in the future: {reviewed.isoformat()}"
            )

        record = match.group("record").strip()
        error = _validate_review_referent(record)
        if error:
            return None, None, error
        return reviewed, record, None
    return None, None, None


def age_days(since: dt.date, today: dt.date) -> int:
    return (today - since).days


class _Blobs:
    """One `git cat-file --batch` process, so the history walk stays cheap."""

    def __init__(self, root: Path) -> None:
        self._proc = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def read(self, spec: str) -> str | None:
        assert self._proc.stdin and self._proc.stdout
        self._proc.stdin.write((spec + "\n").encode())
        self._proc.stdin.flush()
        header = self._proc.stdout.readline().decode("utf-8", "replace").strip()
        parts = header.split()
        if len(parts) < 3 or not parts[-1].isdigit():
            return None
        size = int(parts[-1])
        payload = self._proc.stdout.read(size)
        self._proc.stdout.read(1)
        return payload.decode("utf-8", "replace")

    def close(self) -> None:
        assert self._proc.stdin
        self._proc.stdin.close()
        self._proc.wait(timeout=10)


def _git(args: list[str]) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    )


def _root_commits() -> set[str]:
    try:
        return set(_git(["rev-list", "--max-parents=0", "HEAD"]).split())
    except subprocess.CalledProcessError:
        return set()


def _file_commits(rel: str) -> list[tuple[str, dt.date, str]]:
    """Commits touching `rel`, newest first, as (sha, author date, path then)."""
    try:
        raw = _git(
            ["log", "--follow", "--name-status", "--format=%x00%H%x09%aI", "--", rel]
        )
    except subprocess.CalledProcessError:
        return []

    rows: list[tuple[str, dt.date, str]] = []
    current = rel
    for block in raw.split("\0"):
        block = block.strip("\n")
        if not block:
            continue
        lines = block.splitlines()
        header = lines[0]
        if "\t" not in header:
            continue
        sha, stamp = header.split("\t", 1)
        rows.append((sha, dt.datetime.fromisoformat(stamp).date(), current))
        for entry in lines[1:]:
            parts = entry.split("\t")
            if parts and parts[0].startswith("R") and len(parts) >= 3:
                current = parts[1]
                break
    return rows


def candidacy_start(
    rel: str, blobs: _Blobs, roots: set[str]
) -> tuple[dt.date | None, str]:
    """When `rel` last entered candidate state, and how well we know it."""
    commits = _file_commits(rel)
    if not commits:
        return None, "unknown"
    start_sha, start_date, _ = commits[0]
    for sha, when, path_then in commits:
        _, status = HEADERS.detect_status(
            (blobs.read(f"{sha}:{path_then}") or "").splitlines()
        )
        if not is_candidate(status):
            break
        start_sha, start_date = sha, when
    provenance = "imported" if start_sha in roots else "observed"
    return start_date, provenance


def collect(today: dt.date) -> tuple[list[dict], list[str], dict[str, int]]:
    docs = HEADERS.git_docs(None)
    rows: list[dict] = []
    errors: list[str] = []
    classes: dict[str, int] = {"candidate": 0, "other": 0}

    blobs = _Blobs(ROOT)
    roots = _root_commits()
    try:
        for rel in docs:
            lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
            _, status = HEADERS.detect_status(lines)
            if not is_candidate(status):
                classes["other"] += 1
                continue
            classes["candidate"] += 1

            reviewed, record, error = parse_review_marker(lines, today)
            if error:
                errors.append(f"{rel}: {error}")
                continue

            since, provenance = candidacy_start(rel, blobs, roots)
            if reviewed and (since is None or reviewed > since):
                since, provenance = reviewed, "reviewed"
            rows.append(
                {
                    "path": rel,
                    "status_head": status_head(status or ""),
                    "since": since,
                    "provenance": provenance,
                    "record": record,
                    "age": age_days(since, today) if since else None,
                }
            )
    finally:
        blobs.close()

    rows.sort(key=lambda row: (-(row["age"] or -1), row["path"]))
    return rows, errors, classes


def render(
    rows: list[dict],
    classes: dict[str, int],
    threshold: int,
    today: dt.date,
    list_imported: bool = False,
) -> str:
    aged = [
        row for row in rows
        if row["age"] is not None and row["age"] >= threshold
    ]
    observed = [
        row for row in rows if row["provenance"] in {"observed", "reviewed"}
    ]
    imported = [row for row in rows if row["provenance"] == "imported"]

    out = [
        "# Candidacy aging",
        "",
        f"As of {today.isoformat()}. Candidate documents: **{classes['candidate']}** "
        f"of {classes['candidate'] + classes['other']} governance documents.",
        "",
        f"- unresolved for {threshold} days or more: **{len(aged)}**",
        f"- candidacy start observable here (a commit or a dated review): {len(observed)}",
        f"- candidacy start not observable (present at import): {len(imported)}",
        "",
        "Age does not promote anything. A row leaves this report by promotion "
        "with a referent, by archival, or by a dated human review with an "
        "explicit decision referent in the document header.",
        "",
    ]

    if aged:
        out += [
            f"## Unresolved for {threshold} days or more",
            "",
            "| Document | Class | Candidate since | Days | Start |",
            "|---|---|---|---|---|",
        ]
        for row in aged:
            out.append(
                f"| `{row['path']}` | {row['status_head']} | "
                f"{row['since'].isoformat()} | {row['age']} | {row['provenance']} |"
            )
        out.append("")
    else:
        out += [
            f"No candidate has been unresolved for {threshold} days or more.",
            "",
        ]

    if imported:
        out += [
            "## Start not observable",
            "",
            f"{len(imported)} candidate(s) were already candidates at the import "
            "commit. The predecessor repository is retired and is not a source "
            "dependency, so their real candidacy start is not recoverable here; "
            "the observable clock starts at the import "
            f"({imported[0]['since'].isoformat()}).",
            "",
        ]
        if list_imported:
            out += [f"- `{row['path']}`" for row in imported]
            out.append("")

    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--aging-threshold-days", type=int, default=DEFAULT_THRESHOLD_DAYS
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail when a candidate is unresolved past the threshold",
    )
    parser.add_argument("--today", default=None, help="ISO date, for reproducible runs")
    parser.add_argument(
        "--list-imported",
        action="store_true",
        help="name every candidate whose start predates this repository",
    )
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    rows, errors, classes = collect(today)
    report = render(
        rows,
        classes,
        args.aging_threshold_days,
        today,
        list_imported=args.list_imported,
    )
    print(report)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report + "\n")

    if errors:
        print("\nCandidacy review markers are not usable:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    if args.strict:
        aged = [
            row for row in rows
            if row["age"] is not None and row["age"] >= args.aging_threshold_days
        ]
        if aged:
            print(
                f"\n--strict: {len(aged)} candidate(s) unresolved past "
                f"{args.aging_threshold_days} days.",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
