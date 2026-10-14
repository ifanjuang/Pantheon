from pathlib import Path

from mvp_vertical import agency_schema


ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "mvp_vertical" / "cockpit" / "notion_agency_binding.js"


def test_notion_project_view_projects_only_declared_fields() -> None:
    registry = agency_schema.get_project_registry()
    notion = agency_schema.get_project_schema("notion")
    declared = registry["views"]["notion"]["fields"]

    assert notion["resolved_view"]["name"] == "notion"
    assert [field["key"] for field in notion["fields"]] == declared
    assert "revision" in declared
    assert "created_by" not in declared
    assert "updated_by" not in declared

    record = {
        "project_id": "project-test",
        "code": "TEST",
        "display_name": "Projet test",
        "description": "Description",
        "status": "active",
        "phase": "PRO",
        "location": "Rouen",
        "tags": ["erp"],
        "contacts": [{"group": "Maîtrise d’ouvrage", "name": "Client"}],
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
        "revision": 7,
        "created_by": "hidden-from-notion-view",
    }
    projected = agency_schema.project_record_for_view(record, "notion")

    assert list(projected) == declared
    assert projected["budget"] == 420000
    assert projected["surface_projet"] == 230.5
    assert projected["programme_summary"] == "ERP en rénovation"
    assert projected["revision"] == 7
    assert "created_by" not in projected


def test_notion_binding_derives_read_only_defaults_from_named_schema() -> None:
    source = BINDING.read_text(encoding="utf-8")

    assert "createProjectPoliciesFromSchema" in source
    assert 'resolved !== "notion"' in source
    assert 'notion_editable: false' in source
    assert 'sync_direction: "postgres_to_notion"' in source
    assert "options.projectSchema" in source
    assert "projectProjection(record" in source
    assert 'field.storage === "projection"' in source
    assert 'operation: "notion_projection_mutation_candidate"' in source
    assert "execution_authorized: false" in source
