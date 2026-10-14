"""Compatibility CLI for read-only update-availability verification."""

from __future__ import annotations

import sys

from .verification_cli import run_legacy


def run(argv: list[str] | None = None) -> int:
    return run_legacy("update", argv, prog="pantheon-verify-update")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
