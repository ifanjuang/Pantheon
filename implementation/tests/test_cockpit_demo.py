from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_demo_redirects_to_current_cockpit_and_not_retired_demo_assets():
    html = (COCKPIT / "demo.html").read_text(encoding="utf-8")

    assert "index.html?mode=demo" in html
    assert "v2.html?mode=demo" not in html
    assert 'href="styles/demo.css"' not in html
    assert '<script src="demo.js"' not in html
    assert '<script src="app.js"' not in html


def test_demo_bootstrap_loads_current_modules():
    demo_bootstrap = (COCKPIT / "demo_bootstrap.js").read_text(encoding="utf-8")
    live_bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    cockpit_html = (COCKPIT / "index.html").read_text(encoding="utf-8")

    assert 'src="cockpit_bootstrap.js"' in cockpit_html

    modules = [
        "structured_interface.js",
        "context_resolver.js",
        "agency_data_binding.js",
        "spatial_navigation.js",
        "projection/cockpit_projection.js",
        "interactions/interaction_policy.js",
        "project_claim_view_adapter.js",
        "information_view_adapter.js",
        "context/context_selection.js",
        "handoff/handoff_lifecycle.js",
        "handoff/handoff_send.js",
        "actions/card_actions.js",
        "actions/change_candidate_actions.js",
        "schema_editor.js",
        "contacts_editor.js",
        "information_create.js",
    ]
    assert "demo-data.json" in demo_bootstrap
    for module in modules:
        assert module in live_bootstrap


def test_demo_fixture_is_fictional_and_read_only():
    fixture = json.loads((COCKPIT / "demo-data.json").read_text(encoding="utf-8"))
    bootstrap = (COCKPIT / "demo_bootstrap.js").read_text(encoding="utf-8")

    assert {project["project_id"] for project in fixture["projects"]} == {
        "demo-vallons",
        "demo-falaises",
        "demo-horizon",
        "demo-tilleuls",
    }
    assert "Démonstration statique : écriture désactivée" in bootstrap
    assert 'method !== "GET"' in bootstrap
    assert "demo-data.json" in bootstrap
