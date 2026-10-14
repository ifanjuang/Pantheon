from __future__ import annotations

import ast
from pathlib import Path

import pytest

from mvp_vertical.entity_ref import EntityRef, EntityRefError, unique_entity_refs


def test_entity_ref_normalizes_stable_identity_without_claiming_owner_existence() -> None:
    ref = EntityRef.from_mapping(
        {"entity_id": "  project:p1  ", "entity_type": " project "},
        label="root entity",
    )

    assert ref.entity_id == "project:p1"
    assert ref.entity_type == "project"
    assert ref.key == ("project", "project:p1")
    assert ref.as_dict() == {
        "entity_id": "project:p1",
        "entity_type": "project",
    }


def test_entity_ref_refuses_incomplete_or_non_object_input() -> None:
    with pytest.raises(EntityRefError, match="requires stable entity_id and entity_type"):
        EntityRef.from_mapping({"entity_id": "project:p1"}, label="selected entity")

    with pytest.raises(EntityRefError, match="must be an object"):
        EntityRef.from_mapping(None, label="selected entity")  # type: ignore[arg-type]


def test_unique_entity_refs_preserves_order_and_deduplicates_by_type_and_id() -> None:
    refs = unique_entity_refs(
        [
            {"entity_id": "project:p1", "entity_type": "project"},
            {"entity_id": "project:p1", "entity_type": "project"},
            {"entity_id": "project:p1", "entity_type": "document"},
            {"entity_id": "document:d1", "entity_type": "document"},
        ],
        label="selected context",
        limit=10,
    )

    assert [ref.key for ref in refs] == [
        ("project", "project:p1"),
        ("document", "project:p1"),
        ("document", "document:d1"),
    ]


def test_unique_entity_refs_enforces_caller_owned_collection_limit() -> None:
    with pytest.raises(EntityRefError, match="exceeds 1 entries"):
        unique_entity_refs(
            [
                {"entity_id": "project:p1", "entity_type": "project"},
                {"entity_id": "project:p2", "entity_type": "project"},
            ],
            label="selected context",
            limit=1,
        )


def test_entity_ref_has_no_database_http_or_adapter_dependency() -> None:
    path = Path(__import__("mvp_vertical.entity_ref", fromlist=["EntityRef"]).__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {"__future__", "collections", "dataclasses", "typing"}
