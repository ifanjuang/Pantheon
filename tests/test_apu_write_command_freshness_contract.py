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
    attribute_claim = yaml.safe_load(
        (APU / "attribute_claim.schema.yaml").read_text(encoding="utf-8")
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
            (
                "attribute_claim.schema.yaml",
                Resource.from_contents(attribute_claim, default_specification=DRAFT202012),
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
    assert schema["properties"]["operation"]["enum"] == [
        "add_match_to_existing_object",
        "add_claim",
        "supersede_claim",
    ]
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


def _claim_command(operation: str = "add_claim") -> dict:
    example = _example()
    for field in ("source_representation", "identity_relation_claim", "expected_object_revision", "match_axis"):
        example.pop(field, None)
    example["operation"] = operation
    example["claim_family"] = "attribute"
    example["claim"] = {
        "attribute_claim_id": "claim.door-017.width.v2",
        "subject_ref": {"entity_type": "stable_object", "entity_id": "OBJ-DOOR-017"},
        "attribute_key": "geometry.width",
        "value": {"value_type": "number", "value": 0.93},
        "assertion_mode": "observed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
    }
    if operation == "supersede_claim":
        example["superseded_claim_ref"] = "claim.door-017.width.v1"
    return example


def test_claim_commands_validate_with_owner_freshness_only() -> None:
    validator = _validator()
    for operation in ("add_claim", "supersede_claim"):
        validator.validate(_claim_command(operation))
    candidate = _claim_command()
    candidate.pop("expected_owner_revision")
    assert list(validator.iter_errors(candidate))


def test_claim_command_carries_one_candidate_claim_and_no_match_effect() -> None:
    validator = _validator()
    for mutate in (
        lambda c: c.pop("claim"),
        lambda c: c.pop("claim_family"),
        lambda c: c["claim"].__setitem__("proof_status", "accepted_as_support"),
        lambda c: c.__setitem__("expected_object_revision", 1),
        lambda c: c.__setitem__("source_representation", _example()["source_representation"]),
    ):
        candidate = _claim_command()
        mutate(candidate)
        assert list(validator.iter_errors(candidate)), "claim command shape was not enforced"


def test_only_supersede_claim_names_a_replaced_claim() -> None:
    validator = _validator()
    replacing = _claim_command("supersede_claim")
    replacing.pop("superseded_claim_ref")
    assert list(validator.iter_errors(replacing))
    adding = _claim_command("add_claim")
    adding["superseded_claim_ref"] = "claim.door-017.width.v1"
    assert list(validator.iter_errors(adding))
    match = _example()
    match["superseded_claim_ref"] = "claim.door-017.width.v1"
    assert list(validator.iter_errors(match))


def test_identity_alignment_is_not_a_claim_write() -> None:
    candidate = _claim_command()
    candidate["claim_family"] = "relation"
    candidate["claim"] = dict(_example()["identity_relation_claim"])
    assert list(_validator().iter_errors(candidate))
