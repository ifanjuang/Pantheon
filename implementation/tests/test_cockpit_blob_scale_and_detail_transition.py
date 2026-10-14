from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_blob_scale_changes_decoration_not_card_dimensions() -> None:
    cards = (COCKPIT / "styles" / "cards.css").read_text(encoding="utf-8")
    families = (COCKPIT / "styles" / "families.css").read_text(encoding="utf-8")

    assert ".card,\n  .card-preview" in cards
    assert "width: 100%;" in cards
    assert "height: 100%;" in cards
    assert "--effect-1-width: 50%;" in families
    assert "--effect-2-width: 50%;" in families
    assert "--effect-3-width: 50%;" in families
    assert "--effect-1-height: 50%;" in families
    assert "--effect-2-height: 50%;" in families
    assert "--effect-3-height: 50%;" in families


def test_shared_blobs_keep_a_fixed_center_and_opposite_rotations() -> None:
    cards = (COCKPIT / "styles" / "cards.css").read_text(encoding="utf-8")
    families = (COCKPIT / "styles" / "families.css").read_text(encoding="utf-8")

    assert "top: 50%;" in cards
    assert "left: 50%;" in cards
    assert "--effect-1-top: 50%;" in families
    assert "--effect-2-top: 50%;" in families
    assert "--effect-3-top: 50%;" in families
    assert "card-blob-rotate-forward" in cards
    assert "card-blob-rotate-reverse" in cards
    assert "--effect-1-top: 47%" not in cards
    assert "--effect-3-left: 43%" not in cards


def test_affaires_pack_uses_opaque_yellow_blobs_on_white() -> None:
    families = (COCKPIT / "styles" / "families.css").read_text(encoding="utf-8")
    affaires = families.split('[data-family="affaires"] {', 1)[1].split("}", 1)[0]

    assert "--card-front-background: #fff;" in affaires
    assert "--effects-opacity: 1;" in affaires
    for index in (1, 2, 3):
        assert f"--effect-{index}-fill: var(--pantheon-yellow);" in affaires
    assert "mix-blend-mode: normal;" in families


def test_card_details_replace_content_without_horizontal_rotation() -> None:
    cards = (COCKPIT / "styles" / "cards.css").read_text(encoding="utf-8")

    assert 'card[data-flipped="true"] .card-back' in cards
    assert "opacity: 1;" in cards
    assert "visibility: visible;" in cards
    assert "rotateY(180deg)" not in cards
    assert "perspective:" not in cards
