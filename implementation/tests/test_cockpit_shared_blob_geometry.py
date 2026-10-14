from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "mvp_vertical" / "cockpit" / "styles"


def test_pantheon_affaires_pack_and_project_booster_share_one_geometry() -> None:
    cards = (STYLES / "cards.css").read_text(encoding="utf-8")
    families = (STYLES / "families.css").read_text(encoding="utf-8")
    for index in (1, 2, 3):
        assert f"--effect-width: var(--effect-{index}-width, 50%)" in cards
        assert f"--effect-height: var(--effect-{index}-height, 50%)" in cards
        assert f"--effect-{index}-width: 50%" in families
        assert f"--effect-{index}-height: 50%" in families
        assert f"--effect-{index}-top: 50%" in families
        assert f"--effect-{index}-left: 50%" in families

    # Inspect only the dedicated Project visual block, not the earlier shared
    # geometry selector which intentionally includes [data-kind="project"].
    project = families.rsplit('[data-kind="project"] {', 1)[1].split('[data-kind="work"]', 1)[0]
    for legacy_override in ("--effect-2-top:", "--effect-2-left:", "--effect-3-top:", "--effect-3-left:"):
        assert legacy_override not in project


def test_shared_blobs_rotate_in_opposite_directions_with_stable_fast_variation() -> None:
    cards = (STYLES / "cards.css").read_text(encoding="utf-8")
    assert "card-blob-rotate-forward" in cards
    assert "card-blob-rotate-reverse" in cards
    assert "+ 360deg" in cards
    assert "- 360deg" in cards
    for variant in ("1", "2", "3"):
        assert f'.card[data-variant="{variant}"]' in cards
        assert f'.card-preview[data-variant="{variant}"]' in cards
    for duration in ("1.1s", "1.2s", "1.4s", "1.5s", "1.6s", "1.8s", "1.9s"):
        assert duration in cards
    assert "prefers-reduced-motion" not in cards
    assert "animation: none !important" not in cards
