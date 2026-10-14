#!/usr/bin/env python3
"""Compile a bounded contradictory-review payload into candidate review output.

Hermes or another admitted runtime may invoke this adapter with an already
bounded Task Contract payload. The adapter performs no tool execution, repair,
approval, dispatch, Evidence admission or memory promotion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mvp_vertical.contradictory_review import report_from_payload


def _read_payload(path: Path | None) -> dict:
    raw = path.read_text(encoding="utf-8") if path else sys.stdin.read()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("contradictory review input must be a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="JSON input; stdin when omitted")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        rendered = json.dumps(
            report_from_payload(_read_payload(args.input)).as_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        print(f"contradictory review rejected: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
