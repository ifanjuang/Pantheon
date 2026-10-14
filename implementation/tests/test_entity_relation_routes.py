"""Route-surface tests for explicit Entity relations."""

from fastapi import FastAPI

from mvp_vertical.entity_relation_api import install_entity_relation_routes


def test_entity_relation_routes_are_installed_once() -> None:
    app = FastAPI()

    def with_connection(operation):
        return operation(None)

    def allow():
        return None

    install_entity_relation_routes(
        app,
        with_connection=with_connection,
        require_read_key=allow,
        require_editor_key=allow,
    )

    methods_by_path = {
        route.path: set(route.methods or set())
        for route in app.routes
        if getattr(route, "path", "").startswith("/agency/")
    }
    assert methods_by_path["/agency/entity-relations/{relation_id}"] == {"GET"}
    assert methods_by_path["/agency/projects/{project_id}/entity-relations"] == {"GET"}
    assert methods_by_path["/agency/entities/{entity_type}/{entity_id}/relations"] == {"GET"}
    assert methods_by_path["/agency/entity-relations"] == {"POST"}
    assert methods_by_path["/agency/entity-relations/{relation_id}/retire"] == {"POST"}
