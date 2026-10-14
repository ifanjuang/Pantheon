from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "mvp_vertical" / "sql" / "002_agency_data.sql").read_text(encoding="utf-8")


def test_project_claim_store_is_append_only_and_semantic() -> None:
    assert "CREATE TABLE IF NOT EXISTS agency_project_claims" in SQL
    assert "backing_entity_type" in SQL
    assert "backing_entity_id" in SQL
    assert "agency_project_claims are append-only" in SQL
    assert "BEFORE UPDATE ON agency_project_claims" in SQL
    assert "BEFORE DELETE ON agency_project_claims" in SQL


def test_legacy_consequential_project_attributes_are_removed_at_schema_init() -> None:
    assert "attributes = attributes - ARRAY[" in SQL
    for key in (
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
    ):
        assert f"'{key}'" in SQL
