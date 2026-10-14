"""Read-only command-line entry point for the verification preset reader.

Validates a per-module verification preset (a YAML file or stdin) against its
schema and prints the verification plan as JSON: for each active verification, its
thresholds and the evidence fields a producer should gather. It runs no
verification, gathers no evidence, probes nothing and decides nothing.

The exit code lets the command gate a script: 0 when the preset is valid and
projects a plan, 1 on schema errors or an input error. It never reflects or
performs a side effect.

Usage::

    pantheon-load-verification-preset path/to/preset.yaml
    cat preset.yaml | pantheon-load-verification-preset -
"""

from __future__ import annotations

import argparse
import json
import sys

import yaml

from . import presets


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pantheon-load-verification-preset",
        description=(
            "Validate a per-module verification preset and project it into a "
            "verification plan as JSON (read-only). Exit 0 when valid, 1 on schema "
            "or input errors. It runs no verification and decides nothing."
        ),
    )
    parser.add_argument(
        "preset",
        nargs="?",
        default="-",
        help="path to a YAML preset, or '-' for stdin (default: stdin)",
    )
    args = parser.parse_args(argv)

    try:
        raw = _read(args.preset)
    except OSError as exc:
        print(json.dumps({"result": "error", "problems": [f"cannot read preset: {exc}"]}))
        return 1

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        print(json.dumps({"result": "error", "problems": [f"invalid YAML: {exc}"]}))
        return 1

    report = presets.load_verification_preset(data)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("result") == "ok" else 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
