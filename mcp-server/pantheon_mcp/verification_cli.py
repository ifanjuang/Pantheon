"""Shared read-only CLI for the bounded verification family.

This module centralizes only command-line mechanics: selecting one of the five
explicit verifiers, reading caller-provided YAML, serializing the report and
mapping the positive verdict to exit code 0. Each verifier keeps its own module,
evidence schema and domain logic.

The registry below is static program metadata. It is not a plugin registry,
runtime router, installer, scheduler, provider router or activation system.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import sys
from collections.abc import Callable

import yaml

from . import backup, exposure, install, observability, update


Verifier = Callable[[dict], dict]


@dataclass(frozen=True)
class VerificationSpec:
    verify: Verifier
    success_verdict: str
    description: str


VERIFIERS: dict[str, VerificationSpec] = {
    "install": VerificationSpec(
        verify=install.verify_install,
        success_verdict="green",
        description="install / liveness evidence",
    ),
    "observability": VerificationSpec(
        verify=observability.verify_observability,
        success_verdict="observable",
        description="signal / freshness / error evidence",
    ),
    "backup": VerificationSpec(
        verify=backup.verify_backup,
        success_verdict="protected",
        description="backup / freshness / restore evidence",
    ),
    "exposure": VerificationSpec(
        verify=exposure.verify_exposure,
        success_verdict="guarded",
        description="reach / authentication / scope evidence",
    ),
    "update": VerificationSpec(
        verify=update.verify_update,
        success_verdict="current",
        description="current / available version evidence",
    ),
}


def _error(problem: str) -> dict:
    return {
        "result": "error",
        "verdict": "invalid",
        "problems": [problem],
        "capability_gaps": [],
        "posture": "read-only",
        "decides": False,
    }


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _load(path: str) -> tuple[dict | None, dict | None]:
    try:
        raw = _read(path)
    except OSError as exc:
        return None, _error(f"cannot read evidence: {exc}")

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, _error(f"invalid YAML: {exc}")

    return data, None


def run_kind(kind: str, evidence_path: str) -> int:
    """Run one statically declared verifier and print its report as JSON."""

    spec = VERIFIERS.get(kind)
    if spec is None:
        report = _error(f"unknown verification kind: {kind}")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    evidence, error = _load(evidence_path)
    report = error if error is not None else spec.verify(evidence)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("verdict") == spec.success_verdict else 1


def run_legacy(
    kind: str,
    argv: list[str] | None = None,
    *,
    prog: str,
) -> int:
    """Compatibility entry point used by the five historical commands."""

    spec = VERIFIERS[kind]
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            f"Verify {spec.description} from provided evidence (read-only). "
            f"Prints JSON; exits 0 only for verdict '{spec.success_verdict}'. "
            "It gathers no evidence, performs no operation and decides nothing."
        ),
    )
    parser.add_argument(
        "evidence",
        nargs="?",
        default="-",
        help="path to a YAML evidence file, or '-' for stdin (default: stdin)",
    )
    args = parser.parse_args(argv)
    return run_kind(kind, args.evidence)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pantheon-verify",
        description=(
            "Classify caller-provided verification evidence through one explicit "
            "read-only Pantheon verifier. The command probes, installs, updates, "
            "writes and approves nothing."
        ),
    )
    parser.add_argument("kind", choices=tuple(VERIFIERS))
    parser.add_argument(
        "evidence",
        nargs="?",
        default="-",
        help="path to a YAML evidence file, or '-' for stdin (default: stdin)",
    )
    args = parser.parse_args(argv)
    return run_kind(args.kind, args.evidence)


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
