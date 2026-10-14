from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
REGISTRY = COCKPIT / "registries" / "materials.json"
RETIRED_PATH = COCKPIT / "v3" / "materials.json"
INTERACTIONS = COCKPIT / "interactions" / "card_interactions.js"


def test_material_registry_has_stable_identity_and_unique_materials() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert payload["schema_id"] == "cockpit.materials"
    assert payload["revision"] == 1
    assert "schema_version" not in payload
    assert payload["assignment"] == {
        "strategy": "stable-entity-hash",
        "fallback_key": "projection-index",
    }

    materials = payload["materials"]
    identifiers = [material["id"] for material in materials]
    assert len(materials) == 12
    assert len(identifiers) == len(set(identifiers))
    assert all(len(material["stops"]) >= 5 for material in materials)


def test_generation_named_material_path_is_retired() -> None:
    assert REGISTRY.is_file()
    assert not RETIRED_PATH.exists()


def test_card_interactions_loads_the_stable_material_registry() -> None:
    interactions = INTERACTIONS.read_text(encoding="utf-8")

    assert 'fetch("registries/materials.json"' in interactions
    assert 'fetch("v3/materials.json"' not in interactions
