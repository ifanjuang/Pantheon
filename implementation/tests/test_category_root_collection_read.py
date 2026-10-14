"""Acceptance tests for the Cockpit root Category Card collection."""

from __future__ import annotations

import pytest

from mvp_vertical import (
    agency_classification,
    agency_data,
    category_collection_read,
    cockpit_composed,
    store,
)


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(agency_classification.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(
        """
        TRUNCATE agency_category_assignments, agency_categories,
                 agency_projects
        RESTART IDENTITY CASCADE
        """
    )
    connection.commit()
    yield connection
    connection.close()


def _category(
    conn,
    category_id: str,
    *,
    title: str,
    sort_order: int,
    parent_category_id: str | None = None,
) -> None:
    agency_classification.create_category(
        conn,
        category_id=category_id,
        title=title,
        parent_category_id=parent_category_id,
        applies_to=["knowledge", "document"],
        sort_order=sort_order,
        actor="human:test",
    )


def test_root_category_collection_projects_only_persisted_roots_as_container_cards(conn) -> None:
    _category(conn, "reglementations", title="Réglementations", sort_order=20)
    _category(conn, "referentiels", title="Référentiels", sort_order=10)
    _category(
        conn,
        "urbanisme",
        title="Urbanisme",
        sort_order=0,
        parent_category_id="reglementations",
    )

    projection = category_collection_read.get_root_category_card_collection(conn)

    assert projection["cards_are_projections"] is True
    assert projection["classification_is_not_authorization"] is True
    assert projection["authorization_inferred"] is False
    collection = projection["collection"]
    assert collection == {
        "collection_id": "children:space:connaissances",
        "parent_entity_id": "space:connaissances",
        "state": "loaded",
        "items": collection["items"],
        "can_add": False,
    }

    assert [item["entity_id"] for item in collection["items"]] == [
        "category:referentiels",
        "category:reglementations",
    ]
    assert all(item["entity_type"] == "category" for item in collection["items"])
    assert all(item["role"] == "container" for item in collection["items"])
    assert all(item["available_actions"] == [] for item in collection["items"])
    assert all(item["source_entity_ref"]["entity_type"] == "category" for item in collection["items"])
    assert [
        item["child_collection"]["load_action"] for item in collection["items"]
    ] == [
        {
            "kind": "collection_read",
            "href": "/cockpit/category-collections/referentiels",
        },
        {
            "kind": "collection_read",
            "href": "/cockpit/category-collections/reglementations",
        },
    ]
    assert "category:urbanisme" not in {
        item["entity_id"] for item in collection["items"]
    }


def test_no_root_category_projects_explicit_empty_not_not_loaded(conn) -> None:
    projection = category_collection_read.get_root_category_card_collection(conn)

    assert projection["collection"] == {
        "collection_id": "children:space:connaissances",
        "parent_entity_id": "space:connaissances",
        "state": "empty",
        "items": [],
        "can_add": False,
    }


def test_root_and_recursive_category_collection_routes_are_both_mounted() -> None:
    app = cockpit_composed.create_composed_cockpit_app(
        connect_fn=lambda: None,
        initialize_fn=None,
        api_key="read-secret",
        editor_api_key="editor-secret",
        hermes_api_key="hermes-secret",
    )
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods_by_path.setdefault(route.path, set()).update(route.methods or set())

    assert "GET" in methods_by_path["/cockpit/category-collections"]
    assert "GET" in methods_by_path[
        "/cockpit/category-collections/{category_id}"
    ]
