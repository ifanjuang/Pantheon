#!/usr/bin/env python3
"""Require explicit PR context for Role, Rite and governed-Space changes.

This check is intentionally documentary and deterministic. It verifies that a
pull request touching semantic owner surfaces declares the change level,
overlap analysis, consumers, migration posture and authority/runtime impact.
It does not decide whether a new Role, Rite or Space is semantically justified.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

SENSITIVE_EXACT = {
    "docs/governance/AGENTS.md",
    "docs/governance/GOVERNANCE_COLLEGE.md",
    "docs/governance/CARD_STACK_MODEL.md",
    "docs/governance/EVOLUTION_OF_ROLES_RITES_AND_SPACES.md",
}
SENSITIVE_PREFIXES = (
    "docs/governance/rites/",
    "docs/domain-packs/architecture/ROLE_",
)
REQUIRED_SECTIONS = (
    "Change level",
    "Observed need",
    "Existing owners checked",
    "Overlap analysis",
    "Affected consumers",
    "Migration and rollback",
    "Authority impact",
    "Runtime impact",
)
VALID_LEVELS = {"editorial", "guidance", "semantic"}
PLACEHOLDER_RE = re.compile(r"^(?:n/?a|none|todo|tbd|-)\.?$", re.IGNORECASE)


def changed_files(base_ref: str) -> list[str]:
    merge_base = subprocess.check_output(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    output = subprocess.check_output(
        ["git", "diff", "--name-only", merge_base, "HEAD"],
        cwd=ROOT,
        text=True,
    )
    return sorted(path for path in output.splitlines() if path)


def is_sensitive(path: str) -> bool:
    return path in SENSITIVE_EXACT or path.startswith(SENSITIVE_PREFIXES)


def section_content(body: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"(?im)^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return None
    content = match.group("body").strip()
    return content or None


def main() -> int:
    base_ref = os.environ.get("GOVERNANCE_BASE_REF", "").strip()
    pr_body = os.environ.get("PR_BODY", "")

    if not base_ref:
        print("SKIP: no GOVERNANCE_BASE_REF supplied.")
        return 0

    affected = [path for path in changed_files(base_ref) if is_sensitive(path)]
    if not affected:
        print("OK: no Role, Rite or governed-Space owner surface changed.")
        return 0

    failures: list[str] = []
    values: dict[str, str] = {}
    for heading in REQUIRED_SECTIONS:
        content = section_content(pr_body, heading)
        if content is None:
            failures.append(f"missing PR section: ## {heading}")
            continue
        values[heading] = content
        if PLACEHOLDER_RE.fullmatch(content):
            failures.append(f"placeholder-only PR section: ## {heading}")

    level_text = values.get("Change level", "")
    level = level_text.split(maxsplit=1)[0].strip().lower() if level_text else ""
    if level and level not in VALID_LEVELS:
        failures.append(
            "Change level must start with one of: editorial, guidance, semantic"
        )

    if failures:
        print("Roles / rites / spaces change guard failed:", file=sys.stderr)
        print("Affected owner surfaces:", file=sys.stderr)
        for path in affected:
            print(f"- {path}", file=sys.stderr)
        print("Required corrections:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(
            "This check verifies declared review context only; it does not judge "
            "semantic adequacy.",
            file=sys.stderr,
        )
        return 1

    print("OK: Role / Rite / governed-Space change context is declared.")
    print(f"Change level: {level}")
    for path in affected:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
