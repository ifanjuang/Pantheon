#!/usr/bin/env python3
"""Compare the Hermes runtime pinned by Pantheon with a HarnessRouter release.

This is a qualification preflight only. It does not install, activate, dispatch,
authorize, adopt, or admit Evidence. A version mismatch blocks a *matched* A/B;
it does not by itself reject UHP as a protocol.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_HERMES_PIN = re.compile(
    r"""hermes-agent==(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9_.+-]*)?)"""
)


class CompatibilityError(RuntimeError):
    pass


def discover_harnessrouter_hermes_version(entrypoint: Path) -> str:
    try:
        text = entrypoint.read_text(encoding="utf-8")
    except OSError as exc:
        raise CompatibilityError(f"cannot read HarnessRouter entrypoint: {exc}") from exc
    versions = sorted({match.group("version") for match in _HERMES_PIN.finditer(text)})
    if not versions:
        raise CompatibilityError("HarnessRouter entrypoint exposes no exact hermes-agent== pin")
    if len(versions) != 1:
        raise CompatibilityError(
            "HarnessRouter entrypoint exposes multiple Hermes pins: " + ", ".join(versions)
        )
    return versions[0]


def build_report(
    *,
    harnessrouter_version: str,
    harnessrouter_ref: str,
    protocol_version: str,
    harnessrouter_hermes_version: str,
    pantheon_hermes_version: str,
    pantheon_hermes_ref: str,
) -> dict:
    exact_match = harnessrouter_hermes_version == pantheon_hermes_version
    return {
        "schema": "pantheon/uhp-hermes-runtime-compatibility/v1",
        "status": "ready_for_matched_ab" if exact_match else "blocked_runtime_mismatch",
        "harnessrouter": {
            "version": harnessrouter_version,
            "ref": harnessrouter_ref,
            "protocol_version": protocol_version,
            "observed_hermes_version": harnessrouter_hermes_version,
        },
        "pantheon_hermes": {
            "version": pantheon_hermes_version,
            "ref": pantheon_hermes_ref,
        },
        "exact_hermes_version_match": exact_match,
        "matched_ab_allowed": exact_match,
        "interpretation": (
            "The stock HarnessRouter release and Pantheon target the same Hermes version."
            if exact_match
            else (
                "The stock HarnessRouter release and Pantheon target different Hermes versions. "
                "Transport characterization may continue, but a causal native-vs-UHP comparison "
                "must not attribute differences to UHP until the runtime mismatch is removed."
            )
        ),
        "non_equivalences": [
            "protocol conformance != runtime comparability",
            "runtime version match != authorization",
            "transport characterization != UHP adoption",
            "technical receipt != Evidence",
        ],
        "authority": {
            "installs_runtime": False,
            "activates_runtime": False,
            "dispatches_task": False,
            "authorizes_effect": False,
            "adopts_transport": False,
            "admits_evidence": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harnessrouter-entrypoint", type=Path, required=True)
    parser.add_argument("--harnessrouter-version", required=True)
    parser.add_argument("--harnessrouter-ref", required=True)
    parser.add_argument("--protocol-version", required=True)
    parser.add_argument("--pantheon-hermes-version", required=True)
    parser.add_argument("--pantheon-hermes-ref", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-match",
        action="store_true",
        help="return non-zero when a matched A/B is not currently valid",
    )
    args = parser.parse_args(argv)

    try:
        observed = discover_harnessrouter_hermes_version(args.harnessrouter_entrypoint)
        report = build_report(
            harnessrouter_version=args.harnessrouter_version,
            harnessrouter_ref=args.harnessrouter_ref,
            protocol_version=args.protocol_version,
            harnessrouter_hermes_version=observed,
            pantheon_hermes_version=args.pantheon_hermes_version,
            pantheon_hermes_ref=args.pantheon_hermes_ref,
        )
    except CompatibilityError as exc:
        report = {
            "schema": "pantheon/uhp-hermes-runtime-compatibility/v1",
            "status": "invalid_upstream_contract",
            "error": str(exc),
            "matched_ab_allowed": False,
            "authority": {
                "installs_runtime": False,
                "activates_runtime": False,
                "dispatches_task": False,
                "authorizes_effect": False,
                "adopts_transport": False,
                "admits_evidence": False,
            },
        }

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")

    if report["status"] == "invalid_upstream_contract":
        return 1
    if args.require_match and not report["matched_ab_allowed"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
