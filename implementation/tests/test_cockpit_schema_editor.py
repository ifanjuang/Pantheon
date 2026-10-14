from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"


def test_project_edit_view_is_generic_and_keeps_claims_and_contacts_out() -> None:
    registry = json.loads((ROOT / "mvp_vertical" / "agency_schema" / "project.json").read_text(encoding="utf-8"))
    edit_fields = registry["views"]["edit"]["fields"]
    assert "code" in edit_fields
    assert "display_name" in edit_fields
    assert "programme_summary" in edit_fields
    assert "architectural_style" in edit_fields
    assert "agency_notes" in edit_fields
    assert "budget" not in edit_fields
    assert "surface_projet" not in edit_fields
    assert "contacts" not in edit_fields


def test_schema_editor_uses_field_renderer_registry_without_business_field_switches() -> None:
    source = (COCKPIT / "schema_editor.js").read_text(encoding="utf-8")
    assert 'request("../agency/schema/project?view=edit")' in source
    assert "../v1/agency/" not in source
    for renderer in ("string", "enum", "number", "date", "string_list"):
        assert f'registerRenderer("{renderer}"' in source
    assert 'field.storage === "attributes"' in source
    assert "expected_revision: entity.revision" in source
    assert 'method: "PATCH"' in source
    assert 'field.key === "budget"' not in source
    assert 'field.key === "plu_zone"' not in source
    assert 'field.key === "surface_projet"' not in source


def test_schema_editor_is_a_removable_cockpit_module() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")
    editors = (COCKPIT / "styles" / "editors.css").read_text(encoding="utf-8")

    assert '"schema_editor.js"' in bootstrap
    assert 'href="styles/editors.css"' in html
    assert '.v2-schema-editor' in editors
    assert "schema_editor.js" not in PROJECTION.read_text(encoding="utf-8")
    assert "PantheonSchemaEditor" not in (COCKPIT / "actions" / "card_actions.js").read_text(encoding="utf-8")


def test_schema_editor_does_not_turn_project_contacts_into_generic_json_editing() -> None:
    source = (COCKPIT / "schema_editor.js").read_text(encoding="utf-8")
    assert 'registerRenderer("object_list"' not in source
    assert 'entityId.includes(":contacts")' in source
    assert (COCKPIT / "contacts_editor.js").exists()