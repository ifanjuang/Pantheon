from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"
LOADER = COCKPIT / "boot" / "classic_script_loader.js"


def test_live_bootstrap_delegates_ordered_classic_script_loading() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    assert 'import("./boot/classic_script_loader.js")' in bootstrap
    assert "loadClassicScriptsInOrder(scripts)" in bootstrap
    assert 'document.createElement("script")' not in bootstrap
    assert "script.onload" not in bootstrap
    assert "script.onerror" not in bootstrap


def test_classic_script_loader_has_a_bounded_non_domain_role() -> None:
    source = LOADER.read_text(encoding="utf-8")

    assert "export function loadClassicScript" in source
    assert "export async function loadClassicScriptsInOrder" in source
    assert 'document.createElement("script")' in source
    assert "for (const src of sources) await loadClassicScript" in source

    forbidden = (
        "fetch(",
        "Hermes",
        "hermes",
        "ChangeCandidate",
        "Evidence",
        "authorization",
        "admission",
        "dispatch",
        "Swiper",
    )
    for token in forbidden:
        assert token not in source


def test_bootstrap_and_classic_script_loader_parse_in_node() -> None:
    for path in (BOOTSTRAP, LOADER):
        subprocess.run(["node", "--check", str(path)], check=True, capture_output=True, text=True)
