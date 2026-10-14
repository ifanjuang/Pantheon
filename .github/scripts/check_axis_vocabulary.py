#!/usr/bin/env python3
"""Read-only check for E/V/K/C vocabulary.

Baseline dated 2026-06-11: when GOVERNANCE_BASE_REF is set, findings already
present on that ref are ignored. Axis-definition and reviewed support documents
listed below are exempt.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PREFIXES = ("docs", "schemas", "templates")
BAD_CONSEQUENCE = re.compile(r"(?i)(consequence|criticality|impact)[^\n]{0,80}\bC[0-5]\b")
BAD_APPROVAL = re.compile(r"(?i)(approval|required_approval|approval_required|ceiling)[^\n]{0,80}\bK[0-4]\b")
BAD_FIELD = re.compile(r"^\s*confidence\s*:", re.MULTILINE)

EXCLUDED = {
    "docs/governance/GLOSSARY.md",
    "docs/governance/OPEN_PR_RECONCILIATION.md",
    "docs/governance/TARGET_ARCHITECTURE.md",
    "CHANGELOG.md",
}


def git_text(ref: str, rel: str) -> str:
    try:
        return subprocess.check_output(["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return ""


def files(ref: str | None) -> list[str]:
    if ref is None:
        out: list[str] = []
        for prefix in PREFIXES:
            root = ROOT / prefix
            if root.exists():
                out.extend(p.relative_to(ROOT).as_posix() for p in root.rglob("*") if p.suffix.lower() in {".md", ".yaml", ".yml"})
        return sorted(out)
    try:
        raw = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref, *PREFIXES], cwd=ROOT, text=True)
    except subprocess.CalledProcessError:
        return []
    return sorted(p for p in raw.splitlines() if Path(p).suffix.lower() in {".md", ".yaml", ".yml"})


def read(rel: str, ref: str | None) -> str:
    return (ROOT / rel).read_text(encoding="utf-8") if ref is None else git_text(ref, rel)


def scan(ref: str | None) -> dict[str, str]:
    found: dict[str, str] = {}
    for rel in files(ref):
        if rel in EXCLUDED:
            continue
        text = read(rel, ref)
        lines = text.splitlines()
        # Keys omit the line number (they carry the line text instead) so a
        # baseline finding is not resurrected when unrelated edits shift it.
        for idx, line in enumerate(lines, start=1):
            short = line.strip()
            # A line that explicitly attributes C to approval is a
            # clarification, not a misuse (same spirit as GLOSSARY).
            if re.search(r"approval (only|ceiling|ceilings|axis)|reserved for approval", line, re.IGNORECASE):
                continue
            if BAD_CONSEQUENCE.search(line):
                found[f"{rel}|consequence|{short.lower()}"] = f"{rel}:{idx}: consequence-like context uses C-axis: {short}"
            if BAD_APPROVAL.search(line):
                found[f"{rel}|approval|{short.lower()}"] = f"{rel}:{idx}: approval-like context uses K-axis: {short}"
        if Path(rel).suffix.lower() in {".yaml", ".yml"}:
            for match in BAD_FIELD.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                # Honor the documented exception: a field explicitly marked
                # legacy/deprecated in its immediate context is allowed.
                context = "\n".join(lines[max(0, line_no - 2): line_no + 3]).lower()
                if "deprecated" in context or "legacy" in context:
                    continue
                short = lines[line_no - 1].strip() if line_no - 1 < len(lines) else "confidence:"
                found[f"{rel}|field|{short.lower()}"] = f"{rel}:{line_no}: YAML field 'confidence:' should be 'certainty:' unless explicitly legacy/deprecated"
    return found


def main() -> int:
    base = os.environ.get("GOVERNANCE_BASE_REF") or None
    current = scan(None)
    baseline = scan(base) if base and base != "HEAD" else {}
    new_keys = sorted(set(current) - set(baseline))
    if new_keys:
        print("Axis vocabulary check failed:", file=sys.stderr)
        if base:
            print(f"Baseline ref: {base}; existing baseline findings are ignored.", file=sys.stderr)
        for key in new_keys:
            print(f"- {current[key]}", file=sys.stderr)
        return 1
    print("OK: no new E/V/K/C vocabulary finding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
