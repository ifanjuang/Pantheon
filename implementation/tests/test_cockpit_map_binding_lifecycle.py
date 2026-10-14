"""Lifecycle guards for the live Cockpit map binding and mobile fallback."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
BINDING = COCKPIT / "map_binding.js"
RENDERER = COCKPIT / "rendering" / "card_renderer.js"
BOOT = COCKPIT / "live_bootstrap.js"
INDEX = COCKPIT / "index.html"
CSS = COCKPIT / "styles" / "cockpit.css"


def test_map_binding_owns_one_pantheon_verso_host_for_all_render_paths() -> None:
    binding = BINDING.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")

    assert "function createLens()" in binding
    assert "function ensureLens(card)" in binding
    assert "stage.querySelectorAll('.card[data-family=\"pantheon\"]')" in binding
    assert 'card.querySelector(".card-back-body") || card.querySelector(".card-back")' in binding
    assert 'lens.dataset.pantheonMapLens = "true"' in binding
    assert 'svg.dataset.pantheonMap = "true"' in binding
    assert "pantheonMapLens" not in renderer


def test_live_map_mounts_and_cleans_removed_pantheon_hosts() -> None:
    source = BINDING.read_text(encoding="utf-8")

    assert "new MutationObserver(sync)" in source
    assert "window.PantheonMapMount.mountLive(svg, opts)" in source
    assert "state.mount.destroy();" in source
    assert "mounts.delete(lens);" in source


def test_global_map_toggle_and_overlay_are_retired_from_the_shell() -> None:
    html = INDEX.read_text(encoding="utf-8")
    binding = BINDING.read_text(encoding="utf-8")

    for token in ("v2-map-toggle", "v2-map-panel", "v2-map-close"):
        assert token not in html
        assert token not in binding


def test_mobile_shell_is_headerless_when_swiper_navigation_is_ready() -> None:
    source = CSS.read_text(encoding="utf-8")

    assert "@media (max-width: 620px)" in source
    assert ".v3-header,\n    .v2-location { display: none; }" in source
    assert 'html[data-cockpit-navigation="swiper"] .v3-navigation-bridge { display: none; }' in source
    assert 'html[data-cockpit-navigation="swiper"] .v3-shell' in source
    assert "grid-template-rows: minmax(0, 1fr);" in source
    assert ".v3-stage { grid-row: 1; }" in source


def test_non_swiper_fallback_keeps_navigation_controls_reachable() -> None:
    boot = BOOT.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    assert 'dataset.cockpitNavigation = swiperReady ? "swiper" : "fallback"' in boot
    assert 'for (const id of ["v2-previous", "v2-next"])' in boot
    assert "control.hidden = false;" in boot
    assert 'html[data-cockpit-navigation="fallback"] .v3-shell' in css
    assert "grid-template-rows: minmax(0, 1fr) auto;" in css
    assert 'html[data-cockpit-navigation="fallback"] .v3-navigation-bridge' in css
