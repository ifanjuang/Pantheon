from mvp_vertical import agency_schema, hermes_scoped_context


def test_hermes_project_materialization_uses_named_context_view(monkeypatch) -> None:
    record = {
        "project_id": "project-test",
        "code": "TEST",
        "display_name": "Projet test",
        "description": "Description projet",
        "status": "active",
        "phase": "PRO",
        "location": "Rouen",
        "tags": ["erp"],
        "attributes": {
            "programme_summary": "ERP en rénovation",
            "architectural_style": "Existant patrimonial",
        },
        "claim_values": {
            "budget": 420000,
            "surface_projet": 230.5,
            "plu_zone": "UC0",
            "permit_number": "PC-001",
            "erp_type": "5e catégorie",
        },
        "revision": 8,
        "created_by": "must-not-leak",
        "updated_by": "must-not-leak",
    }
    monkeypatch.setattr(
        hermes_scoped_context.agency_data,
        "get_project",
        lambda _conn, _project_id: record,
    )

    materialized = hermes_scoped_context.materialize_context_entity(
        None,
        entity_type="project",
        entity_id="project:project-test",
    )
    expected_fields = agency_schema.get_project_view("hermes_context")["fields"]

    assert list(materialized["record"]) == expected_fields
    assert materialized["record"]["budget"] == 420000
    assert materialized["record"]["surface_projet"] == 230.5
    assert materialized["record"]["programme_summary"] == "ERP en rénovation"
    assert materialized["record"]["revision"] == 8
    assert "created_by" not in materialized["record"]
    assert "updated_by" not in materialized["record"]
    assert materialized["record_owner_system"] == "postgres"


def test_hermes_context_view_is_projection_not_authorization() -> None:
    schema = agency_schema.get_project_schema("hermes_context")

    assert schema["resolved_view"]["name"] == "hermes_context"
    assert schema["resolved_view"]["authorization_inferred"] is False
    assert "revision" in [field["key"] for field in schema["fields"]]
