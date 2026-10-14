#!/usr/bin/env python3
"""Tripwire: curated canonical governance files must not be silently truncated.

A recurring failure mode is a connector returning a *partial* read of a long file,
which is then written back as a full-file replacement — silently dropping the tail.

This check fails CI when a curated file falls below its reviewed minimum line count
or loses its required end-sentinel. The thresholds describe the current intentional
shape of each curated file, not a requirement that doctrine stay verbose. If a file
legitimately converges to a smaller owner map, update the manifest in the same PR.

It does not edit, fix or rewrite anything. It only reports.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

# relative path -> (minimum line count, tail sentinel that must appear near the end)
MANIFEST = {
    "docs/governance/MODULES.md": (130, "does not need to own."),
    "docs/governance/AUTHORITY_INDEX.md": (300, "explicit approval in their own work package."),
}

# How many trailing lines the sentinel must appear within.
TAIL_WINDOW = 20


def main() -> int:
    failures = []
    for rel, (min_lines, sentinel) in MANIFEST.items():
        path = ROOT / rel
        if not path.exists():
            failures.append(f"{rel}: file is missing")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) < min_lines:
            failures.append(
                f"{rel}: {len(lines)} lines, below minimum {min_lines} "
                f"(possible truncation; if intentional, lower the minimum in "
                f".github/scripts/check_no_truncation.py)"
            )
        tail = "\n".join(lines[-TAIL_WINDOW:])
        if sentinel not in tail:
            failures.append(
                f"{rel}: required end-sentinel not found in the last {TAIL_WINDOW} "
                f"lines: {sentinel!r} (the tail may have been truncated; if the "
                f"ending changed on purpose, update the sentinel in "
                f".github/scripts/check_no_truncation.py)"
            )

    if failures:
        print("FAIL: curated governance files may have been truncated:")
        for f in failures:
            print(f"  {f}")
        print("")
        print("A connector that returns a partial read must not be used as")
        print("full-file replacement content. Restore the complete source or")
        print("update this manifest only when a deliberate convergence is reviewed.")
        return 1

    print("OK: curated governance files retain their reviewed size and end-sentinel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
