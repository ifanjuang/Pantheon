"""Deterministic H5.4 IFC source qualification."""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-project-understanding"
CORPUS = EXAMPLES / "ifc_qualification_corpus.yaml"


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validator() -> jsonschema.Draft202012Validator:
    registry = Registry()
    for name in (
        "shared.schema.yaml",
        "source_representation.schema.yaml",
        "attribute_claim.schema.yaml",
        "relation_claim.schema.yaml",
    ):
        registry = registry.with_resource(
            uri=name,
            resource=Resource.from_contents(_load(SCHEMAS / name), default_specification=DRAFT202012),
        )
    return jsonschema.Draft202012Validator(
        _load(SCHEMAS / "observation_bundle.schema.yaml"),
        format_checker=jsonschema.FormatChecker(),
        registry=registry,
    )


def _merge(base: Any, overrides: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(overrides, dict):
        return copy.deepcopy(overrides)
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        merged[key] = _merge(merged[key], value) if key in merged else copy.deepcopy(value)
    return merged


def _cases() -> list[dict[str, Any]]:
    corpus = _load(CORPUS)
    base = _load(EXAMPLES / corpus["base_example"])
    return [scenario | {"bundle": _merge(base, scenario["overrides"])} for scenario in corpus["scenarios"]]


def _candidate_authority(bundle: dict[str, Any]) -> None:
    assert set(bundle["authority"].values()) == {False}
    assert all(item["proof_status"] == "candidate" for item in bundle["source_representations"])
    assert all(
        item["proof_status"] == "candidate"
        for key in ("attribute_claim_candidates", "relation_claim_candidates")
        for item in bundle[key]
    )


def _same_guid_changed_state_preserved(bundle: dict[str, Any]) -> None:
    reps = bundle["source_representations"]
    assert {rep["identifiers"][0]["value"] for rep in reps} == {"3aDoorGuidA"}
    assert len({rep["source_version_ref"] for rep in reps}) == 2
    assert len({rep["content_digest"] for rep in reps}) == 2
    assert [claim["value"]["value"] for claim in bundle["attribute_claim_candidates"]] == ["EI30", "EI60"]
    assert all("supersedes_claim_ref" not in claim for claim in bundle["attribute_claim_candidates"])


def _partial_ifc_absence_refused(bundle: dict[str, Any]) -> None:
    coverage = bundle["coverage"]
    assert coverage["completeness"] == "partial_for_declared_scope"
    assert coverage["absence_inference_allowed"] is False
    assert coverage["observed_scope"] != bundle["scope"]


def _source_disappearance_not_retirement(bundle: dict[str, Any]) -> None:
    assert bundle["coverage"]["absence_inference_allowed"] is True
    assert any(item["code"] == "source.occurrence_not_observed_in_later_complete_snapshot" for item in bundle["warnings"])
    assert any(item["code"] == "project.retirement_not_inferred" for item in bundle["warnings"])
    assert bundle["relation_claim_candidates"] == []
    assert bundle["attribute_claim_candidates"] == []


def _ifc_identity_candidate_only(bundle: dict[str, Any]) -> None:
    representation = bundle["source_representations"][0]
    assert representation["identifiers"] == [{"scheme": "ifc.global_id", "value": "3aDoorGuidA"}]
    relation = bundle["relation_claim_candidates"][0]
    assert relation["relation_type"] == "identity.represents"
    assert relation["object_ref"] == {"entity_type": "stable_object", "entity_id": "OBJ-DOOR-017"}
    assert relation["assertion_mode"] == "proposed"
    assert relation["proof_status"] == "candidate"


def _changed_guid_not_automatic_identity(bundle: dict[str, Any]) -> None:
    reps = bundle["source_representations"]
    assert {rep["identifiers"][0]["value"] for rep in reps} == {"3aOldGuid", "3aNewGuid"}
    relations = bundle["relation_claim_candidates"]
    assert len(relations) == 2
    assert {rel["object_ref"]["entity_id"] for rel in relations} == {"OBJ-DOOR-017"}
    assert all(rel["proof_status"] == "candidate" for rel in relations)
    assert all(rel["assertion_mode"] == "proposed" for rel in relations)


def _ifc_hierarchy_not_promoted(bundle: dict[str, Any]) -> None:
    rep = bundle["source_representations"][0]
    native = rep["context"]["native_context"]
    assert native["ifc_class"] == "IfcSpace"
    assert native["container_class"] == "IfcBuildingStorey"
    assert bundle["relation_claim_candidates"] == []
    assert {claim["attribute_key"] for claim in bundle["attribute_claim_candidates"]} == {
        "ifc.entity_class",
        "ifc.predefined_type",
    }
    assert any(item["code"] == "hierarchy.source_native_only" for item in bundle["warnings"])


def _failed_ifc_no_fabrication(bundle: dict[str, Any]) -> None:
    assert bundle["operational_outcome"] == "failed"
    assert bundle["coverage"]["absence_inference_allowed"] is False
    assert bundle["source_representations"] == []
    assert bundle["attribute_claim_candidates"] == []
    assert bundle["relation_claim_candidates"] == []
    assert any(item["code"] == "source.ifc_parse_failed" for item in bundle["gaps"])


INVARIANTS: dict[str, Callable[[dict[str, Any]], None]] = {
    "candidate_authority": _candidate_authority,
    "same_guid_changed_state_preserved": _same_guid_changed_state_preserved,
    "partial_ifc_absence_refused": _partial_ifc_absence_refused,
    "source_disappearance_not_retirement": _source_disappearance_not_retirement,
    "ifc_identity_candidate_only": _ifc_identity_candidate_only,
    "changed_guid_not_automatic_identity": _changed_guid_not_automatic_identity,
    "ifc_hierarchy_not_promoted": _ifc_hierarchy_not_promoted,
    "failed_ifc_no_fabrication": _failed_ifc_no_fabrication,
}


@pytest.mark.parametrize("case", _cases(), ids=lambda case: "+".join(case["scenario_ids"]))
def test_h5_4_ifc_cases_validate_and_keep_source_boundaries(case: dict[str, Any]) -> None:
    assert case["expected_valid"] is True
    _validator().validate(case["bundle"])
    for invariant in case["invariants"]:
        INVARIANTS[invariant](case["bundle"])


def test_h5_4_ifc_slice_is_bounded_and_reuses_h5_2_granularity_cases() -> None:
    corpus = _load(CORPUS)
    assert {case_id for case in corpus["scenarios"] for case_id in case["scenario_ids"]} == {
        "H54-IFC-SAME-GUID-CHANGED",
        "H54-IFC-PARTIAL-MISSING",
        "H54-IFC-COMPLETE-DISAPPEARANCE",
        "H54-IFC-IDENTITY-CANDIDATE",
        "H54-IFC-CHANGED-GUID-SAME-CANDIDATE",
        "H54-IFC-HIERARCHY-CONTEXT",
        "H54-IFC-FAILED",
    }
    text = CORPUS.read_text(encoding="utf-8")
    assert "IfcSystem" not in text
    assert "IfcFlowTerminal" not in text
