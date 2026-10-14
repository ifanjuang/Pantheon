"""Remaining deterministic H5.3 closure cases."""

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
CORPUS = EXAMPLES / "document_visual_remaining_cases.yaml"


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


def _prescription_not_collapsed_into_observation(bundle: dict[str, Any]) -> None:
    assert {item["source_kind"] for item in bundle["source_representations"]} == {"other", "drawing"}
    assert len(bundle["attribute_claim_candidates"]) == 1
    assert bundle["attribute_claim_candidates"][0]["subject_ref"]["entity_id"] == "rep.pdf.door-p12-width"
    assert any(item["code"] == "requirement.separate_path" for item in bundle["withheld"])
    assert bundle["coverage"]["absence_inference_allowed"] is False


def _triple_quantity_provenance(bundle: dict[str, Any]) -> None:
    claims = bundle["attribute_claim_candidates"]
    assert {item["attribute_key"] for item in claims} == {
        "economy.stated_quantity",
        "geometry.measured_count",
        "physical.visible_count",
    }
    assert len({tuple(item["source_representation_refs"]) for item in claims}) == 3
    assert bundle["coverage"]["absence_inference_allowed"] is False
    assert any(item["code"] == "economy.payable_quantity_not_established" for item in bundle["warnings"])


def _recurrence_appends_history(bundle: dict[str, Any]) -> None:
    representations = bundle["source_representations"]
    assert [item["representation_id"] for item in representations] == ["rep.photo.t0", "rep.photo.t1", "rep.photo.t2"]
    assert representations[0]["observed_at"] < representations[1]["observed_at"] < representations[2]["observed_at"]
    values = [item["value"]["value"] for item in bundle["attribute_claim_candidates"]]
    assert values == ["apparent_defect", "no_visible_defect_in_observed_region", "apparent_defect_reobserved"]
    assert all("supersedes_claim_ref" not in item for item in bundle["attribute_claim_candidates"])
    assert any(item["code"] == "review.no_reservation_inference" for item in bundle["warnings"])


INVARIANTS: dict[str, Callable[[dict[str, Any]], None]] = {
    "candidate_authority": _candidate_authority,
    "prescription_not_collapsed_into_observation": _prescription_not_collapsed_into_observation,
    "triple_quantity_provenance": _triple_quantity_provenance,
    "recurrence_appends_history": _recurrence_appends_history,
}


@pytest.mark.parametrize("case", _cases(), ids=lambda case: "+".join(case["scenario_ids"]))
def test_remaining_h5_3_cases_validate_and_preserve_semantics(case: dict[str, Any]) -> None:
    assert case["expected_valid"] is True
    _validator().validate(case["bundle"])
    for invariant in case["invariants"]:
        INVARIANTS[invariant](case["bundle"])


def test_remaining_h5_3_cases_are_exactly_the_identified_closure_gaps() -> None:
    corpus = _load(CORPUS)
    assert {case_id for case in corpus["scenarios"] for case_id in case["scenario_ids"]} == {
        "H53-CLOSE-REQ-DRAWING",
        "H53-CLOSE-QTY-TRIPLE",
        "H53-CLOSE-RECURRENCE",
    }
