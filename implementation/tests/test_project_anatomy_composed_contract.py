from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSED = ROOT / "mvp_vertical" / "cockpit_composed.py"
API = ROOT / "mvp_vertical" / "project_anatomy_api.py"


def test_composed_cockpit_applies_clean_owner_and_mounts_read_projection() -> None:
    source = COMPOSED.read_text(encoding="utf-8")

    assert 'conn.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))' in source
    assert "install_project_anatomy_routes(" in source


def test_project_anatomy_api_contains_no_mutation_route() -> None:
    source = API.read_text(encoding="utf-8")

    assert '@app.get("/agency/projects/{project_id}/project-anatomy")' in source
    for mutation in ("@app.post(", "@app.put(", "@app.patch(", "@app.delete("):
        assert mutation not in source
