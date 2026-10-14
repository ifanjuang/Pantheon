from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MVP = ROOT / "mvp_vertical"
COCKPIT = MVP / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"


def test_project_contacts_are_owned_by_project_json():
    sql = (MVP / "sql" / "002_agency_data.sql").read_text(encoding="utf-8")
    adapter = (MVP / "agency_data.py").read_text(encoding="utf-8")
    api = (MVP / "agency_data_api.py").read_text(encoding="utf-8")

    assert "contacts JSONB NOT NULL DEFAULT '[]'::jsonb" in sql
    # The column must also reach a database created before it existed. The
    # migration provides it through a catalog-guarded ALTER rather than
    # `ADD COLUMN IF NOT EXISTS`, so that a started-up installation takes no
    # ACCESS EXCLUSIVE lock on every boot; assert the outcome, not the phrasing.
    assert "ALTER TABLE agency_projects ADD COLUMN contacts JSONB" in sql
    assert "column_name = 'contacts'" in sql
    assert '"contacts"' in adapter
    assert "_normalize_contacts" in adapter
    assert "ProjectContactBody" in api


def test_legacy_project_participation_model_is_retired():
    sql = (MVP / "sql" / "002_agency_data.sql").read_text(encoding="utf-8")
    directory = (MVP / "agency_directory.py").read_text(encoding="utf-8")
    api = (MVP / "agency_data_api.py").read_text(encoding="utf-8")
    binding = (COCKPIT / "agency_data_binding.js").read_text(encoding="utf-8")
    context = (COCKPIT / "context" / "context_selection.js").read_text(encoding="utf-8")
    renderer = PROJECTION.read_text(encoding="utf-8")

    assert "DROP TABLE IF EXISTS agency_project_participations" in sql
    assert "CREATE TABLE IF NOT EXISTS agency_project_participations" not in sql
    assert "list_participations" not in directory
    assert "list_project_participations" not in directory
    assert '"/v1/agency/participations"' not in api
    assert '"/v1/agency/projects/{project_id}/participations"' not in api
    assert "project_participations" not in binding
    assert "project_participations" not in context
    assert "/participations" not in renderer
