from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-proof-register"
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-proof-register"
SPEC = ROOT / "docs" / "domain-packs" / "architecture" / "PROOF_REGISTER_IMPLEMENTATION_SPEC.md"


def _yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def test_document_family_does_not_persist_one_universal_current_version() -> None:
    schema = _yaml(SCHEMAS / "document_family.schema.yaml")
    example = _yaml(EXAMPLES / "document_family.example.yaml")
    spec = SPEC.read_text(encoding="utf-8")

    assert "current_authoritative_version_id" not in schema["properties"]
    assert "current_authoritative_version_id" not in example
    assert schema["x-currentness"]["persisted_universal_current_version"] is False
    assert "There is deliberately no persisted `current_authoritative_version_id`." in spec
    assert "\ncurrent_authoritative_version_id\nstatus\n" not in spec

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(example)


def test_currentness_projection_example_and_boundaries_validate() -> None:
    schema = _yaml(SCHEMAS / "document_currentness_projection.schema.yaml")
    example = _yaml(EXAMPLES / "document_currentness_projection.example.yaml")

    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    validator.validate(example)

    assert schema["properties"]["purpose"]["enum"] == [
        "latest_received",
        "latest_reviewed",
        "current_working",
        "current_for_coordination",
        "current_for_consultation",
        "current_contractual",
        "current_for_execution",
        "current_for_site",
        "latest_as_built_candidate",
    ]
    assert schema["x-currentness"]["universal_current_version"] is False
    assert schema["x-currentness"]["highest_index_wins"] is False
    assert schema["x-currentness"]["latest_received_is_authority"] is False
    assert schema["x-boundary"]["projected_only"] is True
    assert schema["x-boundary"]["persisted_authority"] is False


def test_resolved_projection_requires_one_exact_version_and_unresolved_has_none() -> None:
    schema = _yaml(SCHEMAS / "document_currentness_projection.schema.yaml")
    example = _yaml(EXAMPLES / "document_currentness_projection.example.yaml")
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())

    missing_version = dict(example)
    missing_version["document_version_id"] = None
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(missing_version)

    unresolved = dict(example)
    unresolved["resolution_status"] = "unresolved"
    unresolved["document_version_id"] = None
    unresolved["index_label"] = None
    unresolved["effect_class"] = None
    unresolved["version_status"] = None
    unresolved["authority_status"] = None
    unresolved["basis"] = {
        "basis_type": "insufficient_inputs",
        "basis_refs": [],
        "missing_requirements": ["signed contractual basis"],
        "conflict_refs": [],
    }
    validator.validate(unresolved)

    contradictory = dict(unresolved)
    contradictory["resolution_status"] = "conflicting"
    contradictory["basis"] = {
        "basis_type": "conflicting_inputs",
        "basis_refs": [],
        "missing_requirements": [],
        "conflict_refs": ["version-event:a", "version-event:b"],
    }
    validator.validate(contradictory)

    unresolved_with_version = dict(unresolved)
    unresolved_with_version["document_version_id"] = example["document_version_id"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(unresolved_with_version)


def test_effect_and_authority_vocabularies_remain_one_closed_set() -> None:
    indexed = _yaml(SCHEMAS / "indexed_document_version.schema.yaml")
    event = _yaml(SCHEMAS / "version_event.schema.yaml")
    currentness = _yaml(SCHEMAS / "document_currentness_projection.schema.yaml")
    event_example = _yaml(EXAMPLES / "version_event.example.yaml")

    indexed_effects = indexed["properties"]["effect_class"]["enum"]
    event_effects = event["$defs"]["effect_class"]["enum"]
    projection_effects = currentness["$defs"]["effect_class"]["enum"]
    assert indexed_effects == event_effects == projection_effects

    indexed_authorities = indexed["properties"]["authority_status"]["enum"]
    event_authorities = event["$defs"]["authority_status"]["enum"]
    projection_authorities = currentness["$defs"]["authority_status"]["enum"]
    assert indexed_authorities == event_authorities == projection_authorities

    assert event["properties"]["previous_authority_status"]["$ref"] == "#/$defs/authority_status"
    assert event["properties"]["new_authority_status"]["$ref"] == "#/$defs/authority_status"
    assert event_example["previous_authority_status"] == "not_authoritative"
    assert event_example["new_authority_status"] == "contractual_authority"

    jsonschema.Draft202012Validator.check_schema(event)
    jsonschema.Draft202012Validator(event, format_checker=jsonschema.FormatChecker()).validate(event_example)


def test_issuer_document_reference_and_index_labels_are_opaque_strings() -> None:
    schema = _yaml(SCHEMAS / "indexed_document_version.schema.yaml")
    example = _yaml(EXAMPLES / "indexed_document_version.example.yaml")
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())

    for reference in ["123", "A", "A17", "ST-204/EXE-03", "NDC-26-042"]:
        candidate = dict(example)
        candidate["issuer_document_reference"] = reference
        validator.validate(candidate)

    for index_label in ["1", "03", "A", "B2", "01A", "Rev.4"]:
        candidate = dict(example)
        candidate["index_label"] = index_label
        validator.validate(candidate)

    numeric_reference = dict(example)
    numeric_reference["issuer_document_reference"] = 123
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(numeric_reference)

    assert schema["properties"]["issuer_document_reference"]["type"] == "string"
    assert schema["properties"]["index_label"]["type"] == "string"
    assert "opaque" in schema["properties"]["issuer_document_reference"]["description"].lower()
    assert "ordering" in schema["properties"]["index_label"]["description"].lower()
