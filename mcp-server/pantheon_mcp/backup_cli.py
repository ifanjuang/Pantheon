"""Compatibility CLI for read-only backup / recoverability verification."""

from __future__ import annotations

import sys

from .verification_cli import run_legacy


def run(argv: list[str] | None = None) -> int:
    return run_legacy("backup", argv, prog="pantheon-verify-backup")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
