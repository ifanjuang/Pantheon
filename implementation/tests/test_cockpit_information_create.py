from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
CREATE = COCKPIT / "information_create.js"
HTML = COCKPIT / "index.html"
SCHEMA = ROOT / "mvp_vertical" / "agency_schema" / "information.json"


def test_project_loads_removable_blank_information_creation_surface() -> None:
    html = HTML.read_text(encoding="utf-8")
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    editors = (COCKPIT / "styles" / "editors.css").read_text(encoding="utf-8")

    assert '"information_create.js"' in bootstrap
    assert 'href="styles/editors.css"' in html
    assert '.v2-information-create-dialog' in editors
    assert CREATE.exists()


def test_blank_information_surface_has_exact_three_source_modes() -> None:
    source = CREATE.read_text(encoding="utf-8")
    assert 'file: Object.freeze({ source_type: "file", label: "Fichier"' in source
    assert 'link: Object.freeze({ source_type: "link", label: "Lien"' in source
    assert 'draft: Object.freeze({ source_type: "draft", label: "Brouillon"' in source
    assert 'title.textContent = "Nouvelle information"' in source
    assert 'detail.textContent = "Fichier · Lien · Brouillon"' in source


def test_blank_information_is_not_persisted_until_human_create() -> None:
    source = CREATE.read_text(encoding="utf-8")
    assert 'method: "POST"' in source
    assert '/information`, payload' in source
    assert 'submit.textContent = "Créer"' in source
    assert "Pantheon ne stocke pas le fichier" in source
    assert "/upload" not in source
    assert "/ingest" not in source
    assert "/runs/start" not in source


def test_information_registry_declares_creation_projection_separate_from_edit() -> None:
    registry = json.loads(SCHEMA.read_text(encoding="utf-8"))
    create_fields = set(registry["views"]["create"]["fields"])
    edit_fields = set(registry["views"]["edit"]["fields"])
    assert {"source_type", "source_ref", "source_note", "source_version", "index_label"} <= create_fields
    assert not ({"source_type", "source_ref", "source_note", "source_version", "index_label"} & edit_fields)
    assert registry["authority"]["lifecycle_is_authorization"] is False
