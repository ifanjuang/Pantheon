"""Read-only command-line entry point for APU dossier validation.

Validates a candidate Architecture Project Understanding dossier (a YAML file or
stdin) against the governance schemas and prints the gate posture as JSON. It
validates and reports only — it executes, canonizes and approves nothing. The
exit code reflects the validation result (0 = ok, 1 = errors), so the command can
gate a script; it never reflects or performs a side effect.

Usage::

    pantheon-apu-validate path/to/dossier.yaml
    cat dossier.yaml | pantheon-apu-validate -
"""

from __future__ import annotations

import argparse
import json
import sys

import yaml

from . import apu


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pantheon-apu-validate",
        description=(
            "Validate a candidate Architecture Project Understanding dossier "
            "against the governance schemas (read-only). Prints the gate posture "
            "as JSON; exit 0 if ok, 1 on schema/reference/gate errors."
        ),
    )
    parser.add_argument(
        "dossier",
        nargs="?",
        default="-",
        help="path to a YAML dossier, or '-' for stdin (default: stdin)",
    )
    args = parser.parse_args(argv)

    try:
        raw = _read(args.dossier)
    except OSError as exc:
        print(json.dumps({"result": "error", "problems": [f"cannot read dossier: {exc}"]}))
        return 1

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        print(json.dumps({"result": "error", "problems": [f"invalid YAML: {exc}"]}))
        return 1

    report = apu.validate_apu_dossier(data)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("result") == "ok" else 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
