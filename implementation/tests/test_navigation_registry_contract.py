"""Validate the operational Navigation Registry against the canonical Pantheon contract."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from mvp_vertical import pantheon_contracts

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "mvp_vertical" / "cockpit" / "registries" / "navigation_registry.json"
SCHEMA_PATH = pantheon_contracts.schema_path("navigation_registry")


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_operational_navigation_registry_validates_against_canonical_schema() -> None:
    schema = _schema()
    registry = _registry()
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(registry),
        key=lambda error: list(error.path),
    )
    assert not errors, "\n".join(
        f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
        for error in errors
    )


def test_root_identities_and_sources_are_unique() -> None:
    registry = _registry()
    items = registry["root_collection"]["items"]
    identities = [item["id"] for item in items]
    assert identities == [
        "space:pantheon",
        "space:affaires",
        "space:connaissances",
        "space:workspace",
        "space:outils",
        "space:decisions",
    ]
    assert len(identities) == len(set(identities))
    assert all(len(item["sources"]) == len(set(item["sources"])) for item in items)


def test_navigation_registry_uses_canonical_contract_source() -> None:
    source = pantheon_contracts.provenance("navigation_registry")
    assert source["source_repository"] == "ifanjuang/Pantheon"
    assert source["source_path"] == "schemas/navigation_registry.schema.yaml"
    assert source["posture"] == "canonical-repository"
    assert source["authority_transfer"] is False
    assert SCHEMA_PATH == ROOT.parent / "schemas" / "navigation_registry.schema.yaml"


def test_navigation_registry_boundaries_remain_non_authoritative() -> None:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    for token in (
        "endpoint_routing: false",
        "child_assembly: false",
        "runtime_execution: false",
        "task_authorization: false",
        "approval: false",
        "evidence_qualification: false",
    ):
        assert token in schema_text
