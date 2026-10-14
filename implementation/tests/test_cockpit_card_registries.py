import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "mvp_vertical" / "cockpit" / "registries"
REQUIRED_TAG_KEYS = {
    "slug",
    "group",
    "title",
    "description",
    "hermes_context",
    "aliases",
    "applies_to",
    "presentation",
}
REQUIRED_PRESENTATION_KEYS = {"icon_provider", "icon_key", "color"}


def _load(name: str) -> dict:
    return json.loads((REGISTRY_DIR / name).read_text(encoding="utf-8"))


def _tag_registry() -> dict:
    return _load("tag_registry.json")


def _slugs(payload: dict, group: str) -> set[str]:
    return {item["slug"] for item in payload["tags"] if item["group"] == group}


def test_type_and_subject_tag_groups_are_explicit_and_contextual() -> None:
    payload = _tag_registry()
    groups = {item["id"]: item for item in payload["groups"]}

    assert payload["schema_id"] == "cockpit.tag_registry"
    assert payload["revision"] == 1
    assert {"type", "subject"} <= groups.keys()
    assert groups["subject"]["max_per_card"] == 5
    assert groups["type"]["description"].strip()
    assert groups["subject"]["description"].strip()
    assert groups["type"]["hermes_context_role"].strip()
    assert groups["subject"]["hermes_context_role"].strip()

    identities = [(item["group"], item["slug"]) for item in payload["tags"]]
    assert len(identities) == len(set(identities))
    assert _slugs(payload, "type")
    assert _slugs(payload, "subject")


def test_tag_registry_entries_have_complete_context_and_presentation_metadata() -> None:
    icon_css = (ROOT / "mvp_vertical" / "cockpit" / "styles" / "cards.css").read_text(encoding="utf-8")
    radix_keys = set(re.findall(r'\.radix-icon\[data-icon="([^"]+)"\]', icon_css))
    payload = _tag_registry()
    assert payload["tags"]

    identities = set()
    for item in payload["tags"]:
        identity = (item["group"], item["slug"])
        assert identity not in identities
        identities.add(identity)

        missing = REQUIRED_TAG_KEYS - item.keys()
        assert not missing, f"{identity} missing {sorted(missing)}"
        assert item["group"] in {"type", "subject"}
        assert item["title"].strip()
        assert item["description"].strip()
        assert item["hermes_context"].strip()
        assert isinstance(item["aliases"], list)
        assert isinstance(item["applies_to"], list)

        presentation = item["presentation"]
        presentation_missing = REQUIRED_PRESENTATION_KEYS - presentation.keys()
        assert not presentation_missing, f"{identity} presentation missing {sorted(presentation_missing)}"
        assert all(str(presentation[key]).strip() for key in REQUIRED_PRESENTATION_KEYS)
        assert presentation["icon_provider"] in {"radix", "material-symbols"}
        if presentation["icon_provider"] == "radix":
            assert presentation["icon_key"] in radix_keys, f"{identity} references an unvendored Radix icon"
        else:
            assert re.fullmatch(r"[a-z0-9_]+", presentation["icon_key"])


def test_every_rendered_tag_has_an_icon_including_unknown_tags() -> None:
    renderer = (ROOT / "mvp_vertical" / "cockpit" / "rendering" / "card_renderer.js").read_text(encoding="utf-8")
    tag_icons = (ROOT / "mvp_vertical" / "cockpit" / "rendering" / "tag_icons.js").read_text(encoding="utf-8")
    index = (ROOT / "mvp_vertical" / "cockpit" / "index.html").read_text(encoding="utf-8")

    assert 'import { createTagToken } from "./tag_icons.js"' in renderer
    assert 'icon_key: "label"' in tag_icons
    assert "styles/cards.css" in index
    assert "Material+Symbols+Rounded" in index


def test_dce_is_a_type_tag_not_a_subject_tag() -> None:
    payload = _tag_registry()

    assert "dce" in _slugs(payload, "type")
    assert "dce" not in _slugs(payload, "subject")


def test_status_and_limit_registries_remain_separate_from_tags() -> None:
    payload = _tag_registry()
    classification_slugs = _slugs(payload, "type") | _slugs(payload, "subject")

    for filename in ("status_registry.json", "limit_registry.json"):
        registry = _load(filename)
        values = registry["values"]
        assert values
        for item in values:
            assert {"slug", "title", "icon_key", "color"} <= item.keys()
            assert item["slug"] not in classification_slugs


def test_split_tag_registries_are_retired() -> None:
    assert not (REGISTRY_DIR / "type_tags.json").exists()
    assert not (REGISTRY_DIR / "subject_tags.json").exists()
