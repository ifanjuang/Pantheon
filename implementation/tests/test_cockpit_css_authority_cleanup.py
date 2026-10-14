from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
STYLES = COCKPIT / "styles"


def test_retired_visual_stylesheets_are_removed() -> None:
    retired = (
        "index.css", "v2.css", "v2_refinement.css", "v2_swiper.css",
        "v2_shell_controls.css", "v3_living_cards.css", "v3_card_tokens.css",
        "v3_card_blobs.css", "v3_card_project.css", "v3_card_work.css",
        "v3_geometry.css", "v3_collections.css", "schema_editor.css",
        "contacts_editor.css", "information_create.css", "project_claim_view.css",
    )
    for filename in retired:
        assert not (STYLES / filename).exists(), filename


def test_only_four_local_stylesheets_are_loaded_by_the_canonical_page() -> None:
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")
    local_hrefs = [
        line.split('href="', 1)[1].split('"', 1)[0]
        for line in html.splitlines()
        if '<link rel="stylesheet" href="styles/' in line
    ]
    assert local_hrefs == [
        "styles/cockpit.css", "styles/cards.css", "styles/families.css", "styles/editors.css",
    ]


def test_three_effects_share_the_complete_recto_coordinate_system() -> None:
    cards = (STYLES / "cards.css").read_text(encoding="utf-8")
    families = (STYLES / "families.css").read_text(encoding="utf-8")
    assert ".card-front > .card-top" in cards
    assert ".card-front > .card-body" in cards
    assert "position: static" in cards
    for selector in (".card-front::before", ".card-front::after", ".card-body::before"):
        assert selector in cards
    assert "width: var(--effect-width, 50%)" in cards
    assert "height: var(--effect-height, 50%)" in cards
    assert "top: 50%" in cards
    assert "left: 50%" in cards
    for index in (1, 2, 3):
        assert f"--effect-{index}-top: 50%" in families
        assert f"--effect-{index}-left: 50%" in families
