from __future__ import annotations

import uuid

import pytest

from mvp_vertical import agency_data, agency_schema


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def test_project_registry_declares_fields_and_named_views_without_granting_authority() -> None:
    registry = agency_schema.get_project_registry()
    assert registry["entity_type"] == "project"
    assert registry["version"] == 2
    assert registry["schema_id"] == "agency.project.v2"
    assert registry["authority"]["system_of_record"] == "postgres"
    assert registry["authority"]["field_posture_is_authorization"] is False

    fields = {field["key"]: field for field in registry["fields"]}
    assert fields["budget"]["storage"] == "projection"
    assert fields["budget"]["semantics"] == "claim"
    assert fields["budget"]["claim_type"] == "budget"
    assert fields["budget"]["mutable"] is False
    assert fields["programme_summary"]["storage"] == "attributes"
    assert fields["revision"]["storage"] == "system"
    assert fields["revision"]["hermes_mode"] == "system"

    assert set(registry["views"]) >= {
        "cockpit_front",
        "cockpit_back",
        "edit",
        "notion",
        "hermes_context",
    }
    assert "revision" not in registry["views"]["cockpit_back"]["fields"]
    assert "revision" in registry["views"]["hermes_context"]["fields"]


def test_project_schema_defaults_to_named_cockpit_back_projection() -> None:
    schema = agency_schema.get_project_schema()
    registry = agency_schema.get_project_registry()

    assert schema["resolved_view"]["name"] == "cockpit_back"
    assert schema["resolved_view"]["authorization_inferred"] is False
    assert [field["key"] for field in schema["fields"]] == registry["views"]["cockpit_back"]["fields"]
    assert "project_id" not in [field["key"] for field in schema["fields"]]
    assert "budget" in [field["key"] for field in schema["fields"]]


def test_project_named_views_are_distinct_projections_not_authorization() -> None:
    edit = agency_schema.get_project_schema("edit")
    notion = agency_schema.get_project_schema("notion")
    hermes = agency_schema.get_project_schema("hermes_context")

    assert edit["resolved_view"]["name"] == "edit"
    assert notion["resolved_view"]["name"] == "notion"
    assert hermes["resolved_view"]["name"] == "hermes_context"
    assert all(view["authority"]["field_posture_is_authorization"] is False for view in (edit, notion, hermes))

    edit_keys = [field["key"] for field in edit["fields"]]
    notion_keys = [field["key"] for field in notion["fields"]]
    hermes_keys = [field["key"] for field in hermes["fields"]]
    assert "description" in edit_keys
    assert "budget" not in edit_keys
    assert "budget" in notion_keys
    assert "budget" in hermes_keys
    assert "description" not in notion_keys
    assert "revision" in hermes_keys

    with pytest.raises(agency_schema.AgencySchemaError, match="unknown Project schema view"):
        agency_schema.get_project_schema("invented")


def test_project_descriptive_attributes_are_normalized_by_registry() -> None:
    normalized = agency_schema.normalize_project_attributes(
        {
            "programme_summary": " Maison familiale ",
            "architectural_style": " Normand contemporain ",
            "agency_notes": " À confirmer en APD ",
        }
    )
    assert normalized == {
        "programme_summary": "Maison familiale",
        "architectural_style": "Normand contemporain",
        "agency_notes": "À confirmer en APD",
    }


def test_project_attributes_reject_claim_fields_unknown_or_wrong_types() -> None:
    with pytest.raises(agency_schema.AgencySchemaError, match="unsupported Project attribute"):
        agency_schema.normalize_project_attributes({"invented_field": "x"})
    with pytest.raises(agency_schema.AgencySchemaError, match="unsupported Project attribute field.*budget"):
        agency_schema.normalize_project_attributes({"budget": 600000})
    with pytest.raises(agency_schema.AgencySchemaError, match="programme_summary must be a string"):
        agency_schema.normalize_project_attributes({"programme_summary": 123})


def test_project_descriptive_attributes_round_trip_through_postgres_when_available() -> None:
    try:
        conn = agency_data.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    project_id = _id("project-schema")
    try:
        created = agency_data.create_project(
            conn,
            project_id=project_id,
            code=_id("SCHEMA")[:24],
            display_name="Projet schema-driven",
            actor="human",
            actor_kind="human",
            idempotency_key=_id("create"),
            attributes={
                "programme_summary": "Maison familiale",
                "architectural_style": "Normand contemporain",
            },
        )
        assert created["attributes"] == {
            "programme_summary": "Maison familiale",
            "architectural_style": "Normand contemporain",
        }
        assert created["claim_values"] == {}

        updated = agency_data.update_project(
            conn,
            project_id=project_id,
            changes={
                "attributes": {
                    "programme_summary": "Maison familiale avec piscine",
                    "architectural_style": "Normand contemporain",
                    "agency_notes": "À confirmer",
                }
            },
            actor="human",
            actor_kind="human",
            expected_revision=created["revision"],
            idempotency_key=_id("update"),
        )
        assert updated["revision"] == created["revision"] + 1
        assert updated["attributes"]["agency_notes"] == "À confirmer"
        assert "budget" not in updated["attributes"]
    finally:
        conn.close()


def test_project_schema_is_exposed_by_agency_api_and_packaged() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    api = (root / "mvp_vertical" / "agency_data_api.py").read_text(encoding="utf-8")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '@app.get("/agency/schema/project")' in api
    assert '/v1/agency/' not in api
    assert "attributes: dict[str, Any]" in api
    assert '"agency_schema/*.json"' in pyproject
    assert agency_schema.DEFAULT_PROJECT_VIEW == "cockpit_back"