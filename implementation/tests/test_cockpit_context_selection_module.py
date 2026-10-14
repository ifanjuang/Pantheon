from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_context_selection_module_replaces_generation_named_bridge() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    source = (COCKPIT / "context" / "context_selection.js").read_text(encoding="utf-8")

    assert '"context/context_selection.js"' in bootstrap
    assert '"v2_context.js"' not in bootstrap
    assert not (COCKPIT / "v2_context.js").exists()
    assert 'effect !== "read_only"' in source
    assert 'owner_system !== "postgres"' in source
    assert 'scope_widened_implicitly: false' in source
    assert 'Sélection ≠ Evidence.' in source
    assert "../agency/projects?" in source
    assert "../agency/people?" in source
    assert "../agency/organizations?" in source
    assert "/v1/agency/" not in source
