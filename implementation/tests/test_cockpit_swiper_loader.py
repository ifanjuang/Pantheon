from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
LOADER = COCKPIT / "navigation" / "swiper_loader.js"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"
MOTION = COCKPIT / "collection" / "motion_adapter.js"


def test_swiper_acquisition_is_isolated_from_live_bootstrap() -> None:
    loader = LOADER.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assert 'const SWIPER_VERSION = "14.0.7"' in loader
    assert "cdn.jsdelivr.net/npm/swiper" in loader
    assert "unpkg.com/swiper" in loader
    assert "export async function ensureSwiper" in loader
    assert 'import("./navigation/swiper_loader.js")' in bootstrap
    assert "await ensureSwiper()" in bootstrap
    for acquisition_detail in ("cdn.jsdelivr.net/npm/swiper", "unpkg.com/swiper", "SWIPER_VERSION", "loadExternalScript"):
        assert acquisition_detail not in bootstrap


def test_swiper_loader_acquires_library_but_never_constructs_navigation() -> None:
    loader = LOADER.read_text(encoding="utf-8")
    motion = MOTION.read_text(encoding="utf-8")
    assert "new window.Swiper" not in loader
    assert "new Swiper" not in loader
    assert "slideNext(" not in loader
    assert "slidePrev(" not in loader
    assert "new window.Swiper" in motion or "new Swiper" in motion


def test_swiper_loader_javascript_parses() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable")
    result = subprocess.run([node, "--check", str(LOADER)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_swiper_is_loaded_under_subresource_integrity() -> None:
    """Third-party executable code arrives pinned by content, not just by name.

    A version pin names what we asked for; SRI is what refuses anything else.
    Both CDN candidates mirror the same npm tarball, so one hash covers both.
    """
    loader = LOADER.read_text(encoding="utf-8")
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")

    assert "script.integrity = SWIPER_SCRIPT_SRI" in loader
    assert "script.crossOrigin" in loader, "SRI is enforced only on a CORS request"
    assert 'integrity="sha384-' in html
    assert 'crossorigin="anonymous"' in html


def test_every_pinned_swiper_asset_declares_an_integrity_hash() -> None:
    """A version bump that forgets a hash must fail here, not in a browser."""
    import re

    loader = LOADER.read_text(encoding="utf-8")
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")

    version = re.search(r'const SWIPER_VERSION = "([^"]+)"', loader).group(1)
    hashes = re.findall(r"sha384-[A-Za-z0-9+/=]{40,}", loader + html)
    assert len(hashes) >= 2, "expected an integrity hash for both the script and the stylesheet"

    # Every swiper URL we ship names the pinned version, so a bump cannot leave a
    # stale asset behind a fresh hash.
    for url in re.findall(r"https://[^\s\"'`]*swiper[^\s\"'`]*", loader + html):
        if "swiper@" in url or "swiper-bundle" in url:
            assert version in url or "${SWIPER_VERSION}" in url, url
