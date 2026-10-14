from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def _text(name: str) -> str:
    return (COCKPIT / name).read_text(encoding="utf-8")


def test_action_modules_use_canonical_contract_with_bounded_fallback() -> None:
    actions = _text("actions/card_actions.js")
    candidates = _text("actions/change_candidate_actions.js")

    for selector in (".card", ".card-title", ".card-entity-id", ".card-actions"):
        assert selector in actions

    assert "button[data-card-action]" in actions
    assert "button[data-card-action]" in candidates
    assert "dataset.cardAction" in actions
    assert "dataset.cardAction" in candidates
    assert "data-v2-action" not in actions
    assert "data-v2-action" not in candidates

    # The fallback renderer is still active when Swiper is unavailable. Legacy
    # selectors may only appear inside the explicit :is() compatibility seam.
    assert ':is(.card, .v2-card)' in actions
    assert ':is(.card-actions, .v2-card-actions) button' in actions
    assert ':is(.card-entity-id, .v2-entity-id)' in actions
    assert ':is(.card-title, .v2-card-title)' in actions


def test_interaction_policy_locks_canonical_and_fallback_cards() -> None:
    policy = _text("interactions/interaction_policy.js")
    assert 'querySelector(":is(.card, .v2-card)")' in policy
    assert 'attributeFilter: ["data-flipped"]' in policy


def test_generation_named_action_modules_are_removed() -> None:
    for retired in ("v2_actions.js", "v2_candidate_actions.js", "v2_interaction_policy.js"):
        assert not (COCKPIT / retired).exists()
