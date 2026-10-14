from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "mvp_vertical" / "cockpit" / "registries" / "card_projection_definitions.json"
LOADER = ROOT / "mvp_vertical" / "cockpit" / "projection" / "card_projection_definition_loader.js"
STRUCTURED_INTERFACE = ROOT / "mvp_vertical" / "cockpit" / "structured_interface.js"
LIVE_BOOTSTRAP = ROOT / "mvp_vertical" / "cockpit" / "live_bootstrap.js"


def test_root_projection_registry_is_loaded_before_classic_projection_scripts() -> None:
    source = LIVE_BOOTSTRAP.read_text(encoding="utf-8")
    load_index = source.index("loadCardProjectionDefinitions")
    classic_index = source.index("loadClassicScriptsInOrder")
    assert load_index < classic_index


def test_loader_exposes_only_declared_root_projection_identities() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entity_ids = [entry["entity_id"] for entry in registry["definitions"]]
    assert entity_ids == [
        "space:pantheon",
        "space:affaires",
        "space:connaissances",
        "space:workspace",
        "space:outils",
        "space:decisions",
    ]
    source = LOADER.read_text(encoding="utf-8")
    assert "PantheonCardProjectionDefinitions" in source
    assert "cockpit_space" in source
    assert "authorization" not in source.lower()


def test_structured_interface_applies_root_definition_through_dedicated_builder() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    assert "rootProjectionDefinition" in source
    assert "buildRootProjection" in source
    assert "projection_definition_id: definition.definition_id" in source
    assert "role: definition.card_role" in source
    assert "back: Array.isArray(definition.detail_rows)" in source
    assert "return buildRootProjection(rootDefinition);" in source


def test_projection_consumption_keeps_runtime_and_authority_boundaries() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8") + LOADER.read_text(encoding="utf-8")
    forbidden = (
        "fetch('/v1/execute",
        "task_authorized = true",
        "evidence = true",
        "approve(",
        "activate(",
    )
    assert all(token not in source for token in forbidden)
