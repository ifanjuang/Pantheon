"""Acceptance tests for the reversible Workspace navigation space."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mvp_vertical import workspace_collection_read
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


ROOT = Path(__file__).resolve().parents[1]
NAVIGATION_REGISTRY = ROOT / "mvp_vertical" / "cockpit" / "registries" / "navigation_registry.json"
PROJECTION_DEFINITIONS = ROOT / "mvp_vertical" / "cockpit" / "registries" / "card_projection_definitions.json"
ASSEMBLER = ROOT / "mvp_vertical" / "cockpit" / "projection" / "child_collection_assembler.js"
LOADER = ROOT / "mvp_vertical" / "cockpit" / "projection" / "navigation_registry_loader.js"


def _forbidden_connection():
    raise AssertionError("workspace navigation must not open a database connection")


def _client(*, workspace_roots=None) -> TestClient:
    kwargs = {
        "connect_fn": _forbidden_connection,
        "initialize_fn": None,
        "api_key": "read-key",
    }
    if workspace_roots is not None:
        kwargs["workspace_roots"] = workspace_roots
    return TestClient(create_composed_cockpit_app(**kwargs))


def _authorized_get(client: TestClient, path: str):
    return client.get(path, headers={"Authorization": "Bearer read-key"})


def test_runtime_workspace_config_is_server_owned_multi_root_and_does_not_leak_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agency = tmp_path / "agency-vault"
    projects = tmp_path / "project-vault"
    agency.mkdir()
    projects.mkdir()
    (agency / "Connaissances").mkdir()
    (projects / "Affaires").mkdir()

    monkeypatch.setenv(
        "MVP_WORKSPACE_ROOTS_JSON",
        json.dumps({"agency": str(agency), "agency-projects": str(projects)}),
    )
    client = _client()

    unauthorized = client.get("/cockpit/workspace-collections")
    assert unauthorized.status_code == 401

    response = _authorized_get(client, "/cockpit/workspace-collections")
    assert response.status_code == 200
    body = response.json()
    assert body["cards_are_projections"] is True
    assert body["collection"]["parent_entity_id"] == "space:workspace"
    assert body["collection"]["collection_id"] == "children:space:workspace"
    assert body["collection"]["state"] == "loaded"
    assert body["collection"]["can_add"] is False

    items = body["collection"]["items"]
    assert [item["title"] for item in items] == ["agency", "agency-projects"]
    assert all(item["entity_type"] == "workspace_entry" for item in items)
    assert all(item["relative_path"] == "" for item in items)
    assert all(item["workspace_entry_kind"] == "directory" for item in items)
    assert all(item["child_collection"]["load_action"]["kind"] == "collection_read" for item in items)

    serialized = json.dumps(body, ensure_ascii=False)
    assert str(agency) not in serialized
    assert str(projects) not in serialized
    assert "project_id" not in serialized
    assert "knowledge_id" not in serialized

    projects_root = next(item for item in items if item["title"] == "agency-projects")
    child = _authorized_get(client, projects_root["child_collection"]["load_action"]["href"])
    assert child.status_code == 200
    assert [item["title"] for item in child.json()["collection"]["items"]] == ["Affaires"]
    assert child.json()["collection"]["items"][0]["entity_type"] == "workspace_entry"


def test_absent_runtime_workspace_config_projects_an_empty_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MVP_WORKSPACE_ROOTS_JSON", raising=False)
    client = _client()

    response = _authorized_get(client, "/cockpit/workspace-collections")
    assert response.status_code == 200
    body = response.json()
    assert body["collection"] == {
        "collection_id": "children:space:workspace",
        "parent_entity_id": "space:workspace",
        "state": "empty",
        "items": [],
        "can_add": False,
    }


def test_invalid_runtime_workspace_config_fails_closed_at_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MVP_WORKSPACE_ROOTS_JSON", "not-json")
    with pytest.raises(workspace_collection_read.WorkspaceConfigurationError):
        _client()

    monkeypatch.setenv("MVP_WORKSPACE_ROOTS_JSON", json.dumps([str(tmp_path)]))
    with pytest.raises(workspace_collection_read.WorkspaceConfigurationError):
        _client()

    monkeypatch.setenv("MVP_WORKSPACE_ROOTS_JSON", json.dumps({"primary": str(tmp_path / "missing")}))
    with pytest.raises(workspace_collection_read.WorkspaceConfigurationError):
        _client()


def test_workspace_navigation_reuses_cockpit_space_registry_and_generic_collection_read() -> None:
    navigation = json.loads(NAVIGATION_REGISTRY.read_text(encoding="utf-8"))
    roots = {item["id"]: item["sources"] for item in navigation["root_collection"]["items"]}
    assert roots == {
        "space:pantheon": ["pending_change_candidates", "current_runs"],
        "space:affaires": ["projects"],
        "space:connaissances": ["category_roots"],
        "space:workspace": ["workspace_roots"],
        "space:outils": ["tools"],
        "space:decisions": ["decision_requests"],
    }

    definitions = json.loads(PROJECTION_DEFINITIONS.read_text(encoding="utf-8"))["definitions"]
    workspace = next(item for item in definitions if item["entity_id"] == "space:workspace")
    assert workspace["entity_type"] == "cockpit_space"
    assert workspace["card_role"] == "container"
    assert workspace["presentation_family"] == "information"
    assert workspace["status"] == "neutral"
    assert workspace["children_source"] == "navigation_registry"

    assembler = ASSEMBLER.read_text(encoding="utf-8")
    loader = LOADER.read_text(encoding="utf-8")
    assert 'workspace_roots: Object.freeze({' in assembler
    assert 'href: "/cockpit/workspace-collections"' in assembler
    assert '"workspace_roots"' in loader
    assert "workspace_entry" not in loader
