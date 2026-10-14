"""Contract tests for H2 APU write-command freshness."""

from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parents[1]
APU = ROOT / "schemas" / "architecture-project-understanding"
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-project-understanding"


def _validator() -> jsonschema.Draft202012Validator:
    schema = yaml.safe_load((APU / "write_command_candidate.schema.yaml").read_text(encoding="utf-8"))
    shared = yaml.safe_load((APU / "shared.schema.yaml").read_text(encoding="utf-8"))
    source_representation = yaml.safe_load(
        (APU / "source_representation.schema.yaml").read_text(encoding="utf-8")
    )
    relation_claim = yaml.safe_load(
        (APU / "relation_claim.schema.yaml").read_text(encoding="utf-8")
    )
    registry = Registry().with_resources(
        [
            (
                "shared.schema.yaml",
                Resource.from_contents(shared, default_specification=DRAFT202012),
            ),
            (
                "source_representation.schema.yaml",
                Resource.from_contents(
                    source_representation, default_specification=DRAFT202012
                ),
            ),
            (
                "relation_claim.schema.yaml",
                Resource.from_contents(relation_claim, default_specification=DRAFT202012),
            ),
        ]
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        registry=registry,
        format_checker=jsonschema.FormatChecker(),
    )


def _example() -> dict:
    return yaml.safe_load(
        (EXAMPLES / "write_command_candidate.example.yaml").read_text(encoding="utf-8")
    )


def test_write_command_example_validates_with_freshness() -> None:
    example = _example()
    _validator().validate(example)
    assert example["operation"] == "add_match_to_existing_object"
    assert example["expected_owner_revision"] >= 1
    assert example["expected_object_revision"] >= 1
    assert example["match_axis"] in {"cross_index", "cross_source", "cross_level"}
    representation = example["source_representation"]
    relation = example["identity_relation_claim"]
    assert relation["subject_ref"]["entity_id"] == representation["representation_id"]
    assert relation["object_ref"]["entity_type"] == "stable_object"
    assert relation["proof_status"] == "candidate"
    assert "source_candidate_ref" not in example
    assert "target_stable_object_ref" not in example
    assert "source_artifact_ref" not in example


def test_write_command_requires_project_and_target_revisions() -> None:
    validator = _validator()
    for field in ("project_ref", "expected_owner_revision", "expected_object_revision"):
        candidate = _example()
        candidate.pop(field)
        errors = list(validator.iter_errors(candidate))
        assert errors, f"write command unexpectedly accepts missing {field}"


def test_write_command_refuses_non_positive_target_revisions() -> None:
    validator = _validator()
    for field in ("expected_owner_revision", "expected_object_revision"):
        candidate = _example()
        candidate[field] = 0
        errors = list(validator.iter_errors(candidate))
        assert errors, f"write command unexpectedly accepts stale sentinel {field}=0"


def test_write_command_remains_candidate_only() -> None:
    schema = yaml.safe_load((APU / "write_command_candidate.schema.yaml").read_text(encoding="utf-8"))
    assert schema["properties"]["operation"]["const"] == "add_match_to_existing_object"
    assert schema["x-boundary"]["runtime_execution"] is False
    assert schema["x-boundary"]["automatic_apu_write"] is False
    assert schema["x-boundary"]["automatic_canonization"] is False
    assert schema["x-boundary"]["approval_engine"] is False


def test_command_requires_exact_canonical_effect_payloads() -> None:
    validator = _validator()
    for field in ("source_representation", "identity_relation_claim"):
        candidate = _example()
        candidate.pop(field)
        errors = list(validator.iter_errors(candidate))
        assert errors, f"write command unexpectedly accepts missing {field}"


def test_command_rejects_redundant_effect_references() -> None:
    validator = _validator()
    for field, value in (
        ("source_candidate_ref", "REP-OTHER"),
        ("target_stable_object_ref", "OBJ-OTHER"),
        ("source_artifact_ref", "document.other"),
    ):
        candidate = _example()
        candidate[field] = value
        errors = list(validator.iter_errors(candidate))
        assert errors, f"write command unexpectedly accepts redundant {field}"


def test_effect_remains_candidate_identity_alignment() -> None:
    validator = _validator()
    mutations = (
        ("source_representation", "proof_status", "accepted_as_support"),
        ("identity_relation_claim", "relation_type", "spatial.contains"),
        ("identity_relation_claim", "assertion_mode", "human_asserted"),
        ("identity_relation_claim", "proof_status", "accepted_as_support"),
    )
    for owner, field, value in mutations:
        candidate = _example()
        candidate[owner][field] = value
        errors = list(validator.iter_errors(candidate))
        assert errors, f"write command unexpectedly accepts {owner}.{field}={value}"
