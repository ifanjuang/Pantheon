"""HTTP boundary tests for Agency Data Category classification."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mvp_vertical import agency_classification
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def _client(**keys) -> TestClient:
    return TestClient(
        create_composed_cockpit_app(
            connect_fn=_Connection,
            initialize_fn=None,
            **keys,
        )
    )


def test_category_reads_expose_postgres_without_authorization_inference(monkeypatch) -> None:
    monkeypatch.setattr(
        agency_classification,
        "list_categories",
        lambda _conn, *, include_archived: [
            {
                "category_id": "urbanisme",
                "title": "Urbanisme",
                "parent_category_id": None,
                "revision": 2,
            }
        ],
    )
    client = _client(api_key="read-key", hermes_api_key="hermes-key")

    response = client.get(
        "/agency/categories",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["system_of_record"] == "postgres"
    assert body["classification_is_not_authorization"] is True
    assert body["categories"][0]["category_id"] == "urbanisme"

    hermes = client.get(
        "/agency/categories",
        headers={"Authorization": "Bearer hermes-key"},
    )
    assert hermes.status_code == 401


def test_category_collection_is_read_as_projection_input(monkeypatch) -> None:
    monkeypatch.setattr(
        agency_classification,
        "get_category_collection",
        lambda _conn, category_id: {
            "category": {"category_id": category_id},
            "child_categories": [{"category_id": "plu-plui"}],
            "assignments": [],
            "collection_is_projection_input": True,
            "classification_is_not_authorization": True,
        },
    )
    client = _client(api_key="read-key")
    response = client.get(
        "/agency/categories/urbanisme/collection",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 200
    assert response.json()["collection"]["child_categories"][0]["category_id"] == "plu-plui"
    assert response.json()["classification_is_not_authorization"] is True


def test_editor_creates_category_as_human_without_approval_inference(monkeypatch) -> None:
    observed = {}

    def create_category(_conn, **values):
        observed.update(values)
        return {
            "category_id": values["category_id"],
            "title": values["title"],
            "revision": 1,
        }

    monkeypatch.setattr(agency_classification, "create_category", create_category)
    client = _client(editor_api_key="editor-key", hermes_api_key="hermes-key")
    response = client.post(
        "/agency/categories",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json={
            "category_id": "urbanisme",
            "title": "Urbanisme",
            "applies_to": ["document", "knowledge"],
        },
    )
    assert response.status_code == 201
    assert observed["actor"] == "ifan"
    assert observed["actor_kind"] == "human"
    assert response.json()["effect"] == "internal_agency_classification_write"
    assert response.json()["approval_inferred"] is False
    assert response.json()["classification_is_not_authorization"] is True


def test_hermes_direct_category_write_is_refused_before_adapter(monkeypatch) -> None:
    called = False

    def create_category(_conn, **_values):
        nonlocal called
        called = True
        raise AssertionError("Hermes Category write must not reach the adapter")

    monkeypatch.setattr(agency_classification, "create_category", create_category)
    client = _client(editor_api_key="editor-key", hermes_api_key="hermes-key")
    response = client.post(
        "/agency/categories",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Human-Actor": "fabricated-human",
        },
        json={
            "category_id": "urbanisme",
            "title": "Urbanisme",
            "applies_to": ["document"],
        },
    )
    assert response.status_code == 403
    assert "suggest classification" in response.json()["detail"]
    assert called is False


def test_ambiguous_editor_and_hermes_key_is_refused(monkeypatch) -> None:
    called = False

    def create_category(_conn, **_values):
        nonlocal called
        called = True
        raise AssertionError("ambiguous writer key must fail closed")

    monkeypatch.setattr(agency_classification, "create_category", create_category)
    with pytest.raises(
        ValueError,
        match="MVP_EDITOR_API_KEY and MVP_HERMES_API_KEY must be distinct",
    ):
        _client(editor_api_key="shared-key", hermes_api_key="shared-key")
    assert called is False


def test_category_write_requires_human_actor(monkeypatch) -> None:
    called = False

    def create_category(_conn, **_values):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(agency_classification, "create_category", create_category)
    client = _client(editor_api_key="editor-key")
    response = client.post(
        "/agency/categories",
        headers={"Authorization": "Bearer editor-key"},
        json={
            "category_id": "urbanisme",
            "title": "Urbanisme",
            "applies_to": ["document"],
        },
    )
    assert response.status_code == 422
    assert called is False


def test_stale_category_update_maps_to_conflict(monkeypatch) -> None:
    def update_category(_conn, **_values):
        raise agency_classification.StaleCategoryWrite("stale Category revision")

    monkeypatch.setattr(agency_classification, "update_category", update_category)
    client = _client(editor_api_key="editor-key")
    response = client.patch(
        "/agency/categories/urbanisme",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json={"expected_revision": 2, "title": "Urbanisme réglementaire"},
    )
    assert response.status_code == 409
    assert "stale Category revision" in response.json()["detail"]


def test_explicit_null_sort_order_is_rejected_before_adapter(monkeypatch) -> None:
    called = False

    def update_category(_conn, **_values):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(agency_classification, "update_category", update_category)
    client = _client(editor_api_key="editor-key")
    response = client.patch(
        "/agency/categories/urbanisme",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json={"expected_revision": 1, "sort_order": None},
    )
    assert response.status_code == 422
    assert called is False
