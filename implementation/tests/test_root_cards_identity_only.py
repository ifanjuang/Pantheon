from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT_PROJECTION = ROOT / "mvp_vertical" / "cockpit" / "projection" / "cockpit_projection.js"


def root_cards_block() -> str:
    source = COCKPIT_PROJECTION.read_text(encoding="utf-8")
    start = source.index("function rootCards()")
    end = source.index("function projectEntityId", start)
    return source[start:end]


def test_root_cards_derive_stable_identity_inputs_from_navigation_registry() -> None:
    block = root_cards_block()
    expected = (
        "navigationProjection.rootItemIds.map",
        "entity_id: entityId",
        'entity_type: "cockpit_space"',
    )
    assert all(entry in block for entry in expected)
    assert block.count('entity_type: "cockpit_space"') == 1
    for root_id in (
        "space:pantheon",
        "space:affaires",
        "space:connaissances",
        "space:outils",
        "space:decisions",
    ):
        assert root_id not in block


def test_root_cards_do_not_duplicate_projection_metadata() -> None:
    block = root_cards_block()
    forbidden = (
        "role:",
        "family:",
        "presentation_family:",
        "category:",
        "title:",
        "summary:",
        "status:",
        "back:",
        "available_actions:",
        "type_tags:",
        "subject_tags:",
        "limits:",
    )
    assert all(token not in block for token in forbidden)
