from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "navigation_registry.schema.yaml"
EXAMPLE = ROOT / "schemas" / "examples" / "navigation_registry.example.json"


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))


def load_example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_navigation_registry_example_validates() -> None:
    jsonschema.Draft202012Validator(load_schema()).validate(load_example())


def test_navigation_root_identities_and_sources_are_unique() -> None:
    payload = load_example()
    items = payload["root_collection"]["items"]
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids))
    assert all(len(item["sources"]) == len(set(item["sources"])) for item in items)


def test_navigation_registry_keeps_projection_config_boundaries() -> None:
    payload = load_example()
    assert set(payload["x-boundary"].values()) == {False}
    serialized = json.dumps(payload).lower()
    for forbidden in ("http://", "https://api", "sql", "authorize", "approve(", "execute("):
        assert forbidden not in serialized
