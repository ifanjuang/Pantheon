"""Architecture budgets for the cockpit navigation core.

These are static guards, not runtime measurements: they pin the contracts so a
later edit cannot quietly reintroduce a Swiper-shaped cockpit or mount a whole
collection into the DOM again.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
ADAPTER = "collection/motion_adapter.js"
COLLECTION_PROVIDER = COCKPIT / "collection" / "collection_provider.js"

SWIPER_FREE = (
    "collection/navigation_state.js",
    "collection/collection_provider.js",
    "collection/collection_controller.js",
    "rendering/card_renderer.js",
    "providers/live_provider.js",
    "demo_bootstrap.js",
)


def _read(rel: str) -> str:
    return (COCKPIT / rel).read_text(encoding="utf-8")


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


def test_swiper_is_confined_to_the_motion_adapter() -> None:
    adapter = _read(ADAPTER)
    assert "new window.Swiper" in adapter
    for rel in SWIPER_FREE:
        source = _read(rel)
        assert "new window.Swiper" not in source, rel
        assert "new Swiper(" not in source, rel


def test_cockpit_never_drives_swiper_slide_apis_directly() -> None:
    for rel in SWIPER_FREE + ("live_collection_adapter.js",):
        source = _read(rel)
        for forbidden in (
            "appendSlide",
            "removeAllSlides",
            "updateSlides",
            "slideTo(",
            "slidePrev(",
            "slideNext(",
        ):
            assert forbidden not in source, f"{rel} calls {forbidden}"


def test_mounted_window_is_bounded_independently_of_collection_size() -> None:
    adapter = _read(ADAPTER)
    assert "virtual" in adapter
    assert "addSlidesBefore: 1" in adapter
    assert "addSlidesAfter: 1" in adapter
    assert "cache: false" in adapter


def test_resident_arrays_are_not_fake_streamed() -> None:
    provider = _read("collection/collection_provider.js")
    assert "isAsyncIterable" in provider
    assert "Symbol.asyncIterator" in provider
    assert "requestAnimationFrame" not in provider


def test_superseded_async_load_cannot_pollute_replacement_collection() -> None:
    result = _run_module(
        f"""
        import {{ loadCollection }} from {json.dumps(COLLECTION_PROVIDER.as_uri())};
        const model = {{ collectionId: null, items: [], loading: false }};
        const state = {{
          setCollection(next) {{ model.collectionId = next.collectionId; model.items = [...next.items]; model.loading = next.loading; }},
          appendItems(items) {{ model.items.push(...items); }},
          setLoading(value) {{ model.loading = value; }},
        }};
        async function* staleStream() {{
          yield {{ id: "stale-first" }};
          await new Promise(resolve => setTimeout(resolve, 25));
          yield {{ id: "stale-late" }};
        }}
        const cancel = loadCollection(state, {{ spaceId: "agency", id: "stale" }}, staleStream(), 0);
        await new Promise(resolve => setTimeout(resolve, 5));
        cancel();
        loadCollection(state, {{ spaceId: "agency", id: "current" }}, [{{ id: "current-only" }}], 0);
        await new Promise(resolve => setTimeout(resolve, 50));
        if (model.collectionId !== "current") throw new Error("stale collection replaced the current identity");
        if (model.loading) throw new Error("cancelled stream changed the current loading state");
        if (model.items.length !== 1 || model.items[0].id !== "current-only") {{
          throw new Error(`stale stream polluted replacement collection: ${{JSON.stringify(model.items)}}`);
        }}
        """
    )
    assert result.returncode == 0, result.stderr


def test_create_affordance_is_a_real_button_excluded_from_swiping() -> None:
    """The live create card is a real button, and the motion adapter — not the
    renderer — is what keeps a gesture on it from becoming a slide change.

    The retired demo island used the opposite convention (a div carrying
    role="button" so it stayed swipeable). The live path deliberately reversed
    it, so the invariant now lives in noSwipingSelector.
    """
    create = _read("information_create.js")
    adapter = _read(ADAPTER)

    assert 'createElement("button")' in create
    assert 'button.type = "button"' in create
    assert "swiper-no-swiping" not in create

    selector_line = next(
        line
        for line in adapter.splitlines()
        if "noSwipingSelector:" in line and not line.lstrip().startswith("//")
    )
    assert "button" in selector_line


def test_demo_html_targets_the_single_cockpit_page() -> None:
    demo_html = _read("demo.html")
    assert "index.html?mode=demo" in demo_html
    assert "v2.html?mode=demo" not in demo_html


def test_canonical_shell_is_the_single_backdrop_authority() -> None:
    cockpit_css = _read("styles/cockpit.css")
    cards_css = _read("styles/cards.css")
    families_css = _read("styles/families.css")
    assert ".v3-body {" in cockpit_css
    assert "background: var(--cockpit-bg);" in cockpit_css
    assert ".v3-body {" not in cards_css
    assert ".v3-body {" not in families_css
