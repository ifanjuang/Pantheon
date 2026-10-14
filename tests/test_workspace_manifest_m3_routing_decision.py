from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = (
    ROOT
    / "docs"
    / "examples"
    / "workspace_manifest_inspector"
    / "qualification"
)
M2_FIXTURE = QUALIFICATION / "m2_document_information_routing.yaml"
M3_DECISION = QUALIFICATION / "m3_routing_decision.yaml"


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for nested in value.values():
            keys.update(_all_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for nested in value:
            keys.update(_all_keys(nested))
        return keys
    return set()


def test_m3_selects_calculated_routing_without_sidecar_schema_adoption() -> None:
    decision = _load(M3_DECISION)

    assert decision["decision_status"] == "repository_qualification"
    assert decision["issue"] == 859
    assert decision["tranche"] == "M3"
    assert (
        decision["classification"]
        == "routing_converged_without_production_sidecar_schema_change"
    )
    assert decision["observed"]["production_document_sidecar_schema_present"] is False
    assert decision["routing_decision"]["persistence"] == "none"
    assert decision["routing_decision"]["persisted_routing_fields"] == []
    assert (
        decision["routing_decision"]["resolution"]
        == "calculated_or_unresolved_at_use_time"
    )


def test_m2_fixture_does_not_accidentally_persist_m3_routing_fields() -> None:
    fixture = _load(M2_FIXTURE)
    decision = _load(M3_DECISION)
    keys = _all_keys(fixture)

    forbidden = set(
        decision["routing_decision"]["forbidden_new_sidecar_routing_fields"]
    )
    assert forbidden == {"profile_refs", "analysis_routes", "capabilities"}
    assert not forbidden.intersection(keys)


def test_profiles_and_bindings_remain_external_and_may_be_unresolved() -> None:
    decision = _load(M3_DECISION)
    inputs = decision["routing_decision"]["inputs"]

    assert inputs["project_anatomy_profile"]["persist_in_sidecar"] is False
    assert inputs["project_anatomy_profile"]["unresolved_is_allowed"] is True
    assert inputs["analysis_binding"]["persist_in_sidecar"] is False
    assert inputs["analysis_binding"]["unresolved_is_allowed"] is True
    assert inputs["document_kind"]["authority_transfer"] is False
    assert inputs["physical_format"]["authority_transfer"] is False
    assert inputs["source_scope"]["authority_transfer"] is False


def test_m2_information_and_scope_are_not_promoted_to_production_persistence() -> None:
    decision = _load(M3_DECISION)

    assert (
        decision["information_carrier"]["posture"]
        == "candidate_workspace_metadata_only"
    )
    assert decision["information_carrier"]["production_persistence_adopted"] is False
    assert decision["scope_carrier"]["posture"] == "candidate_source_metadata_only"
    assert decision["scope_carrier"]["production_persistence_adopted"] is False


def test_existing_downstream_contracts_are_reused_without_claiming_persistence() -> None:
    decision = _load(M3_DECISION)
    contracts = decision["existing_downstream_contracts"]

    assert (
        contracts["document_structure"]["contract"]
        == "schemas/document_knowledge_slice.schema.yaml"
    )
    assert (
        contracts["document_structure"]["contract_status"]
        == "candidate_support_schema_implemented_external_persistence_not_adopted"
    )
    assert contracts["document_structure"]["copy_into_sidecar"] is False
    assert decision["observed"]["document_structure_external_persistence_adopted"] is False
    assert (
        contracts["project_semantics"]["contract"]
        == "schemas/architecture-project-understanding/observation_bundle.schema.yaml"
    )
    assert contracts["project_semantics"]["copy_into_sidecar"] is False
    assert (
        decision["semantic_boundary"]["semantic_promotion_path"]
        == "canonical_observation_bundle"
    )


def test_m3_preserves_governance_distinctions() -> None:
    boundary = _load(M3_DECISION)["semantic_boundary"]

    assert boundary["manifest_ref_is_not_attribute_claim"] is True
    assert boundary["manifest_ref_is_not_relation_claim"] is True
    assert boundary["source_scope_is_not_project_completeness"] is True
    assert boundary["routing_resolution_is_not_profile_admission"] is True
    assert boundary["binding_selection_is_not_capability_adoption"] is True
    assert boundary["analysis_success_is_not_candidate_application"] is True
    assert boundary["projection_is_not_persistence"] is True
