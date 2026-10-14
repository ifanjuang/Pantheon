import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS_PATH = (
    ROOT
    / "mvp_vertical"
    / "cockpit"
    / "registries"
    / "card_projection_definitions.json"
)
NAVIGATION_PATH = (
    ROOT
    / "mvp_vertical"
    / "cockpit"
    / "registries"
    / "navigation_registry.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_root_card_projection_definitions_match_navigation_spaces() -> None:
    definitions = _load(DEFINITIONS_PATH)
    navigation = _load(NAVIGATION_PATH)

    definition_ids = [item["definition_id"] for item in definitions["definitions"]]
    entity_ids = [item["entity_id"] for item in definitions["definitions"]]
    navigation_ids = [item["id"] for item in navigation["root_collection"]["items"]]

    assert len(definition_ids) == len(set(definition_ids))
    assert len(entity_ids) == len(set(entity_ids))
    assert entity_ids == navigation_ids


def test_root_definitions_remain_projection_only() -> None:
    definitions = _load(DEFINITIONS_PATH)

    assert set(definitions["boundaries"].values()) == {False}
    assert all(item["children_source"] == "navigation_registry" for item in definitions["definitions"])
    assert all("actions" not in item for item in definitions["definitions"])
    assert all("permissions" not in item for item in definitions["definitions"])
    assert all("endpoint" not in item for item in definitions["definitions"])


def test_root_definition_presentation_vocabulary_is_bounded() -> None:
    definitions = _load(DEFINITIONS_PATH)
    allowed_roles = {"conversation", "container", "entity"}
    allowed_families = {"pantheon", "project", "information", "contact", "work", "decision", "tool"}

    assert all(item["card_role"] in allowed_roles for item in definitions["definitions"])
    assert all(item["presentation_family"] in allowed_families for item in definitions["definitions"])
