from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (
    ROOT
    / "docs"
    / "governance"
    / "authority"
    / "PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json"
)

OWNER_FIELDS = {
    "semantic_owner",
    "implementation_owner",
    "transition_owner",
    "persistence_owner",
    "runtime_owner",
    "projection_owner",
}

CORE_GOVERNED_STATE_CONCEPTS = {
    "project_claim",
    "evidence",
    "document_source",
    "decision",
    "governed_identity",
}


def _registry() -> dict:
    value = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _concepts_by_id(registry: dict) -> dict[str, dict]:
    return {concept["id"]: concept for concept in registry["concepts"]}


def test_system_ownership_uses_current_logical_responsibility_identities() -> None:
    registry = _registry()

    assert registry["revision"] == 4
    assert set(registry["owners"]) == {
        "Pantheon governance",
        "Pantheon implementation",
        "Hermes/external runtime",
        "Pantheon Cockpit",
    }
    assert registry["owners"]["Pantheon Cockpit"]["role"] == "governed_projection"
    assert "Cockpit/OpenWebUI" not in registry["owners"]
    assert "Pantheon-Next" not in registry["owners"]
    assert "pantheon-mvp" not in registry["owners"]


def test_every_concept_owner_resolves_to_a_declared_logical_owner() -> None:
    registry = _registry()
    owners = set(registry["owners"])

    for concept in registry["concepts"]:
        for field in OWNER_FIELDS:
            owner = concept.get(field)
            if owner is not None:
                assert owner in owners, f"{concept['id']}.{field} -> {owner}"


def test_owner_dimensions_are_closed_and_do_not_grow_by_spelling_drift() -> None:
    registry = _registry()

    for concept in registry["concepts"]:
        declared_owner_fields = {
            field for field in concept if field.endswith("_owner")
        }
        assert declared_owner_fields <= OWNER_FIELDS, concept["id"]
        assert concept.get("semantic_owner"), concept["id"]


def test_repository_and_retired_product_names_are_not_active_owner_identities() -> None:
    registry = _registry()
    retired = {"Pantheon-Next", "pantheon-mvp", "Cockpit/OpenWebUI"}

    for concept in registry["concepts"]:
        referenced = {concept.get(field) for field in OWNER_FIELDS}
        assert not (retired & referenced), concept["id"]


def test_core_governed_state_concepts_declare_the_same_authority_envelope() -> None:
    registry = _registry()
    concepts = _concepts_by_id(registry)

    assert CORE_GOVERNED_STATE_CONCEPTS <= set(concepts)

    for concept_id in CORE_GOVERNED_STATE_CONCEPTS:
        concept = concepts[concept_id]
        assert concept["semantic_owner"] == "Pantheon governance"
        assert concept["implementation_owner"] == "Pantheon implementation"
        assert concept["transition_owner"] == "Pantheon implementation"
        assert concept["persistence_owner"] == "Pantheon implementation"
        assert concept["projection_owner"] == "Pantheon Cockpit"
        assert concept.get("runtime_owner") is None


def test_projection_and_persistence_are_separate_dimensions() -> None:
    registry = _registry()
    concepts = _concepts_by_id(registry)

    for concept_id in CORE_GOVERNED_STATE_CONCEPTS:
        concept = concepts[concept_id]
        assert "projection_owner" in concept
        assert "persistence_owner" in concept

    cockpit = concepts["cockpit_projection"]
    assert cockpit["projection_owner"] == "Pantheon Cockpit"
    assert cockpit.get("persistence_owner") is None

    postgres = concepts["postgres_persistence"]
    assert postgres["persistence_owner"] == "Pantheon implementation"
    assert postgres.get("projection_owner") is None


def test_registry_carries_the_non_equivalence_rules_needed_by_the_topology() -> None:
    rules = set(_registry()["boundary_rules"])

    assert "projection != persistence" in rules
    assert "folder != governed identity" in rules
    assert "repository co-location != authority transfer" in rules
    assert "runtime_success != Evidence" in rules
