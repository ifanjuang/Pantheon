"""Observation Bundles reuse the append-only Execution Result owner."""

from copy import deepcopy

import pytest

from mvp_vertical import execution_results


PROJECT_REF = "project.contract-test"
TASK_CONTRACT_REF = "task-contract.contract-test"


def _bundle() -> dict:
    scope = {
        "document_refs": ["revit-document.contract-test"],
        "categories": ["OST_Rooms"],
        "include_linked_sources": False,
    }
    return {
        "observation_bundle_id": "observation-bundle.contract-test",
        "project_ref": PROJECT_REF,
        "task_contract_ref": TASK_CONTRACT_REF,
        "basis": {
            "source_artifact_refs": ["source.revit.contract-test"],
            "source_version_refs": ["snapshot.revit.contract-test.1"],
            "exact_digests": [
                {
                    "source_artifact_ref": "source.revit.contract-test",
                    "source_version_ref": "snapshot.revit.contract-test.1",
                    "digest": "sha256:source-contract-test",
                }
            ],
        },
        "method": {
            "capability_id": "building_model.observe.spaces",
            "binding_id": "binding.revit.contract-test",
            "operation_id": "revit.architecture.observe_rooms.v1",
            "adapter_ref": "pantheon.revit",
            "adapter_version": "0.1.0",
            "request_ref": "request.contract-test",
        },
        "observed_at": "2026-08-09T12:00:00Z",
        "freshness_token": "sha256:document-contract-test",
        "scope": scope,
        "coverage": {
            "completeness": "partial_for_declared_scope",
            "observed_scope": scope,
            "excluded_reasons": ["live_completeness_not_validated"],
            "absence_inference_allowed": False,
        },
        "limitations": ["contract fixture only"],
        "source_representations": [
            {
                "representation_id": "rep.revit.contract-test.room-101",
                "project_ref": PROJECT_REF,
                "source_artifact_ref": "source.revit.contract-test",
                "source_version_ref": "snapshot.revit.contract-test.1",
                "source_kind": "revit",
                "identifiers": [
                    {"scheme": "revit.unique_id", "value": "room-101"}
                ],
                "observed_at": "2026-08-09T12:00:00Z",
                "binding_ref": "binding.revit.contract-test",
                "adapter_version": "0.1.0",
                "freshness_token": "sha256:document-contract-test",
                "context": {
                    "document_ref": "revit-document.contract-test",
                    "native_context": {"category": "OST_Rooms"},
                },
                "proof_status": "candidate",
            }
        ],
        "attribute_claim_candidates": [],
        "relation_claim_candidates": [],
        "gaps": [],
        "withheld": [],
        "warnings": [],
        "operational_outcome": "success",
        "authority": dict(execution_results.AUTHORITY),
    }


def _validate(payload: dict, *, schema_ref: str | None = None) -> None:
    execution_results._validate_result_payload(
        kind="observation_bundle",
        schema_ref=schema_ref or execution_results.OBSERVATION_BUNDLE_SCHEMA_REF,
        payload=payload,
        project_ref=PROJECT_REF,
        task_contract_ref=TASK_CONTRACT_REF,
    )


def test_observation_bundle_uses_the_exact_vendored_contract() -> None:
    _validate(_bundle())


def test_observation_bundle_requires_the_canonical_schema_ref() -> None:
    with pytest.raises(execution_results.ExecutionResultError, match="canonical schema_ref"):
        _validate(_bundle(), schema_ref="schemas/observation_bundle.schema.yaml")


@pytest.mark.parametrize("field", ["project_ref", "task_contract_ref"])
def test_observation_bundle_cannot_cross_execution_context(field: str) -> None:
    payload = _bundle()
    payload[field] = "another-context"
    with pytest.raises(execution_results.ExecutionResultError, match="execution result"):
        _validate(payload)


def test_observation_bundle_cannot_gain_authority() -> None:
    payload = deepcopy(_bundle())
    payload["authority"]["is_fact"] = True
    with pytest.raises(execution_results.ExecutionResultError, match="governed contract"):
        _validate(payload)


def test_non_success_bundle_cannot_enable_absence_inference() -> None:
    payload = _bundle()
    payload["operational_outcome"] = "failed"
    payload.pop("freshness_token")
    payload["coverage"]["completeness"] = "complete_for_declared_scope"
    payload["coverage"]["absence_inference_allowed"] = True
    with pytest.raises(execution_results.ExecutionResultError, match="governed contract"):
        _validate(payload)
