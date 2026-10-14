from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
STYLES = COCKPIT / "styles"


def test_clean_slate_has_four_authority_files() -> None:
    expected = {"cockpit.css", "cards.css", "families.css", "editors.css"}
    for name in expected:
        assert (STYLES / name).is_file()


def test_css_layers_and_responsibilities_are_explicit() -> None:
    cockpit = (STYLES / "cockpit.css").read_text(encoding="utf-8")
    cards = (STYLES / "cards.css").read_text(encoding="utf-8")
    families = (STYLES / "families.css").read_text(encoding="utf-8")
    editors = (STYLES / "editors.css").read_text(encoding="utf-8")

    layer_order = "@layer reset, tokens, shell, navigation, cards, families, states, editors, responsive;"
    for css in (cockpit, cards, families, editors):
        assert layer_order in css

    assert ".card-inner" in cards
    assert ".card-front::before" in cards
    assert ".card-front::after" in cards
    assert ".card-body::before" in cards
    assert "--effect-width" in cards
    assert "--marker-clip" in cards
    assert ".card-back::after" in cards
    assert '[data-kind="work"]' not in cards
    assert '[data-kind="folder"]' not in cards
    assert '[data-family="knowledge"]' in families
    assert '[data-family="skills"]' in families
    assert "display:" not in families
    assert "position:" not in families
    assert ".v2-schema-editor" in editors
    assert ".v2-contacts-editor" in editors
    assert ".v2-information-create-dialog" in editors


def test_renderer_projects_visual_axes_without_style_presets() -> None:
    renderer = (COCKPIT / "rendering" / "card_renderer.js").read_text(encoding="utf-8")

    assert "wrapper.dataset.level = axes.level" in renderer
    assert "wrapper.dataset.kind = axes.kind" in renderer
    assert "wrapper.dataset.family" in renderer
    assert "wrapper.dataset.status" in renderer
    assert 'kind = "folder"' in renderer
    assert 'kind = "work"' in renderer
    assert "BLOB_FAMILIES" not in renderer
    assert "blobSignature" not in renderer

    for filename in ("cockpit.css", "cards.css", "families.css", "editors.css"):
        assert filename not in renderer

    # `v2-card` is deliberately retained by the canonical renderer as the CSS
    # hook the live stylesheets bind to (locked by test_cockpit_js_inventory).
    # Only the decorative primitives are retired.
    for legacy in ("v3-card-blobs", "v3-card-blob", "card-blobs", "card-blob"):
        assert legacy not in renderer


def test_visual_markers_remain_twelve_pixels_and_flat() -> None:
    cockpit = (STYLES / "cockpit.css").read_text(encoding="utf-8")
    cards = (STYLES / "cards.css").read_text(encoding="utf-8")
    families = (STYLES / "families.css").read_text(encoding="utf-8")

    assert "--cockpit-accent-size: 12px" in cockpit
    assert "var(--cockpit-accent-size)" in families
    assert "--marker-clip" in cards
    for forbidden in ("box-shadow", "filter: blur", "backdrop-filter"):
        assert forbidden not in cards
        assert forbidden not in families


def test_level_family_kind_status_and_context_stay_independent() -> None:
    families = (STYLES / "families.css").read_text(encoding="utf-8")

    for level in ("pack", "booster", "card"):
        assert f'[data-level="{level}"]' in families

    for family in ("pantheon", "affaires", "knowledge", "skills"):
        assert f'[data-family="{family}"]' in families

    for kind in ("project", "work", "folder"):
        assert f'[data-kind="{kind}"]' in families

    assert "--project-accent" in families
    assert "data-status" not in families


def test_canonical_page_loads_only_four_local_stylesheets() -> None:
    index = (COCKPIT / "index.html").read_text(encoding="utf-8")
    expected = (
        "styles/cockpit.css",
        "styles/cards.css",
        "styles/families.css",
        "styles/editors.css",
    )
    for href in expected:
        assert f'href="{href}"' in index

    retired = (
        "styles/index.css",
        "styles/v2.css",
        "styles/v2_refinement.css",
        "styles/v2_swiper.css",
        "styles/v2_shell_controls.css",
        "styles/v3_living_cards.css",
        "styles/v3_card_tokens.css",
        "styles/v3_card_blobs.css",
        "styles/v3_card_project.css",
        "styles/v3_card_work.css",
        "styles/v3_geometry.css",
        "styles/v3_collections.css",
        "styles/schema_editor.css",
        "styles/contacts_editor.css",
        "styles/information_create.css",
        "styles/project_claim_view.css",
    )
    for href in retired:
        assert f'href="{href}"' not in index
