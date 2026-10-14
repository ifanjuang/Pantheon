"""Compatibility CLI for read-only exposure-surface verification."""

from __future__ import annotations

import sys

from .verification_cli import run_legacy


def run(argv: list[str] | None = None) -> int:
    return run_legacy("exposure", argv, prog="pantheon-verify-exposure")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
