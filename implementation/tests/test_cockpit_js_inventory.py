from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
INVENTORY = ROOT / "docs" / "cockpit" / "JS_MODULE_INVENTORY.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_inventory_records_the_actual_live_boot_chain() -> None:
    bootstrap = _text(COCKPIT / "live_bootstrap.js")
    inventory = _text(INVENTORY)

    match = re.search(r"const scripts = \[(.*?)\];", bootstrap, re.S)
    assert match is not None
    loaded = re.findall(r'"([^"]+\.js)"', match.group(1))

    assert loaded
    for filename in loaded:
        assert f"`{filename}`" in inventory
        assert (COCKPIT / filename).is_file(), filename


def test_live_collection_uses_canonical_renderer_without_class_translation() -> None:
    adapter = _text(COCKPIT / "live_collection_adapter.js")
    renderer = _text(COCKPIT / "rendering" / "card_renderer.js")

    assert 'import { renderCanonicalCard } from "./rendering/card_renderer.js"' in adapter
    assert "CLASS_MAP" not in adapter
    assert "normalizeClasses" not in adapter
    assert "normalizeCard" not in adapter
    assert "renderCanonicalCard(model" in adapter
    assert 'wrapper.className = "card v2-card"' in renderer
    assert 'face.className = "card-face card-front' in renderer
    assert 'face.className = "card-face card-back' in renderer
    assert "card-blob" not in renderer


def test_neutral_entrypoints_replace_generation_named_files() -> None:
    html = _text(COCKPIT / "index.html")
    assert 'src="cockpit_bootstrap.js"' in html
    for current in ("cockpit_bootstrap.js", "live_bootstrap.js", "live_collection_adapter.js", "shell_controls.js"):
        assert (COCKPIT / current).is_file()
    for retired in ("v3_bootstrap.js", "v2_bootstrap.js", "v3_swiper.js", "v2_shell_controls.js"):
        assert not (COCKPIT / retired).exists()


def test_inventory_preserves_core_architectural_boundaries() -> None:
    inventory = _text(INVENTORY)
    for statement in (
        "visual projection != semantic model",
        "UI status != authorization",
        "runtime_success != Evidence",
        "Pantheon != runtime",
        "Swiper must remain isolated",
    ):
        assert statement in inventory


def test_dead_code_requires_all_reference_classes_to_be_empty() -> None:
    inventory = _text(INVENTORY)
    for reference_class in (
        "HTML script inclusion",
        "static import",
        "dynamic import",
        "ordered classic-script inclusion",
        "global produced and global consumed",
        "test or published regression surface dependency",
    ):
        assert reference_class in inventory
