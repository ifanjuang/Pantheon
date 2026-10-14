"""Read-only contract tests for the specialized Tag Registry schema."""

from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "tag_registry.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "tag_registry.example.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_tag_registry_example_validates() -> None:
    schema = _load(SCHEMA_PATH)
    example = _load(EXAMPLE_PATH)

    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(example),
        key=lambda error: list(error.path),
    )
    assert not errors, "\n".join(error.message for error in errors)


def test_tag_registry_example_has_unique_groups_slugs_and_aliases() -> None:
    registry = _load(EXAMPLE_PATH)
    group_ids = [group["id"] for group in registry["groups"]]
    tag_slugs = [tag["slug"] for tag in registry["tags"]]
    aliases = [alias for tag in registry["tags"] for alias in tag["aliases"]]

    assert len(group_ids) == len(set(group_ids))
    assert len(tag_slugs) == len(set(tag_slugs))
    assert len(aliases) == len(set(aliases))
    assert not (set(tag_slugs) & set(aliases))


def test_every_tag_references_a_declared_group() -> None:
    registry = _load(EXAMPLE_PATH)
    group_ids = {group["id"] for group in registry["groups"]}

    assert all(tag["group"] in group_ids for tag in registry["tags"])


def test_subject_group_keeps_five_subject_projection_limit() -> None:
    registry = _load(EXAMPLE_PATH)
    subject = next(group for group in registry["groups"] if group["id"] == "subject")

    assert subject["max_per_card"] == 5


def test_schema_keeps_non_authority_boundaries() -> None:
    text = SCHEMA_PATH.read_text(encoding="utf-8")

    assert "runtime_execution: false" in text
    assert "task_authorization: false" in text
    assert "evidence_promotion: false" in text
    assert "memory_promotion: false" in text
