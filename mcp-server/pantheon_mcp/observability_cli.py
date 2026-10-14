"""Compatibility CLI for read-only observability verification."""

from __future__ import annotations

import sys

from .verification_cli import run_legacy


def run(argv: list[str] | None = None) -> int:
    return run_legacy("observability", argv, prog="pantheon-verify-observability")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
