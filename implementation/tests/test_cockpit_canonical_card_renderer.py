from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
RENDERER = COCKPIT / "rendering" / "card_renderer.js"


def test_canonical_renderer_javascript_parses() -> None:
    node = shutil.which("node")
    if node is None:  # pragma: no cover
        pytest.skip("Node.js is unavailable; JavaScript syntax check skipped")
    result = subprocess.run(
        [node, "--check", str(RENDERER)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_canonical_renderer_owns_structural_axes_not_graphics() -> None:
    source = RENDERER.read_text(encoding="utf-8")

    for axis in ("dataset.family", "dataset.level", "dataset.kind", "dataset.status", "dataset.variant"):
        assert axis in source

    for structural_class in (
        '"card v2-card"',
        '"card-inner v2-card-inner"',
        '"card-face card-front',
        '"card-face card-back',
        '"card-body v2-card-body"',
        '"card-footer v2-card-footer"',
    ):
        assert structural_class in source

    for graphic_instruction in (
        "card-blob",
        "card-blobs",
        "borderRadius",
        "backgroundImage",
        "boxShadow",
    ):
        assert graphic_instruction not in source


def test_adapter_imports_renderer_and_does_not_own_swiper() -> None:
    adapter = (COCKPIT / "live_collection_adapter.js").read_text(encoding="utf-8")
    assert 'from "./rendering/card_renderer.js"' in adapter
    assert "new window.Swiper" not in adapter
    assert "new Swiper(" not in adapter
