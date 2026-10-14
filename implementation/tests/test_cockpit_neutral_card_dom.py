from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_live_collection_renders_canonical_dom_without_translation() -> None:
    adapter = (COCKPIT / "live_collection_adapter.js").read_text(encoding="utf-8")
    renderer = (COCKPIT / "rendering" / "card_renderer.js").read_text(encoding="utf-8")

    assert "const CLASS_MAP" not in adapter
    assert "normalizeClasses" not in adapter
    assert "normalizeCard" not in adapter
    assert "renderCanonicalCard(model" in adapter
    assert 'wrapper.className = "card v2-card"' in renderer
    assert 'inner.className = "card-inner v2-card-inner"' in renderer
    assert 'face.className = "card-face card-front' in renderer
    assert 'face.className = "card-face card-back' in renderer
    assert "wrapper.dataset.level" in renderer
    assert "wrapper.dataset.family" in renderer
    assert "wrapper.dataset.kind" in renderer
    assert "--project-accent" in renderer


def test_live_adapter_does_not_inject_decorative_dom() -> None:
    adapter = (COCKPIT / "live_collection_adapter.js").read_text(encoding="utf-8")
    renderer = (COCKPIT / "rendering" / "card_renderer.js").read_text(encoding="utf-8")

    for decorative_contract in (
        "ensureBlobPrimitive",
        "card-blobs",
        "card-blob",
        "index <= 3",
    ):
        assert decorative_contract not in adapter
        assert decorative_contract not in renderer


def test_canonical_card_css_has_no_legacy_or_decorative_dom_selectors() -> None:
    cards = (COCKPIT / "styles" / "cards.css").read_text(encoding="utf-8")

    for legacy in (
        ".v2-card",
        ".v2-card-inner",
        ".v2-card-face",
        ".v2-card-front",
        ".v2-card-back",
        ".v2-card-title",
    ):
        assert legacy not in cards

    for primitive in (
        ".card",
        ".card-inner",
        ".card-face",
        ".card-front",
        ".card-back",
    ):
        assert primitive in cards

    for decorative_dom_selector in (".card-blobs", ".card-blob"):
        assert decorative_dom_selector not in cards

    for css_effect_layer in (
        ".card-front::before",
        ".card-front::after",
        ".card-body::before",
        ".card-back::after",
        ".card-top::after",
    ):
        assert css_effect_layer in cards
