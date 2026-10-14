from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
SCHEMA_EDITOR = COCKPIT / "schema_editor.js"
CONTACTS_EDITOR = COCKPIT / "contacts_editor.js"
INFORMATION_SCHEMA = ROOT / "mvp_vertical" / "agency_schema" / "information.json"
AGENCY_INFORMATION = ROOT / "mvp_vertical" / "agency_information.py"


def test_schema_editor_is_multi_entity_and_contacts_stay_separate() -> None:
    source = SCHEMA_EDITOR.read_text(encoding="utf-8")

    assert "project: Object.freeze" in source
    assert "information: Object.freeze" in source
    assert "openInformation" in source
    assert 'return ["draft", "in_progress"].includes' in source
    assert CONTACTS_EDITOR.exists()
    assert "object_list" not in source


def test_information_editor_uses_context_supplied_schema() -> None:
    source = SCHEMA_EDITOR.read_text(encoding="utf-8")
    domain = AGENCY_INFORMATION.read_text(encoding="utf-8")

    assert "/agency/information/${encodeURIComponent(id)}/context" in source
    assert "/v1/agency/" not in source
    assert "context.edit_schema" in source
    assert '"edit_schema": agency_schema.get_information_schema("edit")' in domain
    assert '"schema_authorization_inferred": False' in domain


def test_information_schema_keeps_source_versioning_outside_generic_editor() -> None:
    import json

    schema = json.loads(INFORMATION_SCHEMA.read_text(encoding="utf-8"))
    edit_fields = set(schema["views"]["edit"]["fields"])
    source_fields = {"source_type", "source_ref", "source_note", "source_version", "index_label"}

    assert not (source_fields & edit_fields)
    status = next(field for field in schema["fields"] if field["key"] == "status")
    assert status["values"] == ["draft", "in_progress", "acted", "superseded"]
    assert status["editor"]["values"] == ["draft", "in_progress"]