#!/usr/bin/env python3
"""Reject affirmative wording that makes Pantheon sound like an execution runtime.

This is the extracted form of the former inline Governance CI guard. Keeping the
logic in one importable script lets CI and the read-only Governance Doctor use the
same check without duplicating a large Python program inside YAML.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DIR = ROOT / "docs" / "governance"

FORBIDDEN = [
    "Pantheon executes",
    "Pantheon Agent Runtime",
    "Pantheon tool runtime",
    "automatic memory promotion",
    "hidden workflow runtime",
    "provider router",
    "scheduler",
    "queue",
]

NEGATION = re.compile(
    r"\b("
    r"must not|do not|does not|did not|is not|are not|will not|would not|"
    r"cannot|can ?not|may not|should not|shall not|must never|never|none of|"
    r"without|forbidden|prohibited|refus(e|es|ed|al|ing)?|"
    r"reject(s|ed|ion|ing)?|disallowed|denied|excluded|incompatible|"
    r"intentionally absent|voluntarily not|not implemented|not migrated|"
    r"non implémenté|absent|avoid(s|ed|ing)?|"
    r"belongs outside|outside pantheon|on the hermes side|"
    r"stays? on the|remains? on the|stays? outside|remains? outside|"
    r"external (execution|runtime|tool|action|capability|capabilities)|"
    r"runtime state|boundary rule|stub present|hermes-side|hermes side|"
    r"risky capabilities|risks?:|drift|"
    r"requires? (a |an )?task contract|task contract requirement|"
    r"requires? approval|remove(s|d|al)?|reformulate|transform or remove|"
    r"\bno\b|governance[- ]only|governance-first|read[- ]only|policy[- ]gated|"
    r"not (recreate|implement|introduce|expose|grant|run|execute|approve|own|"
    r"migrate|install|schedule|queue|route|promote|a |an |another |the )"
    r")",
    re.IGNORECASE,
)

# A governed review/decision queue is a human-decision surface, not a runtime
# message queue.
QUEUE_OK = re.compile(
    r"review[- ]?queue|decision queue|impact[- ]?queue|"
    r"queue of governed decisions|governed (review|decision) queue",
    re.IGNORECASE,
)


def section_context(lines: list[str], idx: int) -> str:
    start = 0
    for position in range(idx, -1, -1):
        if re.match(r"^#{1,6}\s", lines[position]):
            start = position
            break
    return "\n".join(lines[start : idx + 1])


def find_failures() -> list[tuple[str, int, str, str]]:
    failures: list[tuple[str, int, str, str]] = []
    for md in sorted(GOVERNANCE_DIR.rglob("*.md")):
        # Reference reviews describe third-party runtimes. The guard targets
        # Pantheon's own doctrine claiming to execute.
        if "reference_reviews/" in md.as_posix():
            continue
        lines = md.read_text(encoding="utf-8").splitlines()
        head = "\n".join(lines[:3])
        for index, line in enumerate(lines):
            for phrase in FORBIDDEN:
                pattern = r"\b" + re.escape(phrase) + r"\b"
                if not re.search(pattern, line, re.IGNORECASE):
                    continue
                context = section_context(lines, index)
                if NEGATION.search(context):
                    continue
                if phrase == "queue" and (
                    QUEUE_OK.search(line)
                    or QUEUE_OK.search(context)
                    or QUEUE_OK.search(head)
                ):
                    continue
                failures.append(
                    (
                        str(md.relative_to(ROOT)),
                        index + 1,
                        phrase,
                        line.strip(),
                    )
                )
    return failures


def main() -> int:
    failures = find_failures()
    if failures:
        print(
            f"FAIL: {len(failures)} affirmative runtime-suggesting occurrence(s) found:"
        )
        for path, lineno, phrase, text in failures:
            print(f"  {path}:{lineno}: phrase='{phrase}' line='{text}'")
        print()
        print("Governance files must not suggest that Pantheon executes,")
        print("schedules, queues, routes providers, runs hidden workflows,")
        print("or promotes memory automatically. Each occurrence must appear")
        print("under context that establishes negation, exclusion or external scope.")
        return 1

    print("OK: no affirmative runtime-suggesting phrase detected in docs/governance/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
