"""Regression guards for compact vertical level navigation in the Cockpit."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
MOTION = COCKPIT / "collection" / "motion_adapter.js"
CONTROLLER = COCKPIT / "collection" / "collection_controller.js"
LIVE_ADAPTER = COCKPIT / "live_collection_adapter.js"


def _run_module(body: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - runner dependent
        pytest.skip("Node.js is unavailable; vertical swipe behavior check skipped")
    return subprocess.run(
        [node, "--input-type=module", "-e", body],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_compact_vertical_navigation_uses_one_bounded_deck_swiper() -> None:
    result = _run_module(
        f"""
        import {{ createDeckMotion }} from {json.dumps(MOTION.as_uri())};

        class FakeElement {{
          constructor() {{
            this.children = [];
            this.className = "";
            this.dataset = {{}};
            this.classList = {{ add() {{}} }};
          }}
          append(...nodes) {{ this.children.push(...nodes); }}
          setAttribute() {{}}
          remove() {{}}
          querySelector(selector) {{
            if (selector === ".swiper-wrapper") return this.children[0] || null;
            return null;
          }}
        }}

        let swiper = null;
        let callbacks = null;
        let optionsSeen = null;
        class FakeSwiper {{
          constructor(_shell, options) {{
            optionsSeen = options;
            callbacks = options.on;
            swiper = this;
            this.activeIndex = options.initialSlide || 0;
            this.animating = false;
            this.allowSlidePrev = true;
            this.allowSlideNext = true;
            this.allowTouchMove = true;
          }}
          slideTo(index) {{ this.activeIndex = index; }}
          slidePrev() {{ this.activeIndex = Math.max(0, this.activeIndex - 1); }}
          slideNext() {{ this.activeIndex += 1; }}
          destroy() {{}}
        }}

        globalThis.document = {{ createElement() {{ return new FakeElement(); }} }};
        globalThis.window = {{ Swiper: FakeSwiper }};

        const mount = new FakeElement();
        const settled = [];
        const moving = [];
        const deck = createDeckMotion({{
          mount,
          hosts: 3,
          initial: 1,
          onSettled(index) {{ settled.push(index); }},
          onMoveState(value) {{ moving.push(value); }},
        }});

        if (optionsSeen.direction !== "vertical") throw new Error("deck must be vertical");
        if (optionsSeen.initialSlide !== 1 || deck.index !== 1) throw new Error("middle level must be active");
        if (!deck.hostAt(0) || !deck.hostAt(1) || !deck.hostAt(2) || deck.hostAt(3) !== null) {{
          throw new Error("deck must expose exactly three bounded hosts");
        }}

        deck.setBounds({{ previous: false, next: true }});
        if (swiper.allowSlidePrev !== false || swiper.allowSlideNext !== true) {{
          throw new Error("deck bounds were not applied");
        }}

        callbacks.touchStart(swiper);
        callbacks.sliderMove(swiper);
        callbacks.touchEnd(swiper);
        swiper.activeIndex = 2;
        callbacks.slideChangeTransitionEnd(swiper);

        if (JSON.stringify(settled) !== JSON.stringify([2])) throw new Error("settled level not emitted");
        if (moving[0] !== true || moving.at(-1) !== false) throw new Error("move state not bounded");
        """
    )
    assert result.returncode == 0, result.stderr


def test_vertical_swipe_reuses_projection_commands_without_custom_cross_axis_recognizer() -> None:
    motion = MOTION.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    adapter = LIVE_ADAPTER.read_text(encoding="utf-8")

    assert "onCrossAxisMove" not in motion
    assert "touchMoveOpposite" not in motion
    assert "onCrossAxisMove" not in controller

    assert "createDeckMotion({" in adapter
    assert "onSettled: handleLevelSettled" in adapter
    assert 'index < 1 ? "v2-ascend" : "v2-descend"' in adapter
    assert "control.click()" in adapter
    assert "PantheonSpatialNavigation" not in adapter
    assert ".descend(" not in adapter
    assert ".ascend(" not in adapter


def test_demo_and_live_share_the_same_vertical_swipe_adapter() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    demo = (COCKPIT / "demo_bootstrap.js").read_text(encoding="utf-8")

    assert 'if (isDemo) await import("./demo_bootstrap.js")' in bootstrap
    assert 'await import("./live_collection_adapter.js")' in bootstrap
    assert "live_collection_adapter" not in demo
    assert "createDeckMotion" not in demo
