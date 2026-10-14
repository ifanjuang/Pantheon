from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_claim_is_not_added_as_cockpit_family() -> None:
    structured = (ROOT / "mvp_vertical" / "cockpit" / "structured_interface.js").read_text(encoding="utf-8")
    renderer = (ROOT / "mvp_vertical" / "cockpit" / "projection" / "cockpit_projection.js").read_text(encoding="utf-8")
    assert '"claim"' not in structured.split("CARD_FAMILIES", 1)[1].split("}", 1)[0]
    assert 'claim: "' not in renderer
