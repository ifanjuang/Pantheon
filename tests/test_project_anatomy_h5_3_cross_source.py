"""H5.3 cross-source document/image qualification cases."""

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
CORPUS = EXAMPLES / "document_visual_cross_source_corpus.yaml"


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


def _quantities_remain_source_scoped(bundle: dict[str, Any]) -> None:
    claims = bundle["attribute_claim_candidates"]
    assert {item["attribute_key"] for item in claims} == {"economy.stated_quantity", "geometry.measured_count"}
    assert {item["value"]["value"] for item in claims} == {7, 8}
    assert len({tuple(item["source_representation_refs"]) for item in claims}) == 2
    assert any(item["code"] == "economy.payable_quantity_not_established" for item in bundle["warnings"])


def _identity_is_candidate_only(bundle: dict[str, Any]) -> None:
    assert len(bundle["relation_claim_candidates"]) == 1
    relation = bundle["relation_claim_candidates"][0]
    assert relation["relation_type"] == "identity.represents"
    assert relation["subject_ref"]["entity_type"] == "source_representation"
    assert relation["object_ref"] == {"entity_type": "stable_object", "entity_id": "OBJ-DOOR-017"}
    assert relation["assertion_mode"] == "proposed"
    assert relation["proof_status"] == "candidate"
    assert any(item["code"] == "identity.review_required" for item in bundle["warnings"])


def _temporary_not_final(bundle: dict[str, Any]) -> None:
    claim = bundle["attribute_claim_candidates"][0]
    assert claim["attribute_key"] == "physical.temporary_state"
    assert claim["value"]["value"] == "temporary_guardrail_present"
    assert any(item["code"] == "design.final_state_not_inferred" for item in bundle["warnings"])
    assert bundle["authority"]["is_decision"] is False


def _hidden_work_history_preserved(bundle: dict[str, Any]) -> None:
    before, after = bundle["source_representations"]
    assert before["observed_at"] < after["observed_at"]
    assert bundle["attribute_claim_candidates"][0]["source_representation_refs"] == ["rep.photo.before-closure"]
    assert any(item["code"] == "visibility.concealed_after_closure" for item in bundle["gaps"])
    assert any(item["code"] == "verification.current_state_withheld" for item in bundle["withheld"])
    assert bundle["coverage"]["absence_inference_allowed"] is False


INVARIANTS: dict[str, Callable[[dict[str, Any]], None]] = {
    "candidate_authority": _candidate_authority,
    "quantities_remain_source_scoped": _quantities_remain_source_scoped,
    "identity_is_candidate_only": _identity_is_candidate_only,
    "temporary_not_final": _temporary_not_final,
    "hidden_work_history_preserved": _hidden_work_history_preserved,
}


@pytest.mark.parametrize("case", _cases(), ids=lambda case: "+".join(case["scenario_ids"]))
def test_h5_3_cross_source_cases_validate_and_keep_boundaries(case: dict[str, Any]) -> None:
    assert case["expected_valid"] is True
    _validator().validate(case["bundle"])
    for invariant in case["invariants"]:
        INVARIANTS[invariant](case["bundle"])


def test_h5_3_cross_source_slice_is_bounded_and_does_not_duplicate_h5_2_chronology_cases() -> None:
    corpus = _load(CORPUS)
    assert {case_id for case in corpus["scenarios"] for case_id in case["scenario_ids"]} == {
        "H53-X-QTY",
        "H53-X-IDENTITY",
        "H53-X-TEMPORARY",
        "H53-X-HIDDEN",
    }
    text = CORPUS.read_text(encoding="utf-8")
    for duplicated_concern in ("older issue received", "same business index", "separate receipt events"):
        assert duplicated_concern not in text
