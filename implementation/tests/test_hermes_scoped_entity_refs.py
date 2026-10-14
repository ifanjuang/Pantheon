from __future__ import annotations

from pathlib import Path

import pytest

from mvp_vertical import hermes_launch_context, hermes_scoped_context
from mvp_vertical.entity_ref import EntityRef


def test_context_pack_refs_use_shared_normalization_and_ordered_deduplication() -> None:
    refs = hermes_scoped_context.admitted_entity_refs(
        {
            "included_entities": [
                {"entity_id": " project:p1 ", "entity_type": " project "},
                {"entity_id": "project:p1", "entity_type": "project"},
                {"entity_id": "document:d1", "entity_type": "document"},
            ]
        }
    )

    assert all(isinstance(ref, EntityRef) for ref in refs)
    assert [ref.as_dict() for ref in refs] == [
        {"entity_id": "project:p1", "entity_type": "project"},
        {"entity_id": "document:d1", "entity_type": "document"},
    ]


def test_invalid_stored_context_ref_keeps_scoped_conflict_message() -> None:
    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="stored Context Pack contains an invalid entity reference",
    ):
        hermes_scoped_context.admitted_entity_refs(
            {"included_entities": ["project:p1"]}
        )


def test_incomplete_stored_context_ref_keeps_scoped_conflict_message() -> None:
    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="stored Context Pack contains an incomplete entity reference",
    ):
        hermes_scoped_context.admitted_entity_refs(
            {"included_entities": [{"entity_id": "project:p1"}]}
        )


def test_context_pack_still_requires_at_least_one_admitted_entity() -> None:
    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="stored Context Pack contains no admitted entity",
    ):
        hermes_scoped_context.admitted_entity_refs({"included_entities": []})


def test_admitted_entity_uses_shared_key_but_keeps_exact_scope_gate() -> None:
    context_pack = {
        "included_entities": [
            {"entity_id": "project:p1", "entity_type": "project"},
        ]
    }

    admitted = hermes_scoped_context.require_admitted_entity(
        context_pack,
        entity_type=" project ",
        entity_id=" project:p1 ",
    )
    assert admitted == EntityRef(entity_id="project:p1", entity_type="project")

    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="outside the exact admitted Context Pack",
    ):
        hermes_scoped_context.require_admitted_entity(
            context_pack,
            entity_type="project",
            entity_id="project:p2",
        )


def test_scoped_context_keeps_materialization_and_authority_outside_entity_ref() -> None:
    source = Path(hermes_scoped_context.__file__).read_text(encoding="utf-8")

    assert "unique_entity_refs" in source
    assert "_runtime_scope" in source
    assert "materialize_context_entity" in source
    assert "context_pack_authorizes_identity_not_snapshot" in source
    assert "runtime success != Evidence" in source


def test_launch_context_consumes_only_public_scoped_context_contract() -> None:
    source = Path(hermes_launch_context.__file__).read_text(encoding="utf-8")

    assert "hermes_scoped_context.admitted_entity_refs" in source
    assert "hermes_scoped_context.materialize_context_entity" in source
    assert "hermes_scoped_context._" not in source
