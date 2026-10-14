from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"


def test_contacts_editor_is_dedicated_and_project_owned() -> None:
    source = (COCKPIT / "contacts_editor.js").read_text(encoding="utf-8")
    assert 'const GROUPS = Object.freeze([' in source
    assert '"Maîtrise d’ouvrage"' in source
    assert '"Bureaux d’études"' in source
    assert '"Entreprises de travaux"' in source
    assert 'expected_revision: state.project.revision' in source
    assert 'contacts,' in source
    assert 'method: "PATCH"' in source
    assert 'project:(.+):contacts' in source
    assert "participation" not in source.lower()


def test_contacts_editor_keeps_optional_connector_provenance_as_data_only() -> None:
    source = (COCKPIT / "contacts_editor.js").read_text(encoding="utf-8")
    assert '"source_ref", "Source / Google Contact"' in source
    assert "googleapis" not in source.lower()
    assert "fetch('https://" not in source.lower()
    assert "browser_sync_execution" not in source


def test_contacts_editor_is_loaded_as_an_independent_module() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    editors = (COCKPIT / "styles" / "editors.css").read_text(encoding="utf-8")
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")

    assert '"contacts_editor.js"' in bootstrap
    assert '.v2-contacts-editor' in editors
    assert 'href="styles/editors.css"' in html
    assert "PantheonContactsEditor" not in PROJECTION.read_text(encoding="utf-8")
    assert "PantheonContactsEditor" not in (COCKPIT / "schema_editor.js").read_text(encoding="utf-8")
