from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
ADAPTER = COCKPIT / "information_view_adapter.js"
V2_HTML = COCKPIT / "index.html"
PROJECTION_MODULE = '"projection/cockpit_projection.js"'


def test_information_view_adapter_consumes_server_card_contract() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    assert "/agency/information/${encodeURIComponent(informationId)}/context" in source
    assert "/agency/projects/${encodeURIComponent(projectId)}/information" in source
    assert "/v1/agency/" not in source
    assert "payload.card_contract?.back" in source
    assert "schema.fields" in source
    assert "field.label" in source
    assert "data-schema-field" not in source


def test_information_view_adapter_respects_cardshell_slots() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    for field in (
        '"title"',
        '"category"',
        '"status"',
        '"index_label"',
        '"information_date"',
        '"limits"',
        '"type_tags"',
        '"subject_tags"',
    ):
        assert field in source

    assert '"Résumé"' not in source
    assert '"Informations détaillées"' not in source
    assert '"Version source"' not in source


def test_information_view_adapter_is_loaded_after_main_renderer() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")

    renderer = bootstrap.index(PROJECTION_MODULE)
    adapter = bootstrap.index('"information_view_adapter.js"')
    editor = bootstrap.index('"schema_editor.js"')
    assert renderer < adapter < editor
