from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "storage_object.schema.yaml"
EXAMPLE = ROOT / "schemas" / "examples" / "storage_object.example.yaml"
DOCTRINE = ROOT / "docs" / "governance" / "DATA_PLATFORM_STORAGE_OBJECT_RETENTION.md"


def _yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def test_storage_object_example_validates_and_keeps_provider_opaque() -> None:
    schema = _yaml(SCHEMA)
    example = _yaml(EXAMPLE)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(example)

    location = schema["$defs"]["location"]
    assert location["properties"]["storage_provider_ref"]["type"] == "string"
    assert "enum" not in location["properties"]["storage_provider_ref"]
    assert schema["x-boundary"]["provider_routing"] is False
    assert schema["x-boundary"]["access_authorization"] is False


def test_verified_location_requires_verification_record() -> None:
    schema = _yaml(SCHEMA)
    example = _yaml(EXAMPLE)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )

    invalid = {**example, "locations": [dict(example["locations"][0])]}
    invalid["locations"][0].pop("verification")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid)


def test_digest_is_single_object_level_identity_not_duplicated_per_location() -> None:
    schema = _yaml(SCHEMA)
    example = _yaml(EXAMPLE)

    assert schema["properties"]["content_sha256"]["pattern"] == "^[A-Fa-f0-9]{64}$"
    assert "content_sha256" not in schema["$defs"]["location"]["properties"]
    assert example["locations"][0]["verification"]["method"] == "full_sha256"


def test_object_id_is_not_forced_to_equal_digest() -> None:
    schema = _yaml(SCHEMA)
    example = _yaml(EXAMPLE)
    assert example["storage_object_id"] != example["content_sha256"]
    assert "pattern" not in schema["properties"]["storage_object_id"]


def test_storage_contract_does_not_own_scope_authority_or_evidence() -> None:
    schema = _yaml(SCHEMA)
    doctrine = DOCTRINE.read_text(encoding="utf-8")

    assert "project_id" not in schema["properties"]
    assert "scope_id" not in schema["properties"]
    assert schema["x-boundary"]["evidence_admission"] is False
    assert schema["x-boundary"]["professional_validation"] is False
    assert "same bytes != same access rights" in doctrine
    assert "runtime copy success != Evidence" in doctrine


def test_content_addressed_is_a_binding_not_required_identity_scheme() -> None:
    schema = _yaml(SCHEMA)
    guarantee = schema["$defs"]["location"]["properties"]["retention_guarantee"]["enum"]
    assert "content_addressed" in guarantee
    assert "provider_version" in guarantee
    assert "immutable_object" in guarantee
    assert "unknown" in guarantee
