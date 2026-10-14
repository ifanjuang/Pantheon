import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "mvp_vertical" / "cockpit" / "tool_catalog.json"


def _catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_tool_catalog_preserves_independent_governance_axes():
    catalog = _catalog()
    assert catalog["catalog_version"] == 2
    assert catalog["authority"]["catalogue_is_authority"] is False

    for item in catalog["items"]:
        assert item["tool_id"]
        assert item["capability_slots"]
        assert item["installation_state"]
        assert item["native_state"]
        assert item["health_state"]
        assert item["governance_state"]
        assert item["update_state"]
        assert item["activation_state"]
        assert isinstance(item["permissions"], dict)
        assert item["evidence_expectation"]
        assert item["rollback_posture"]
        assert "next_human_decision" in item


def test_retrieval_frameworks_are_catalogue_candidates_only():
    items = {item["tool_id"]: item for item in _catalog()["items"]}
    assert items["haystack"]["binding_role"] == "candidate"
    assert items["llamaindex"]["binding_role"] == "watch"
    assert items["langchain"]["binding_role"] == "watch"
    assert all(items[name]["installation_state"] == "listed" for name in ("haystack", "llamaindex", "langchain"))
    assert all(items[name]["activation_state"] == "not_activated" for name in ("haystack", "llamaindex", "langchain"))


def test_catalog_does_not_encode_automatic_authorization():
    serialized = CATALOG.read_text(encoding="utf-8").lower()
    assert '"approved"' not in serialized
    assert '"activated"' not in serialized
    assert "automatic binding adoption" in serialized
