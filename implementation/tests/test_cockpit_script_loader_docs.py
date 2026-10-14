from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "cockpit" / "CLASSIC_SCRIPT_LOADING.md"


def test_classic_script_loading_boundary_is_documented() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "boot/classic_script_loader.js" in text
    assert "live_bootstrap.js" in text
    assert "navigation/swiper_loader.js" in text
    assert "v3/collection/motion_adapter.js" in text
    assert "script loaded != module approved" in text
