from hashlib import sha256

from mvp_vertical import pantheon_contracts


def test_project_claim_schema_is_canonical_and_bounded() -> None:
    schema = pantheon_contracts.load_schema("project_claim")
    provenance = pantheon_contracts.provenance("project_claim")

    assert schema["title"] == "Pantheon Next Project Claim"
    assert schema["x-boundary"]["system_of_record_mutation"] is False
    assert "backing_ref" in schema["properties"]
    assert provenance["source_path"] == "schemas/project_claim.schema.yaml"
    assert provenance["posture"] == "canonical-repository"
    assert provenance["authority_transfer"] is False
    assert provenance["sha256"] == sha256(
        pantheon_contracts.schema_path("project_claim").read_bytes()
    ).hexdigest()


def test_project_claim_uses_shared_contract_registry_without_special_pin() -> None:
    assert pantheon_contracts.CONTRACT_PATHS["project_claim"] == "schemas/project_claim.schema.yaml"
