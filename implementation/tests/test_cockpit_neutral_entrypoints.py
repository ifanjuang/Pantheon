from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_canonical_page_uses_responsibility_named_entrypoint() -> None:
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")
    assert 'src="cockpit_bootstrap.js"' in html
    assert 'src="v3_bootstrap.js"' not in html


def test_neutral_entrypoint_chain_is_complete() -> None:
    cockpit = (COCKPIT / "cockpit_bootstrap.js").read_text(encoding="utf-8")
    live = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    assert 'import("./live_bootstrap.js")' in cockpit
    assert 'import("./live_collection_adapter.js")' in live
    # shell_controls.js is loaded once, by the classic script chain that
    # live_bootstrap.js owns, so demo and live cannot diverge on it.
    assert "shell_controls.js" not in cockpit
    assert '"shell_controls.js"' in live


def test_single_boot_chain_serves_both_modes() -> None:
    """Demo is a fixture substitution, never a second application."""
    cockpit = (COCKPIT / "cockpit_bootstrap.js").read_text(encoding="utf-8")
    live = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")

    # The entrypoint must not branch on the mode: one import, both modes.
    assert cockpit.count('import("./') == 1
    assert "URLSearchParams" not in cockpit
    assert "cockpitMode" not in cockpit

    # live_bootstrap.js is the single place that reads and publishes the mode.
    assert 'params.get("mode") === "demo"' in live
    assert 'import("./demo_bootstrap.js")' in live


def test_generation_named_entrypoint_files_are_retired() -> None:
    for filename in ("v3_bootstrap.js", "v2_bootstrap.js", "v3_swiper.js", "v2_shell_controls.js"):
        assert not (COCKPIT / filename).exists(), filename
