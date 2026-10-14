from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
MOTION = COCKPIT / "collection" / "motion_adapter.js"


def _read(path: str) -> str:
    return (COCKPIT / path).read_text(encoding="utf-8")


def _run_module(body: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; JavaScript behavior check skipped")
    return subprocess.run(
        [node, "--input-type=module", "-e", body],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_horizontal_arrow_controls_are_visually_retired_but_compatibility_ids_remain():
    html = _read("index.html")

    previous = next(line for line in html.splitlines() if 'id="v2-previous"' in line)
    next_button = next(line for line in html.splitlines() if 'id="v2-next"' in line)
    assert " hidden" in previous
    assert " hidden" in next_button

    for control_id in ("v2-ascend", "v2-flip", "v2-descend"):
        line = next(line for line in html.splitlines() if f'id="{control_id}"' in line)
        assert " hidden" not in line


def test_collection_controller_uses_one_responsive_motion_boundary():
    controller = _read("collection/collection_controller.js")
    motion = _read("collection/motion_adapter.js")

    assert 'import { createResponsiveMotion } from "./motion_adapter.js";' in controller
    assert "createResponsiveMotion({" in controller
    assert "createWindowedMotion({" not in controller

    assert "const EXPANDED_MIN_STAGE_WIDTH = 760;" in motion
    assert "const EXPANDED_MIN_CARD_WIDTH = 230;" in motion
    assert "const EXPANDED_MAX_ITEMS = 6;" in motion
    assert "export function canExpandCollection(" in motion
    assert "function createExpandedMotion(" in motion
    assert "export function createResponsiveMotion(" in motion
    assert "createWindowedMotion(common)" in motion
    assert 'presentation === "expanded"' in motion
    assert 'presentation: "compact"' in motion
    assert "ResizeObserver" in motion


def test_expanded_mode_requires_the_whole_bounded_level_to_fit():
    result = _run_module(
        f"""
        import {{ canExpandCollection }} from {MOTION.as_uri()!r};
        const expect = (value, label) => {{ if (!value) throw new Error(label); }};
        expect(!canExpandCollection({{ width: 5000, count: 7 }}), "seven items must exceed the DOM budget");
        expect(!canExpandCollection({{ width: 1250, count: 1 }}), "one item does not need expanded sibling mode");
        expect(!canExpandCollection({{ width: 1249, count: 5 }}), "five cards must not expand when they do not all fit");
        expect(canExpandCollection({{ width: 1250, count: 5 }}), "five cards should expand at their exact fit budget");
        expect(canExpandCollection({{ width: 1004, count: 4 }}), "four cards should expand when the whole row fits");
        """
    )
    assert result.returncode == 0, result.stderr


def test_expanded_collection_reuses_existing_provider_controller_renderer_and_graph():
    adapter = _read("live_collection_adapter.js")

    assert adapter.count("createLiveProvider()") == 1
    assert adapter.count("createCollectionController({") == 1
    assert 'renderCanonicalCard(model' in adapter
    assert "window.PantheonCockpitGraph" in adapter
    assert "currentGraph.children.get(entityId)" in adapter
    assert "currentGraph.cards.get(id)" in adapter
    assert "canExpandCollection({ width: stageWidth(), count: children.length })" in adapter
    assert "new window.Swiper" not in adapter
    assert "createNavigationState" not in adapter


def test_expansion_is_presentation_state_not_navigation_or_persistence_state():
    adapter = _read("live_collection_adapter.js")

    assert "let expandedEntityId = null;" in adapter
    assert 'stage.dataset.collectionExpanded = "true"' in adapter
    assert "expandedEntityId = model.entity_id" in adapter
    assert "state.children" not in adapter
    assert "fetch(" not in adapter


def test_expanded_selection_dims_siblings_and_hover_only_previews_the_back_on_pointer_devices():
    css = _read("styles/cockpit.css")

    assert '[data-collection-expanded="true"] .v3-expanded-cell[data-active="false"]' in css
    assert "opacity: .52;" in css
    assert "filter: saturate(.72);" in css
    assert "@media (hover: hover) and (pointer: fine)" in css
    assert '.card:not([data-flipped="true"]):hover .card-front' in css
    assert '.card:not([data-flipped="true"]):hover .card-back' in css


def test_compact_swipe_remains_windowed_while_expanded_layout_materializes_only_bounded_siblings():
    motion = _read("collection/motion_adapter.js")

    assert "addSlidesBefore: 1" in motion
    assert "addSlidesAfter: 1" in motion
    assert "cache: false" in motion
    assert "items > EXPANDED_MAX_ITEMS" in motion
    assert 'grid.className = "v3-expanded-grid"' in motion
    assert "for (let position = 0; position < count; position += 1)" in motion
