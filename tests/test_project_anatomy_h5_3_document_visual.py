"""H5.3 qualification for structured documents, PDF drawings and site images."""

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
CORPUS = EXAMPLES / "document_visual_qualification_corpus.yaml"
PRIVATE_DRAWING_M4 = EXAMPLES / "private_drawing_m4_observation_bundle.yaml"


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
    assert corpus["base_example"] == "observation_bundle.example.yaml"
    base = _load(EXAMPLES / corpus["base_example"])
    return [scenario | {"bundle": _merge(base, scenario["overrides"])} for scenario in corpus["scenarios"]]


def _case_id(case: dict[str, Any]) -> str:
    return "+".join(case["scenario_ids"])


def _candidate_authority(bundle: dict[str, Any]) -> None:
    assert set(bundle["authority"].values()) == {False}
    assert all(item["proof_status"] == "candidate" for item in bundle["source_representations"])
    assert all(
        item["proof_status"] == "candidate"
        for key in ("attribute_claim_candidates", "relation_claim_candidates")
        for item in bundle[key]
    )


def _requirement_not_observation(bundle: dict[str, Any]) -> None:
    assert bundle["attribute_claim_candidates"] == []
    assert any(item["code"] == "requirement.separate_path" for item in bundle["withheld"])
    assert bundle["source_representations"][0]["context"]["native_context"]["semantic_role"] == "prescription"


def _partial_absence_refused(bundle: dict[str, Any]) -> None:
    assert bundle["coverage"]["completeness"] == "partial_for_declared_scope"
    assert bundle["coverage"]["absence_inference_allowed"] is False
    assert bundle["coverage"]["observed_scope"] != bundle["scope"]


def _pdf_local_identity(bundle: dict[str, Any]) -> None:
    representation = bundle["source_representations"][0]
    assert representation["identifiers"] == [{"scheme": "drawing.local_label", "value": "P12"}]
    assert bundle["relation_claim_candidates"] == []


def _scale_uncertainty_withheld(bundle: dict[str, Any]) -> None:
    assert bundle["attribute_claim_candidates"] == []
    assert bundle["source_representations"][0]["coordinate_frame"] == "PIXEL"
    assert any(item["code"] == "measurement.scale_unresolved" for item in bundle["gaps"])
    assert any(item["code"] == "measurement.real_world_area_withheld" for item in bundle["withheld"])


def _apparent_not_contractual(bundle: dict[str, Any]) -> None:
    claim = bundle["attribute_claim_candidates"][0]
    assert claim["attribute_key"] == "physical.apparent_condition"
    assert claim["assertion_mode"] == "derived"
    assert claim["source_authority"] == "model_interpretation_candidate"
    forbidden = ("nonconform", "compliance", "received", "reservation")
    assert not any(token in claim["attribute_key"] for token in forbidden)


def _photo_field_not_absence(bundle: dict[str, Any]) -> None:
    assert bundle["coverage"]["absence_inference_allowed"] is False
    assert set(bundle["coverage"]["excluded_reasons"]) == {
        "hidden_faces_not_visible",
        "concealed_fixings_not_visible",
    }


def _photo_history_preserved(bundle: dict[str, Any]) -> None:
    before, after = bundle["source_representations"]
    assert before["observed_at"] < after["observed_at"]
    assert before["content_digest"] != after["content_digest"]
    values = [claim["value"]["value"] for claim in bundle["attribute_claim_candidates"]]
    assert values == ["apparent_defect", "no_visible_defect_in_observed_region"]
    assert any(item["code"] == "temporal.continuity_not_observed" for item in bundle["gaps"])
    assert any(item["code"] == "review.no_reservation_inference" for item in bundle["warnings"])


def _non_success_absence_refused(bundle: dict[str, Any]) -> None:
    assert bundle["operational_outcome"] == "failed"
    assert bundle["coverage"]["absence_inference_allowed"] is False


def _no_fabricated_candidates(bundle: dict[str, Any]) -> None:
    assert bundle["source_representations"] == []
    assert bundle["attribute_claim_candidates"] == []
    assert bundle["relation_claim_candidates"] == []
    assert bundle["gaps"]


def _normalized_page_bbox(representation: dict[str, Any]) -> list[float]:
    assert representation["coordinate_frame"] == "PAGE"
    locator = representation["locators"][0]
    assert locator["type"] == "page_bbox"
    native = representation["context"]["native_context"]
    width = float(native["page_width_units"])
    height = float(native["page_height_units"])
    x0, y0, x1, y1 = [float(value) for value in locator["bbox"]]
    normalized = [x0 / width, y0 / height, x1 / width, y1 / height]
    assert 0.0 <= normalized[0] < normalized[2] <= 1.0
    assert 0.0 <= normalized[1] < normalized[3] <= 1.0
    return [round(value, 6) for value in normalized]


INVARIANTS: dict[str, Callable[[dict[str, Any]], None]] = {
    "candidate_authority": _candidate_authority,
    "requirement_not_observation": _requirement_not_observation,
    "partial_absence_refused": _partial_absence_refused,
    "pdf_local_identity": _pdf_local_identity,
    "scale_uncertainty_withheld": _scale_uncertainty_withheld,
    "apparent_not_contractual": _apparent_not_contractual,
    "photo_field_not_absence": _photo_field_not_absence,
    "photo_history_preserved": _photo_history_preserved,
    "non_success_absence_refused": _non_success_absence_refused,
    "no_fabricated_candidates": _no_fabricated_candidates,
}


@pytest.mark.parametrize("case", _cases(), ids=_case_id)
def test_h5_3_document_visual_cases_validate_and_keep_boundaries(case: dict[str, Any]) -> None:
    assert case["expected_valid"] is True
    _validator().validate(case["bundle"])
    for invariant in case["invariants"]:
        INVARIANTS[invariant](case["bundle"])


def test_h5_3_uses_one_canonical_bundle_without_new_source_specific_contract() -> None:
    corpus = _load(CORPUS)
    assert corpus["status"] == "qualification_only"
    assert {case_id for case in corpus["scenarios"] for case_id in case["scenario_ids"]} == {
        "H53-DOC-REQ",
        "H53-PDF-PARTIAL",
        "H53-PDF-SCALE",
        "H53-PHOTO-DEFECT",
        "H53-PHOTO-HISTORY",
        "H53-DOC-CORRUPT",
    }
    assert set(INVARIANTS) == {
        invariant
        for case in corpus["scenarios"]
        for invariant in case["invariants"]
    }


def test_m4_private_drawing_pattern_validates_through_existing_observation_bundle() -> None:
    bundle = _load(PRIVATE_DRAWING_M4)
    _validator().validate(bundle)
    _candidate_authority(bundle)
    _partial_absence_refused(bundle)

    assert bundle["basis"] == {
        "source_artifact_refs": ["source.private-drawing-package.not-retained"],
        "source_version_refs": [],
        "exact_digests": [],
    }
    assert {item["source_artifact_ref"] for item in bundle["source_representations"]} == {
        "source.private-drawing-package.not-retained"
    }
    assert all("source_version_ref" not in item for item in bundle["source_representations"])
    assert all("content_digest" not in item for item in bundle["source_representations"])


def test_m4_one_package_keeps_sheet_dates_local_without_inventing_currentness() -> None:
    bundle = _load(PRIVATE_DRAWING_M4)
    sheet_dates = {
        item["context"]["sheet_ref"]: item["context"]["native_context"]["sheet_date"]
        for item in bundle["source_representations"]
    }

    assert sheet_dates == {"sheet-a": "2025-10-14", "sheet-b": "2026-05-22"}
    assert any(item["code"] == "currentness.sheet_dates_not_resolved" for item in bundle["gaps"])
    assert "revision_set_ref" not in bundle["basis"]


def test_m4_provisional_annotations_remain_source_reality_only() -> None:
    bundle = _load(PRIVATE_DRAWING_M4)
    provisional_ids = {
        "rep.m4.sheet-a.provisional-note",
        "rep.m4.sheet-a.ambiguous-note",
    }
    source_roles = {
        item["representation_id"]: item["context"]["native_context"]["semantic_role"]
        for item in bundle["source_representations"]
        if item["representation_id"] in provisional_ids
    }
    claimed_refs = {
        ref
        for claim in bundle["attribute_claim_candidates"]
        for ref in claim.get("source_representation_refs", [])
    }

    assert source_roles == {item_id: "provisional_annotation" for item_id in provisional_ids}
    assert claimed_refs.isdisjoint(provisional_ids)
    assert bundle["relation_claim_candidates"] == []
    assert any(
        item["code"] == "interpretation.provisional_annotation_not_promoted"
        and set(item["subject_refs"]) == provisional_ids
        for item in bundle["withheld"]
    )
    assert set(bundle["authority"].values()) == {False}


def test_m4_area_claim_stays_attached_to_source_representation_until_identity_review() -> None:
    bundle = _load(PRIVATE_DRAWING_M4)
    claim = bundle["attribute_claim_candidates"][0]

    assert claim["attribute_key"] == "space.area"
    assert claim["value"] == {"value_type": "number", "value": 9.25, "unit": "m2"}
    assert claim["subject_ref"] == {
        "entity_type": "source_representation",
        "entity_id": "rep.m4.sheet-b.space-area",
    }
    assert claim["assertion_mode"] == "observed"
    assert claim["source_authority"] == "project_working_document"
    assert bundle["relation_claim_candidates"] == []
    assert any(item["code"] == "identity.space_unresolved" for item in bundle["gaps"])


def test_m4_page_bbox_projects_to_zoom_map_normalized_rectangle_without_duplication() -> None:
    bundle = _load(PRIVATE_DRAWING_M4)
    normalized = {
        item["representation_id"]: _normalized_page_bbox(item)
        for item in bundle["source_representations"]
    }

    assert normalized == {
        "rep.m4.sheet-a.provisional-note": [0.25, 0.666667, 0.358333, 0.696429],
        "rep.m4.sheet-a.ambiguous-note": [0.325, 0.75, 0.383333, 0.779762],
        "rep.m4.sheet-b.space-area": [0.333333, 0.619048, 0.358333, 0.654762],
    }
    assert all(
        "normalized_bbox" not in item["locators"][0]
        for item in bundle["source_representations"]
    )
