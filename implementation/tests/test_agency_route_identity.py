"""Stable route-identity guards for global Agency Data surfaces."""

from __future__ import annotations

from pathlib import Path

from mvp_vertical.cockpit_shell import create_cockpit_app


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


class _Connection:
    def close(self) -> None:
        pass


def test_mounted_global_agency_routes_use_stable_responsibility_paths() -> None:
    app = create_cockpit_app(
        connect_fn=_Connection,
        api_key="route-read-key",
        editor_api_key="route-editor-key",
        hermes_api_key="route-hermes-key",
    )
    mounted = {route.path for route in app.routes if getattr(route, "path", None)}

    assert not [path for path in mounted if path == "/v1/agency" or path.startswith("/v1/agency/")]
    assert "/agency/projects" in mounted
    assert "/agency/schema/project" in mounted
    assert "/agency/projects/{project_id}/information" in mounted
    assert "/agency/projects/{project_id}/claims" in mounted
    assert "/agency/projects/{project_id}/change-candidates" in mounted
    assert "/agency/change-candidates/{candidate_id}/apply" in mounted


def test_active_cockpit_consumers_do_not_publish_old_agency_paths() -> None:
    consumers = (
        COCKPIT / "data" / "cockpit_data_loader.js",
        COCKPIT / "schema_editor.js",
        COCKPIT / "contacts_editor.js",
        COCKPIT / "information_create.js",
        COCKPIT / "project_claim_view_adapter.js",
        COCKPIT / "actions" / "change_candidate_actions.js",
        COCKPIT / "demo_bootstrap.js",
    )
    for path in consumers:
        content = path.read_text(encoding="utf-8")
        assert "../v1/agency/" not in content, path
        assert "/v1/agency/" not in content, path


def test_document_collections_use_their_own_stable_route_family() -> None:
    loader = (COCKPIT / "data" / "cockpit_data_loader.js").read_text(encoding="utf-8")
    demo = (COCKPIT / "demo_bootstrap.js").read_text(encoding="utf-8")

    assert "../projects/${encoded}/documents" in loader
    assert "../projects/${encoded}/knowledge" in loader
    assert "../v1/projects/" not in loader
    assert "routes.projectDocuments(projectId)" in demo
    assert "routes.projectKnowledge(projectId)" in demo
    assert r"\/projects\/([^/]+)\/(documents|knowledge)$" not in demo
    assert r"\/v1\/projects\/" not in demo
