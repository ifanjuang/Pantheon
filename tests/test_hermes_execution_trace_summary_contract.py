"""Schema checks for the optional Hermes execution trace summary."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = yaml.safe_load(
    (ROOT / "schemas" / "work_issue_slice.schema.yaml").read_text(encoding="utf-8")
)
EXAMPLES = ROOT / "docs" / "examples" / "hermes_execution_trace_summary"


def _validator() -> jsonschema.Draft202012Validator:
    sub_schema = {
        "$schema": SCHEMA["$schema"],
        "$ref": "#/$defs/normalized_hermes_return",
        "$defs": SCHEMA["$defs"],
    }
    jsonschema.Draft202012Validator.check_schema(sub_schema)
    return jsonschema.Draft202012Validator(
        sub_schema,
        format_checker=jsonschema.FormatChecker(),
    )


def test_complete_and_partial_examples_validate_against_work_issue_contract() -> None:
    validator = _validator()
    for name in ("complete.json", "partial.json"):
        payload = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
        validator.validate(payload)


def test_execution_trace_summary_remains_optional() -> None:
    _validator().validate(
        {
            "outcome": "partial",
            "summary": "Legacy bounded return remains valid during migration.",
            "trace_refs": ["hermes://runs/legacy"],
        }
    )
