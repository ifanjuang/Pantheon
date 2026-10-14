from pathlib import Path

from mvp_vertical import agency_schema


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "mvp_vertical" / "agency_data_api.py"


def test_information_list_exposes_one_server_owned_card_contract() -> None:
    source = API.read_text(encoding="utf-8")

    assert '"card_contract": {' in source
    assert '"authorization_inferred": False' in source
    assert 'agency_schema.get_information_schema("cockpit_front")' in source
    assert 'agency_schema.get_information_schema("cockpit_back")' in source


def test_information_card_views_are_distinct_and_ordered() -> None:
    front = agency_schema.get_information_schema("cockpit_front")
    back = agency_schema.get_information_schema("cockpit_back")

    assert front["resolved_view"]["name"] == "cockpit_front"
    assert back["resolved_view"]["name"] == "cockpit_back"
    assert [field["key"] for field in front["fields"]] == front["views"]["cockpit_front"]["fields"]
    assert [field["key"] for field in back["fields"]] == back["views"]["cockpit_back"]["fields"]
    assert "details" not in [field["key"] for field in front["fields"]]
    assert "details" in [field["key"] for field in back["fields"]]
