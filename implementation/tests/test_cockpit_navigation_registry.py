from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
REGISTRY = COCKPIT / "registries" / "navigation_registry.json"


def test_navigation_registry_declares_stable_roots_and_abstract_sources() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert payload["schema_id"] == "cockpit.navigation.registry"
    assert payload["revision"] == 1
    assert "schema_version" not in payload
    root = payload["root_collection"]
    assert root["id"] == "primary-spaces"
    assert [item["id"] for item in root["items"]] == [
        "space:pantheon",
        "space:affaires",
        "space:connaissances",
        "space:workspace",
        "space:outils",
        "space:decisions",
    ]
    assert root["items"][0]["sources"] == [
        "pending_change_candidates",
        "current_runs",
    ]
    assert root["items"][1]["sources"] == ["projects"]
    assert root["items"][2]["sources"] == ["category_roots"]
    assert root["items"][3]["sources"] == ["workspace_roots"]
    assert root["items"][4]["sources"] == ["tools"]
    assert root["items"][5]["sources"] == ["decision_requests"]

    for item in root["items"]:
        for source in item["sources"]:
            assert "/" not in source
            assert "://" not in source


def test_navigation_registry_is_loaded_before_the_projection() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")

    loader_import = 'import("./projection/navigation_registry_loader.js")'
    adapter = '"projection/navigation_registry_adapter.js"'
    decision_projection = '"projection/decision_request_projection.js"'
    projection = '"projection/cockpit_projection.js"'

    assert loader_import in bootstrap
    assert "await loadNavigationRegistry();" in bootstrap
    assert adapter in bootstrap
    assert decision_projection in bootstrap
    assert bootstrap.index(adapter) < bootstrap.index(decision_projection)
    assert bootstrap.index(decision_projection) < bootstrap.index(projection)


def test_navigation_registry_adapter_is_read_only_and_not_authoritative() -> None:
    loader = (COCKPIT / "projection" / "navigation_registry_loader.js").read_text(encoding="utf-8")
    adapter = (COCKPIT / "projection" / "navigation_registry_adapter.js").read_text(encoding="utf-8")
    renderer = (COCKPIT / "projection" / "cockpit_projection.js").read_text(encoding="utf-8")

    assert "ALLOWED_SOURCES" in loader
    assert '"decision_requests"' in loader
    assert "Duplicate navigation root" in loader
    assert "Unknown navigation source" in loader
    assert "navigation.create =" not in adapter
    assert "PantheonSpatialNavigation" not in adapter
    assert "rootCollectionId: root.id" in adapter
    assert "rootItemIds: Object.freeze(root.items.map(item => item.id))" in adapter
    assert "navigationProjection.rootItemIds.map" in renderer
    assert "root_collection_id: navigationProjection.rootCollectionId" in renderer
    assert "root_item_ids: navigationProjection.rootItemIds" in renderer

    forbidden = (
        "Authorization",
        "ChangeCandidate",
        "Evidence",
        "approved =",
        "task_authorized",
        "fetch(\"../v1",
    )
    for token in forbidden:
        assert token not in adapter
