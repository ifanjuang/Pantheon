#!/usr/bin/env python3
"""Validate bounded provisioner handoff contract examples without executing anything."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "catalog" / "schemas"
EXAMPLES = ROOT / "catalog" / "examples"

SCHEMA_BY_KEY = {
    "installation_candidate": "installation-candidate.schema.json",
    "handoff_candidate": "provisioner-handoff-candidate.schema.json",
    "execution_result_candidate": "execution-result-candidate.schema.json",
    "health_observation": "health-observation.schema.json",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(name: str, value: object, schema_path: Path) -> list[str]:
    validator = Draft202012Validator(load_json(schema_path), format_checker=FormatChecker())
    errors = []
    for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{name}.{location}: {error.message}")
    return errors


def validate_chain(chain: dict[str, object], source: Path) -> list[str]:
    errors: list[str] = []
    for key, schema_name in SCHEMA_BY_KEY.items():
        if key not in chain:
            errors.append(f"{source}: missing {key}")
            continue
        errors.extend(validate_schema(key, chain[key], SCHEMAS / schema_name))

    if errors:
        return errors

    installation = chain["installation_candidate"]
    handoff = chain["handoff_candidate"]
    result = chain["execution_result_candidate"]
    health = chain["health_observation"]
    assert isinstance(installation, dict)
    assert isinstance(handoff, dict)
    assert isinstance(result, dict)
    assert isinstance(health, dict)

    installation_id = installation["metadata"]["id"]
    handoff_id = handoff["metadata"]["id"]
    result_id = result["metadata"]["id"]

    if handoff["metadata"]["installation_candidate_id"] != installation_id:
        errors.append(f"{source}: handoff does not reference installation candidate")
    if result["metadata"]["handoff_candidate_id"] != handoff_id:
        errors.append(f"{source}: execution result does not reference handoff candidate")
    if health["metadata"]["execution_result_candidate_id"] != result_id:
        errors.append(f"{source}: health observation does not reference execution result candidate")

    allowed = set(installation["spec"]["allowed_provisioners"])
    selected = handoff["spec"]["selected_provisioner"]
    if selected not in allowed:
        errors.append(f"{source}: selected provisioner {selected!r} is not allowed by installation candidate")

    if handoff["governance"]["handoff_authorized"]:
        errors.append(f"{source}: fixture must not self-authorize handoff")
    if handoff["governance"]["execution_authorized"]:
        errors.append(f"{source}: fixture must not self-authorize execution")
    if result["governance"]["runtime_success_is_evidence"]:
        errors.append(f"{source}: runtime success must not be treated as evidence")
    if health["governance"]["health_is_safety_claim"]:
        errors.append(f"{source}: health must not be treated as a safety claim")
    if health["governance"]["health_is_admission"]:
        errors.append(f"{source}: health must not be treated as admission")

    return errors


def main() -> int:
    files = sorted(EXAMPLES.glob("*-handoff-chain.json"))
    if not files:
        print("FAIL: no handoff chain examples found")
        return 1

    failures: list[str] = []
    for path in files:
        raw = load_json(path)
        if not isinstance(raw, dict):
            failures.append(f"{path}: expected object")
            continue
        failures.extend(validate_chain(raw, path))

    if failures:
        print(f"FAIL: {len(failures)} handoff contract issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"OK: validated {len(files)} bounded handoff chain example(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
