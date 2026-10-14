from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "card_projection_definition.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "card_projection_definition.example.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_card_projection_definition_example_validates() -> None:
    schema = _load(SCHEMA_PATH)
    example = _load(EXAMPLE_PATH)

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(example)


def test_card_projection_definition_keeps_authority_boundaries_closed() -> None:
    example = _load(EXAMPLE_PATH)

    assert set(example["x-boundary"].values()) == {False}
    assert example["actions"]["source"] == "server_projection"
    assert example["relations"]["children_source"] == "navigation_registry"


def test_projection_definition_does_not_admit_runtime_or_transport_fields() -> None:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")

    for forbidden in ("endpoint", "sql", "provider_binding", "permission_rule", "transition"):
        assert forbidden not in schema_text
