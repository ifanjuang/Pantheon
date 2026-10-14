from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_live_collection_does_not_invoke_the_historical_dom_renderer_for_flip_state() -> None:
    adapter = _text(COCKPIT / "live_collection_adapter.js")

    assert "projectLegacyState" not in adapter
    assert "legacyProjection" not in adapter
    assert "renderCard(model)" not in adapter
    assert "view_state" in adapter
    assert "flippedByEntity" in adapter
    assert 'renderCanonicalCard(model, { flipped: model?.view_state?.flipped === true })' in adapter


def test_card_flip_is_published_as_view_state_with_stable_entity_identity() -> None:
    interactions = _text(COCKPIT / "interactions" / "card_interactions.js")

    assert 'new CustomEvent("pantheon:card-flip"' in interactions
    assert "cardEntityId(card)" in interactions
    assert 'querySelector(".card-entity-id")' in interactions
    assert "entity_id: cardEntityId(card)" in interactions
    assert "flipped: next" in interactions


def test_flip_state_remains_projection_not_authorization() -> None:
    adapter = _text(COCKPIT / "live_collection_adapter.js")
    interactions = _text(COCKPIT / "interactions" / "card_interactions.js")

    for forbidden in ("/validate", "/approve", "/apply", "Authorization", "ChangeCandidate"):
        assert forbidden not in adapter
        assert forbidden not in interactions
