from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_live_bootstrap_loads_canonical_card_interactions() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")

    assert '"interactions/card_interactions.js"' in bootstrap
    assert '"v3/cockpit_v3.js"' not in bootstrap
    assert (COCKPIT / "interactions" / "card_interactions.js").is_file()
    assert not (COCKPIT / "v3" / "cockpit_v3.js").exists()


def test_card_interactions_consume_only_canonical_card_structure() -> None:
    source = (COCKPIT / "interactions" / "card_interactions.js").read_text(encoding="utf-8")

    assert 'querySelectorAll(".card:not(' in source
    assert '.card-title' in source
    assert '.v2-card' not in source
    assert '.v2-card-title' not in source
    assert "PantheonCardInteractions" in source
    assert "PantheonCockpitV3" not in source


def test_card_interactions_do_not_own_navigation_or_authorization() -> None:
    source = (COCKPIT / "interactions" / "card_interactions.js").read_text(encoding="utf-8")

    for forbidden in (
        "slidePrev(",
        "slideNext(",
        "slideTo(",
        "/apply",
        "/reject",
        "/runs/start",
        "execution-admissions",
    ):
        assert forbidden not in source
