"""Validate the operational Cockpit tag registry against the canonical Pantheon contract."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from mvp_vertical import pantheon_contracts

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "mvp_vertical" / "cockpit" / "registries" / "tag_registry.json"
SCHEMA_PATH = pantheon_contracts.schema_path("tag_registry")


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_operational_tag_registry_validates_against_canonical_schema() -> None:
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


def test_tag_groups_and_composite_identities_are_unique_and_resolved() -> None:
    registry = _registry()
    group_ids = [group["id"] for group in registry["groups"]]
    tag_keys = [(tag["group"], tag["slug"]) for tag in registry["tags"]]

    assert len(group_ids) == len(set(group_ids))
    assert len(tag_keys) == len(set(tag_keys))
    assert all(tag["group"] in set(group_ids) for tag in registry["tags"])


def test_subject_projection_limit_remains_five() -> None:
    registry = _registry()
    subject = next(group for group in registry["groups"] if group["id"] == "subject")

    assert subject["max_per_card"] == 5


def test_tag_registry_uses_canonical_contract_source() -> None:
    source = pantheon_contracts.provenance("tag_registry")
    assert source["source_repository"] == "ifanjuang/Pantheon"
    assert source["source_path"] == "schemas/tag_registry.schema.yaml"
    assert source["posture"] == "canonical-repository"
    assert source["authority_transfer"] is False
    assert SCHEMA_PATH == ROOT.parent / "schemas" / "tag_registry.schema.yaml"


def test_tag_registry_boundaries_remain_non_authoritative() -> None:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")

    assert "runtime_execution: false" in schema_text
    assert "task_authorization: false" in schema_text
    assert "evidence_promotion: false" in schema_text
    assert "memory_promotion: false" in schema_text
