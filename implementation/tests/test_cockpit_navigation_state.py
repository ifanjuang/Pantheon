"""Behavior contract for the cockpit NavigationState.

NavigationState is pure data — no DOM, no Swiper — so it is exercised for real
here rather than asserted as text. This is the contract every presentation
(mobile deck, scroll-snap, grid, desktop master/detail) has to satisfy.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "mvp_vertical" / "cockpit" / "collection" / "navigation_state.js"


def _run_module(body: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; JavaScript behavior check skipped")
    source = STATE.read_text(encoding="utf-8") + "\n" + body
    return subprocess.run(
        [node, "--input-type=module", "-e", source],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_navigation_state_tracks_identity_bounds_and_face() -> None:
    result = _run_module(
        """
        const state = createNavigationState({ spaceId: "affaires" });
        state.setCollection({ collectionId: "projects", items: [{id:"a"},{id:"b"},{id:"c"}], index: 1 });
        if (state.snapshot().activeEntityId !== "b") throw new Error("active entity identity lost");
        if (state.snapshot().itemCount !== 3) throw new Error("collection is not held as data");
        state.move(1);
        if (state.snapshot().activeEntityId !== "c") throw new Error("move failed");
        if (state.snapshot().canNext) throw new Error("upper bound not reported");
        state.move(1);
        if (state.snapshot().activeEntityId !== "c") throw new Error("index was not clamped");
        state.flip();
        if (state.snapshot().face !== "back") throw new Error("flip failed");
        state.setIndex(0);
        if (state.snapshot().face !== "front") throw new Error("face must reset when the card changes");
        """
    )
    assert result.returncode == 0, result.stderr


def test_navigation_state_supports_progressive_arrival_and_subscription() -> None:
    result = _run_module(
        """
        const state = createNavigationState();
        state.setCollection({ collectionId: "async", items: [], index: 0, loading: true });
        if (state.snapshot().activeIndex !== -1) throw new Error("empty collection must have no active index");
        let notified = 0;
        state.subscribe(() => { notified += 1; });
        state.appendItems([{ id: "first" }]);
        if (state.snapshot().activeEntityId !== "first") throw new Error("first arrival must become active");
        state.appendItems([{ id: "second" }]);
        if (state.snapshot().itemCount !== 2) throw new Error("progressive append failed");
        if (state.snapshot().activeEntityId !== "first") throw new Error("later arrivals must not steal focus");
        state.setLoading(false);
        if (state.snapshot().loading) throw new Error("loading flag stuck");
        if (notified !== 3) throw new Error("subscribers must observe every transition");
        """
    )
    assert result.returncode == 0, result.stderr


def test_navigation_state_is_free_of_dom_and_swiper() -> None:
    code = "\n".join(
        line for line in STATE.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("//")
    )
    for forbidden in ("document", "window.", "Swiper", "swiper", "appendSlide"):
        assert forbidden not in code, forbidden
