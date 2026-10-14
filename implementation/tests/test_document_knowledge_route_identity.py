"""Route identity and active-consumer guards for Documents and Knowledge."""

from pathlib import Path

from mvp_vertical.cockpit_api import create_app


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
MOBILE = ROOT / "mvp_vertical" / "mobile_editor"


class _Connection:
    def close(self) -> None:
        pass


def test_document_knowledge_api_mounts_only_stable_routes() -> None:
    app = create_app(connect_fn=_Connection)
    routes = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }

    expected = {
        ("GET", "/projects/{parent_project_id}/documents"),
        ("GET", "/documents/{document_id}"),
        ("GET", "/documents/{document_id}/chunks"),
        ("GET", "/projects/{parent_project_id}/knowledge"),
        ("GET", "/knowledge/{knowledge_id}"),
        ("GET", "/knowledge/{knowledge_id}/markdown"),
        ("GET", "/knowledge/{knowledge_id}/sources"),
        ("GET", "/knowledge/{knowledge_id}/recompile-context"),
        ("GET", "/documents/{document_id}/knowledge-impacts"),
        ("POST", "/knowledge/{knowledge_id}/recompile-requests"),
        ("GET", "/edit-requests/{request_id}/recompile-context"),
        ("GET", "/edit-requests/{request_id}/recompile-review"),
        ("POST", "/documents/{document_id}/knowledge"),
        ("PUT", "/knowledge/{knowledge_id}"),
        ("POST", "/knowledge/{knowledge_id}/edit-requests"),
        ("PUT", "/edit-requests/{request_id}/proposal"),
        ("GET", "/edit-requests"),
        ("POST", "/edit-requests/{request_id}/apply"),
        ("GET", "/documents/{document_id}/markdown"),
        ("GET", "/documents/{document_id}/preview-link"),
        ("GET", "/previews/{document_id}/original"),
    }

    assert expected <= routes
    assert not {
        (method, f"/v1{path}")
        for method, path in expected
    } & routes


def test_active_document_knowledge_consumers_have_no_retired_prefix() -> None:
    consumers = {
        "loader": COCKPIT / "data" / "cockpit_data_loader.js",
        "actions": COCKPIT / "actions" / "card_actions.js",
        "demo": COCKPIT / "demo_bootstrap.js",
        "mobile": MOBILE / "app.js",
    }
    retired = (
        "/v1/projects/",
        "/v1/documents/",
        "/v1/knowledge/",
        "/v1/edit-requests",
        "/v1/previews/",
    )

    for name, path in consumers.items():
        source = path.read_text(encoding="utf-8")
        for prefix in retired:
            assert prefix not in source, f"{name} still uses {prefix}"

    loader = consumers["loader"].read_text(encoding="utf-8")
    actions = consumers["actions"].read_text(encoding="utf-8")
    demo = consumers["demo"].read_text(encoding="utf-8")
    mobile = consumers["mobile"].read_text(encoding="utf-8")

    assert "../projects/${encoded}/documents" in loader
    assert "../projects/${encoded}/knowledge" in loader
    assert "../documents/${encodeURIComponent(id)}/chunks" in actions
    assert "routes.projectDocuments(projectId)" in demo
    assert "routes.projectKnowledge(projectId)" in demo
    assert r"\/projects\/([^/]+)\/(documents|knowledge)$" not in demo
    assert "../projects/${encodeURIComponent(state.project)}/knowledge" in mobile
    assert "../knowledge/${encodeURIComponent(item.knowledge_id)}/markdown" in mobile
    assert "../knowledge/${encodeURIComponent(operation.knowledge_id)}/edit-requests" in mobile


def test_mobile_service_worker_does_not_cache_api_reads() -> None:
    source = (MOBILE / "sw.js").read_text(encoding="utf-8")

    for prefix in (
        '"/projects/"',
        '"/documents/"',
        '"/knowledge/"',
        '"/edit-requests"',
        '"/execution-results/"',
        '"/previews/"',
        '"/agency/"',
        '"/work/"',
        '"/hermes/"',
        '"/resources/"',
        '"/health"',
    ):
        assert prefix in source

    assert "API_PREFIXES.some" in source
    assert 'const CACHE = "pantheon-knowledge-shell-r4"' in source
