from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str):
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_signature_effect_request_example_validates() -> None:
    schema = _load("schemas/signature_effect_request.schema.yaml")
    example = _load("schemas/examples/signature_effect_request.example.yaml")
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(example)
    assert example["governance"] == {
        "authorization_required": True,
        "authorized": False,
        "execution_performed": False,
    }


def test_signature_provider_observation_example_validates_and_is_non_authoritative() -> None:
    schema = _load("schemas/signature_provider_observation.schema.yaml")
    example = _load("schemas/examples/signature_provider_observation.example.yaml")
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(example)
    assert example["authenticity"]["verified"] is True
    assert example["governance"] == {
        "authoritative": False,
        "evidence_admitted": False,
        "authorization_inferred": False,
    }


def test_signature_catalog_entries_validate_as_candidates() -> None:
    capability_schema = _load("catalog/schemas/capability.schema.json")
    resource_schema = _load("catalog/schemas/resource.schema.json")
    capability = _load("catalog/capabilities/e_signature_workflow.yaml")
    resource = _load("catalog/resources/docuseal.yaml")

    jsonschema.Draft202012Validator(capability_schema).validate(capability)
    jsonschema.Draft202012Validator(resource_schema).validate(resource)

    assert capability["metadata"]["status"] == "candidate"
    assert resource["metadata"]["status"] == "candidate"
    assert resource["spec"]["boundaries"]["activation"] is False
