from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
HTML = COCKPIT / "index.html"
STYLES = COCKPIT / "styles"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_current_styles_replace_historical_refinement_chain() -> None:
    html = _text(HTML)
    for filename in ("cockpit.css", "cards.css", "families.css", "editors.css"):
        assert f'href="styles/{filename}"' in html
    for retired in ("v2.css", "v2_refinement.css", "v2_shell_controls.css"):
        assert retired not in html


def test_card_typography_is_controlled_by_level_variables() -> None:
    cards = _text(STYLES / "cards.css")
    families = _text(STYLES / "families.css")
    assert "var(--card-title-size" in cards
    assert "letter-spacing: -.045em" in cards
    assert "text-wrap: balance" in cards
    for level in ("pack", "booster", "card"):
        assert f'[data-level="{level}"]' in families
        assert "--card-title-size" in families


def test_motion_uses_detail_state_and_continuous_blob_rotation() -> None:
    cards = _text(STYLES / "cards.css")
    assert "rotateY(180deg)" not in cards
    assert "perspective:" not in cards
    assert 'card[data-flipped="true"] .card-front' in cards
    assert 'card[data-flipped="true"] .card-back' in cards
    assert "transition: opacity 180ms ease" in cards
    assert "card-blob-rotate-forward" in cards
    assert "card-blob-rotate-reverse" in cards
    assert "prefers-reduced-motion" not in cards
    assert ":hover" not in cards


def test_family_palettes_do_not_redefine_status_authority() -> None:
    families = _text(STYLES / "families.css")
    for family in ("knowledge", "skills", "tools", "affaires"):
        assert f'[data-family="{family}"]' in families
    assert "--status-ready" not in families
    assert "--status-review" not in families


def test_mobile_surface_keeps_navigation_controls_and_card_first_layout() -> None:
    html = _text(HTML)
    cockpit = _text(STYLES / "cockpit.css")
    for control_id in ("v2-previous", "v2-next", "v2-descend", "v2-ascend", "v2-flip"):
        assert f'id="{control_id}"' in html
    assert "@media" in cockpit
    assert ".v3-stage" in cockpit
    assert ".v2-navigation" in cockpit or ".v3-navigation" in cockpit


def test_live_stage_has_a_definite_viewport_height() -> None:
    cockpit = _text(STYLES / "cockpit.css")
    assert "height: 100dvh" in cockpit
    assert ".v3-stage" in cockpit
    assert "height: 100%" in cockpit
    assert ".v3-stage .swiper-wrapper" in cockpit


def test_live_schema_cards_enter_the_design_system_canonically() -> None:
    cards = _text(STYLES / "cards.css")
    adapter = _text(COCKPIT / "live_collection_adapter.js")
    renderer = _text(COCKPIT / "rendering" / "card_renderer.js")
    for historical_selector in (".v2-card", ".v2-card-inner", ".v2-card-face", ".v2-card-front", ".v2-card-back"):
        assert historical_selector not in cards
    assert "CLASS_MAP" not in adapter
    assert "normalizeCard" not in adapter
    assert "renderCanonicalCard(model" in adapter
    assert 'wrapper.className = "card v2-card"' in renderer
    for axis in ("level", "family", "kind", "status"):
        assert f"wrapper.dataset.{axis}" in renderer


def test_effects_and_card_spacing_are_card_relative() -> None:
    cockpit = _text(STYLES / "cockpit.css")
    cards = _text(STYLES / "cards.css")
    families = _text(STYLES / "families.css")
    assert "--cockpit-card-inset" in cockpit
    assert ".v3-shell" in cockpit and "padding: 0" in cockpit
    assert "inset: var(--cockpit-card-inset)" in cards
    assert "width: var(--effect-width, 50%)" in cards
    assert "height: var(--effect-height, 50%)" in cards
    assert "left: 50%" in cards
    assert "top: 50%" in cards
    assert "75vw" not in families
    assert "75vh" not in families


def test_back_border_does_not_change_content_geometry() -> None:
    cards = _text(STYLES / "cards.css")
    cockpit = _text(STYLES / "cockpit.css")
    assert ".card-face" in cards
    assert "border: 0" in cards
    assert ".card-back::after" in cards
    assert "border: var(--card-back-border-width" in cards
    assert "pointer-events: none" in cards
    assert "--cockpit-back-border-business: 1px" in cockpit
    assert "--cockpit-back-border-general: 12px" in cockpit


def test_detail_faces_are_layered_without_3d_mirroring() -> None:
    cards = _text(STYLES / "cards.css")
    assert "backface-visibility" not in cards
    assert "transform-style: preserve-3d" not in cards
    assert "rotateY(" not in cards
    assert '.card[data-flipped="true"] .card-back' in cards


def test_flip_uses_the_neutral_card_contract_for_pointer_and_keyboard() -> None:
    """Flip state is a data attribute driven by one shared interaction module.

    Demo and live now share this module: the retired demo island carried its
    own copy of the flip, which could drift from the live behaviour.
    """
    interactions = _text(COCKPIT / "interactions" / "card_interactions.js")
    assert 'card.dataset.flipped = String(next)' in interactions
    assert 'card.addEventListener("keydown"' in interactions
    assert 'card.addEventListener("pointerdown"' in interactions
    assert "pantheon:card-flip" in interactions
    # Accessibility state travels with the flip, not with a mirrored transform.
    assert 'card.setAttribute("aria-label"' in interactions
    assert 'card.setAttribute("aria-roledescription", "carte recto verso")' in interactions
