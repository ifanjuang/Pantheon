from pathlib import Path

from mvp_vertical import agency_schema


ROOT = Path(__file__).resolve().parents[1]
SCOPED_CONTEXT = ROOT / "mvp_vertical" / "hermes_scoped_context.py"


def test_hermes_information_projection_is_owned_by_named_schema_view() -> None:
    source = SCOPED_CONTEXT.read_text(encoding="utf-8")

    assert "INFORMATION_FIELDS" not in source
    assert 'agency_schema.information_record_for_view(raw, "hermes_context")' in source
    assert "def get_context_manifest(" in source
    assert "def get_context_entity(" in source


def test_information_hermes_view_excludes_non_declared_audit_fields() -> None:
    keys = agency_schema.get_information_view("hermes_context")["fields"]

    assert "information_id" in keys
    assert "revision" in keys
    assert "details" in keys
    assert "source_note" in keys
    assert "previous_source_id" not in keys
    assert "created_at" not in keys
    assert "updated_at" not in keys
    assert "acted_at" not in keys
