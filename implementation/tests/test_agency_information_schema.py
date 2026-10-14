from __future__ import annotations

import pytest

from mvp_vertical import agency_schema


def test_information_registry_declares_named_views_without_granting_authority() -> None:
    registry = agency_schema.get_information_registry()

    assert registry["schema_id"] == "agency.information.v1"
    assert registry["entity_type"] == "information"
    assert registry["authority"]["field_posture_is_authorization"] is False
    assert registry["authority"]["lifecycle_is_authorization"] is False
    assert {"cockpit_front", "cockpit_back", "edit", "notion", "hermes_context"} <= set(registry["views"])


def test_information_edit_view_excludes_source_identity_and_index() -> None:
    schema = agency_schema.get_information_schema("edit")
    keys = [field["key"] for field in schema["fields"]]

    assert schema["resolved_view"]["authorization_inferred"] is False
    assert "summary" in keys
    assert "details" in keys
    assert "status" in keys
    assert "source_ref" not in keys
    assert "source_note" not in keys
    assert "source_version" not in keys
    assert "source_type" not in keys
    assert "index_label" not in keys


def test_information_hermes_context_keeps_identity_revision_and_lineage() -> None:
    schema = agency_schema.get_information_schema("hermes_context")
    keys = [field["key"] for field in schema["fields"]]

    assert "information_id" in keys
    assert "series_id" in keys
    assert "project_id" in keys
    assert "revision" in keys
    assert "base_acted_id" in keys
    assert "acted_at" not in keys


def test_information_record_projection_uses_declared_view_order() -> None:
    record = {
        "information_id": "info-1",
        "series_id": "series-1",
        "project_id": "project-1",
        "title": "PLU",
        "category": "Urbanisme",
        "source_type": "document",
        "source_ref": "doc:plu",
        "source_note": None,
        "source_version": "v1",
        "index_label": "A01",
        "information_date": "2026-07-26",
        "summary": "Résumé",
        "details": "Détails",
        "author": "agency",
        "status": "draft",
        "limits": ["consultatif"],
        "type_tags": ["etude"],
        "subject_tags": ["urbanisme"],
        "base_acted_id": None,
        "revision": 3,
    }

    projected = agency_schema.information_record_for_view(record, "hermes_context")
    expected = agency_schema.get_information_view("hermes_context")["fields"]

    assert list(projected) == expected
    assert projected["information_id"] == "info-1"
    assert projected["revision"] == 3


def test_information_schema_rejects_unknown_view() -> None:
    with pytest.raises(agency_schema.AgencySchemaError, match="unknown Information schema view"):
        agency_schema.get_information_schema("invented")
