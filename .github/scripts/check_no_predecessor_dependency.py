#!/usr/bin/env python3
"""Fail when the active tree depends on the retired Pantheon-OS repository.

Historical traces may name the predecessor. Active configuration, code, templates
and doctrine must not clone it, fetch it, mount it, read it through an environment
variable or treat it as an authority source.
"""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

HISTORICAL_PREFIXES = (
    "ai_logs/",
    "docs/audits/",
    "docs/history/",
)
HISTORICAL_FILES = {
    "CHANGELOG.md",
}
TECHNICAL_FIXTURE_FILES = {
    ".github/scripts/check_no_predecessor_dependency.py",
    "tests/test_repository_guards.py",
}
TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

ACTIVE_PATTERNS = {
    "https predecessor remote": re.compile(
        r"https?://(?:www\.)?github\.com/ifanjuang/Pantheon-OS(?:\.git)?",
        re.IGNORECASE,
    ),
    "ssh predecessor remote": re.compile(
        r"git@github\.com:ifanjuang/Pantheon-OS(?:\.git)?",
        re.IGNORECASE,
    ),
    "predecessor environment variable": re.compile(
        r"\bPANTHEON[_-]?OS(?:_REPO|_PATH|_ROOT|_URL)?\b",
        re.IGNORECASE,
    ),
    "relative predecessor checkout": re.compile(
        r"(?:^|[\s'\"])(?:\.\./)+Pantheon-OS(?:/|[\s'\"]|$)",
        re.IGNORECASE,
    ),
    "absolute predecessor checkout": re.compile(
        r"/(?:[^\s'\"]+/)*Pantheon-OS(?:/|[\s'\"]|$)",
        re.IGNORECASE,
    ),
}


def is_historical(path: Path, root: Path = ROOT) -> bool:
    relative = path.relative_to(root).as_posix()
    return relative in HISTORICAL_FILES or relative.startswith(HISTORICAL_PREFIXES)


def iter_active_text_files(root: Path = ROOT):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if (
            relative.startswith(".git/")
            or relative in TECHNICAL_FIXTURE_FILES
            or is_historical(path, root)
        ):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitmodules":
            yield path


def find_dependencies(root: Path = ROOT) -> list[tuple[str, int, str, str]]:
    failures: list[tuple[str, int, str, str]] = []

    forbidden_snapshot = root / "legacy" / "Pantheon-OS"
    if forbidden_snapshot.exists():
        failures.append(
            (
                forbidden_snapshot.relative_to(root).as_posix(),
                0,
                "vendored predecessor snapshot",
                "active tree contains a Pantheon-OS snapshot",
            )
        )

    for path in iter_active_text_files(root):
        relative = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            # Vendored minified bundles can contain very long lines. Every
            # active pattern requires "pantheon", so skip regex evaluation
            # early when the literal is absent instead of backtracking over
            # unrelated third-party source.
            if "pantheon" not in line.casefold():
                continue
            for label, pattern in ACTIVE_PATTERNS.items():
                if pattern.search(line):
                    failures.append((relative, lineno, label, line.strip()))
    return failures


def main() -> int:
    failures = find_dependencies()
    if failures:
        print(
            f"FAIL: {len(failures)} active predecessor dependency occurrence(s) found:"
        )
        for path, lineno, label, text in failures:
            location = f"{path}:{lineno}" if lineno else path
            print(f"  {location}: {label}: {text}")
        print()
        print("Pantheon Next must remain self-contained. Historical references belong")
        print("only in logs, audits or changelogs.")
        return 1

    print("OK: no active Pantheon-OS checkout, remote, path or environment dependency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
