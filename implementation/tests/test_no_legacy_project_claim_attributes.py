import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "mvp_vertical" / "agency_schema" / "project.json"


LEGACY = {
    "budget",
    "surface_terrain",
    "surface_existante",
    "surface_projet",
    "emprise",
    "parcelles",
    "plu_zone",
    "permit_number",
    "permit_date",
    "reception_date",
    "erp_type",
}


def test_legacy_consequential_fields_never_return_to_attributes_storage() -> None:
    registry = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fields = {field["key"]: field for field in registry["fields"]}
    assert all(fields[key]["storage"] == "projection" for key in LEGACY)
    assert all(fields[key]["semantics"] == "claim" for key in LEGACY)

    editable = set(registry["views"]["edit"]["fields"])
    assert editable.isdisjoint(LEGACY)
