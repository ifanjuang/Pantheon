"""Deterministic H5.2 qualification corpus for Project Anatomy."""

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
CORPUS = EXAMPLES / "qualification_corpus.yaml"


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
            resource=Resource.from_contents(
                _load(SCHEMAS / name),
                default_specification=DRAFT202012,
            ),
        )
    schema = _load(SCHEMAS / "observation_bundle.schema.yaml")
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
        registry=registry,
    )


def _merge(base: Any, overrides: Any) -> Any:
    """Recursively merge mappings; scenario arrays deliberately replace base arrays."""
    if not isinstance(base, dict) or not isinstance(overrides, dict):
        return copy.deepcopy(overrides)
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        merged[key] = _merge(merged[key], value) if key in merged else copy.deepcopy(value)
    return merged


def _cases() -> list[dict[str, Any]]:
    corpus = _load(CORPUS)
    assert corpus["base_example"] == "observation_bundle.example.yaml"
    base = _load(EXAMPLES / corpus["base_example"])
    return [
        scenario | {"bundle": _merge(base, scenario["overrides"])}
        for scenario in corpus["scenarios"]
    ]


def _case_id(case: dict[str, Any]) -> str:
    return "+".join(str(value) for value in case["scenario_ids"])


def _candidate_authority(bundle: dict[str, Any]) -> None:
    assert set(bundle["authority"].values()) == {False}
    assert all(item["proof_status"] == "candidate" for item in bundle["source_representations"])
    assert all(
        item["proof_status"] == "candidate"
        for key in ("attribute_claim_candidates", "relation_claim_candidates")
        for item in bundle[key]
    )


def _contradictions_preserved(bundle: dict[str, Any]) -> None:
    claims = bundle["attribute_claim_candidates"]
    assert [claim["value"]["value"] for claim in claims] == [21.4, 20.9]
    assert len({claim["attribute_claim_id"] for claim in claims}) == 2
    assert len({tuple(claim["source_representation_refs"]) for claim in claims}) == 2


def _partial_absence_refused(bundle: dict[str, Any]) -> None:
    coverage = bundle["coverage"]
    assert coverage["completeness"] == "partial_for_declared_scope"
    assert coverage["absence_inference_allowed"] is False
    assert coverage["observed_scope"] != bundle["scope"]
    assert bundle["gaps"]


def _source_chronology_preserved(bundle: dict[str, Any]) -> None:
    issue_42, late_issue_41 = bundle["source_representations"][:2]
    assert issue_42["source_version_ref"] == "drawing.a.issue-42"
    assert late_issue_41["source_version_ref"] == "drawing.a.issue-41"
    assert late_issue_41["observed_at"] > issue_42["observed_at"]
    assert bundle["basis"]["source_version_refs"] == ["drawing.a.issue-42", "drawing.a.issue-41"]


def _business_index_not_identity(bundle: dict[str, Any]) -> None:
    representations = bundle["source_representations"]
    assert {item["identifiers"][0]["value"] for item in representations} == {"A-101"}
    assert len({item["content_digest"] for item in representations}) == 2
    assert bundle["relation_claim_candidates"] == []


def _receipt_identity_preserved(bundle: dict[str, Any]) -> None:
    same_bytes = [
        item
        for item in bundle["source_representations"]
        if item["content_digest"] == "sha256:bytes-issue-42"
    ]
    assert len(same_bytes) == 2
    assert len({item["representation_id"] for item in same_bytes}) == 2
    assert len({item["source_artifact_ref"] for item in same_bytes}) == 2


def _multi_granularity_no_identity(bundle: dict[str, Any]) -> None:
    assert len(bundle["source_representations"]) == 3
    assert bundle["scope"]["classes"] == ["IfcSystem", "IfcFlowTerminal"]
    assert bundle["relation_claim_candidates"] == []


def _same_label_not_identity(bundle: dict[str, Any]) -> None:
    labels = [item["identifiers"][0]["value"] for item in bundle["source_representations"]]
    assert labels.count("Diffuseur") == 2
    assert bundle["relation_claim_candidates"] == []


def _physical_not_contractual(bundle: dict[str, Any]) -> None:
    keys = {claim["attribute_key"] for claim in bundle["attribute_claim_candidates"]}
    assert keys == {
        "physical.installation_status",
        "physical.observed_quantity",
        "physical.measured_delay_days",
    }
    assert not any(
        token in key
        for key in keys
        for token in ("received", "payable", "causation", "liability", "compliance")
    )


def _urgent_no_effect(bundle: dict[str, Any]) -> None:
    assert any(item["code"] == "attention.urgent_observation" for item in bundle["warnings"])
    assert bundle["authority"]["authorizes_external_effect"] is False


INVARIANTS: dict[str, Callable[[dict[str, Any]], None]] = {
    "candidate_authority": _candidate_authority,
    "contradictions_preserved": _contradictions_preserved,
    "partial_absence_refused": _partial_absence_refused,
    "source_chronology_preserved": _source_chronology_preserved,
    "business_index_not_identity": _business_index_not_identity,
    "receipt_identity_preserved": _receipt_identity_preserved,
    "multi_granularity_no_identity": _multi_granularity_no_identity,
    "same_label_not_identity": _same_label_not_identity,
    "physical_not_contractual": _physical_not_contractual,
    "urgent_no_effect": _urgent_no_effect,
}


@pytest.mark.parametrize(
    "case",
    [case for case in _cases() if case["expected_valid"]],
    ids=_case_id,
)
def test_valid_h5_2_scenarios_are_contract_valid_and_keep_invariants(
    case: dict[str, Any],
) -> None:
    _validator().validate(case["bundle"])
    for name in case["invariants"]:
        INVARIANTS[name](case["bundle"])


@pytest.mark.parametrize(
    "case",
    [case for case in _cases() if not case["expected_valid"]],
    ids=_case_id,
)
def test_invalid_h5_2_scenarios_fail_at_the_governed_contract_path(
    case: dict[str, Any],
) -> None:
    with pytest.raises(jsonschema.ValidationError) as exc_info:
        _validator().validate(case["bundle"])
    assert list(exc_info.value.absolute_path) == case["expected_error_path"]


def test_h5_2_corpus_covers_the_bounded_issue_matrix_without_hidden_cases() -> None:
    cases = _cases()
    scenario_ids = {
        scenario_id
        for case in cases
        for scenario_id in case["scenario_ids"]
        if not str(scenario_id).endswith("-negative")
    }
    assert scenario_ids == {
        "S01",
        "S03",
        "S04",
        "S05",
        "S06",
        "S07",
        "S11",
        "S15",
        "S16",
        "S18",
        "S21",
        "S22",
        "S23",
        "S27",
    }
    assert set(INVARIANTS) == {
        name for case in cases if case["expected_valid"] for name in case["invariants"]
    }
