"""HTTP composition tests for `/cockpit/*` API routes and the static shell mount."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical.cockpit_composed import create_composed_cockpit_app


def _forbidden_connection():
    raise AssertionError("unauthorized route reachability must not open PostgreSQL")


def _route_index(app, path: str) -> int:
    for index, route in enumerate(app.router.routes):
        if getattr(route, "path", None) == path:
            return index
    raise AssertionError(f"route not registered: {path}")


def test_composed_cockpit_api_routes_precede_static_mount_and_assets_still_serve(
    tmp_path,
) -> None:
    app = create_composed_cockpit_app(
        connect_fn=_forbidden_connection,
        initialize_fn=None,
        api_key="read-key",
        workspace_roots={"fixture": tmp_path},
    )

    static_index = _route_index(app, "/cockpit")
    assert _route_index(app, "/cockpit/category-collections") < static_index
    assert (
        _route_index(app, "/cockpit/category-collections/{category_id}")
        < static_index
    )
    assert (
        _route_index(app, "/cockpit/workspace-collections/{workspace_ref}")
        < static_index
    )
    assert _route_index(app, "/cockpit/role-traces/{run_id}") < static_index
    assert _route_index(app, "/cockpit/role-traces/{run_id}/events") < static_index

    client = TestClient(app)

    category = client.get("/cockpit/category-collections")
    workspace = client.get("/cockpit/workspace-collections/fixture")
    static_shell = client.get("/cockpit/")

    assert category.status_code == 401
    assert category.json()["detail"] == "invalid read API key"
    assert workspace.status_code == 401
    assert workspace.json()["detail"] == "invalid read API key"
    assert static_shell.status_code == 200
    assert "text/html" in static_shell.headers.get("content-type", "")
