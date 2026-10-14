from mvp_vertical import agency_schema


def test_declared_claim_types_are_unique_and_not_attributes() -> None:
    registry = agency_schema.get_project_registry()
    claim_fields = [field for field in registry["fields"] if field.get("storage") == "projection"]
    claim_types = [field["claim_type"] for field in claim_fields]
    assert len(claim_types) == len(set(claim_types))
    assert all(field.get("semantics") == "claim" for field in claim_fields)
    assert all(field.get("mutable") is False for field in claim_fields)
