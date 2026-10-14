"""Read-only contract tests for hierarchical Agency Data classification."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "category_classification.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "category_classification.example.yaml"
DOCTRINE_PATH = ROOT / "docs" / "governance" / "CATEGORY_CLASSIFICATION_MODEL.md"
TAG_SCHEMA_PATH = ROOT / "schemas" / "tag_registry.schema.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _assert_acyclic(categories: list[dict]) -> None:
    parents = {item["category_id"]: item["parent_category_id"] for item in categories}
    for category_id in parents:
        seen: set[str] = set()
        current: str | None = category_id
        while current is not None:
            if current in seen:
                raise AssertionError(f"Category cycle detected from {category_id}: {current}")
            seen.add(current)
            current = parents.get(current)


def test_category_classification_example_validates() -> None:
    schema = _load(SCHEMA_PATH)
    example = _load(EXAMPLE_PATH)

    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.path))
    assert not errors, "\n".join(error.message for error in errors)


def test_category_contract_is_subordinate_to_existing_agency_data_owner() -> None:
    projection = _load(EXAMPLE_PATH)
    refs = projection["governance_refs"]
    doctrine = DOCTRINE_PATH.read_text(encoding="utf-8")

    assert refs == [
        "docs/governance/AGENCY_DATA_SYSTEM_OF_RECORD.md",
        "docs/governance/CATEGORY_CLASSIFICATION_MODEL.md",
    ]
    assert "specializes `AGENCY_DATA_SYSTEM_OF_RECORD.md`" in doctrine
    assert "does not replace that owner document" in doctrine


def test_category_tree_has_unique_ids_declared_parents_and_no_cycles() -> None:
    projection = _load(EXAMPLE_PATH)
    categories = projection["categories"]
    ids = [item["category_id"] for item in categories]
    declared = set(ids)

    assert len(ids) == len(declared)
    assert all(
        item["parent_category_id"] is None or item["parent_category_id"] in declared
        for item in categories
    )
    assert all(item["parent_category_id"] != item["category_id"] for item in categories)
    _assert_acyclic(categories)


def test_example_proves_arbitrary_depth_without_multiple_category_parents() -> None:
    projection = _load(EXAMPLE_PATH)
    by_id = {item["category_id"]: item for item in projection["categories"]}

    assert by_id["plu-plui"]["parent_category_id"] == "urbanisme"
    assert by_id["urbanisme"]["parent_category_id"] == "reglementations"
    assert by_id["reglementations"]["parent_category_id"] is None
    assert all(not isinstance(item["parent_category_id"], list) for item in by_id.values())


def test_assignments_reference_categories_match_applies_to_and_are_unique_when_active() -> None:
    projection = _load(EXAMPLE_PATH)
    categories = {item["category_id"]: item for item in projection["categories"]}
    assignments = projection["assignments"]

    assignment_ids = [item["assignment_id"] for item in assignments]
    assert len(assignment_ids) == len(set(assignment_ids))

    active_keys = []
    for assignment in assignments:
        category = categories[assignment["category_id"]]
        assert assignment["entity_type"] in category["applies_to"]
        assert (assignment["retired_at"] is None) == (assignment["retired_by"] is None)
        if assignment["retired_at"] is None:
            active_keys.append(
                (
                    assignment["category_id"],
                    assignment["entity_type"],
                    assignment["entity_id"],
                )
            )

    assert len(active_keys) == len(set(active_keys))


def test_same_entity_can_be_classified_in_multiple_categories_without_identity_duplication() -> None:
    projection = _load(EXAMPLE_PATH)
    active = [item for item in projection["assignments"] if item["retired_at"] is None]
    entity_keys = [(item["entity_type"], item["entity_id"]) for item in active]
    counts = Counter(entity_keys)

    shared = ("document", "document:plui-metropole")
    assert counts[shared] == 2
    assert {
        item["category_id"]
        for item in active
        if (item["entity_type"], item["entity_id"]) == shared
    } == {"plu-plui", "referentiels"}


def test_category_contract_does_not_replace_tags_status_or_semantic_entity_relations() -> None:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    doctrine = DOCTRINE_PATH.read_text(encoding="utf-8")
    tag_schema = _load(TAG_SCHEMA_PATH)

    assert "category_id" in schema_text
    assert "parent_category_id" in schema_text
    assert "tag_registry" not in schema_text
    assert "status:" not in schema_text
    assert "Category != Tag" in doctrine
    assert "CategoryAssignment != EntityRelation" in doctrine
    assert tag_schema["properties"]["schema_id"]["const"] == "cockpit.tag_registry"


def test_category_contract_keeps_non_authority_boundaries() -> None:
    projection = _load(EXAMPLE_PATH)
    boundary = projection["x-boundary"]

    assert boundary == {
        "runtime_execution": False,
        "provider_routing": False,
        "task_authorization": False,
        "approval": False,
        "evidence_promotion": False,
        "memory_promotion": False,
        "ownership_transfer": False,
    }


def test_category_contract_does_not_create_a_parallel_folder_backend_model() -> None:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    doctrine = DOCTRINE_PATH.read_text(encoding="utf-8")

    assert "folder_id" not in schema_text
    assert "parent_folder_id" not in schema_text
    assert "Do not add a parallel persisted `Folder` model" in doctrine
