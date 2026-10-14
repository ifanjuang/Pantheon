"""H5.8 longitudinal qualification over one representative project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CORPUS = (
    ROOT
    / "schemas"
    / "examples"
    / "architecture-project-understanding"
    / "longitudinal_project_qualification_corpus.yaml"
)


def _load() -> dict[str, Any]:
    value = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _moments(corpus: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {moment["id"]: moment for moment in corpus["moments"]}


def _events(moment: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
    return [event for event in moment["events"] if event["type"] == event_type]


def test_h5_8_is_one_ordered_t0_to_t5_project_without_timeline_owner() -> None:
    corpus = _load()
    assert corpus["status"] == "qualification_only"
    assert [moment["id"] for moment in corpus["moments"]] == ["T0", "T1", "T2", "T3", "T4", "T5"]
    timestamps = [moment["occurred_at"] for moment in corpus["moments"]]
    assert timestamps == sorted(timestamps)
    assert corpus["project"]["expected_room_count"] == 10
    assert corpus["project"]["expected_significant_object_count"] == 40
    assert "ProjectTimelineOwner" in corpus["cross_time_assertions"]["forbidden_architecture_additions"]
    assert "PhaseEngine" in corpus["cross_time_assertions"]["forbidden_architecture_additions"]


def test_h5_8_reuses_prior_h_corpora_instead_of_redefining_source_models() -> None:
    corpus = _load()
    assert set(corpus["reuses"]) == {
        "qualification_corpus.yaml",
        "document_visual_qualification_corpus.yaml",
        "multi_purpose_qualification_corpus.yaml",
    }
    kinds = {source["source_kind"] for moment in corpus["moments"] for source in moment["sources"]}
    assert {"drawing", "manual", "ifc", "revit", "photo", "other"} <= kinds
    assert corpus["project"]["granularity_exercised"] == [
        "project",
        "building",
        "level",
        "room",
        "system",
        "assembly",
        "object",
        "component",
    ]


def test_h5_8_stable_identity_survives_label_and_native_id_changes() -> None:
    corpus = _load()
    moments = _moments(corpus)
    continuity = _events(moments["T1"], "stable_identity_continuity")[0]
    native_change = _events(moments["T3"], "source_native_id_change")[0]
    identity_review = _events(moments["T3"], "identity_review")[0]

    assert continuity["stable_object_ref"] == "OBJ-OPENING-017"
    assert continuity["native_label_change"] == {"from": "P12", "to": "PF-12"}
    assert native_change["stable_object_ref"] == "OBJ-OPENING-017"
    assert native_change["previous_native_id"] != native_change["current_native_id"]
    assert native_change["continuity_requires_review"] is True
    assert identity_review["stable_object_ref"] == "OBJ-OPENING-017"
    assert identity_review["review_state"] == "select_existing_object"


def test_h5_8_contradictory_widths_remain_source_scoped_without_global_winner() -> None:
    corpus = _load()
    claim_set = corpus["cross_time_assertions"]["contradictory_claim_sets"][0]
    assert claim_set["stable_object_ref"] == "OBJ-OPENING-017"
    assert claim_set["attribute_key"] == "geometry.width"
    assert [claim["value"] for claim in claim_set["claims"]] == [0.90, 0.93, 0.93]
    assert len({claim["source_ref"] for claim in claim_set["claims"]}) == 3
    assert claim_set["universal_winner"] is None


def test_h5_8_requirements_quantities_and_currentness_do_not_collapse_into_truth() -> None:
    corpus = _load()
    moments = _moments(corpus)
    t1 = moments["T1"]
    t2 = moments["T2"]

    requirement_change = _events(t1, "requirement_change")[0]
    late_receipt = _events(t1, "late_receipt")[0]
    requirement = _events(t2, "requirement")[0]
    statement = _events(t2, "quantity_statement")[0]
    observation = _events(t2, "quantity_observation")[0]

    assert requirement_change["old_value"] != requirement_change["new_value"]
    assert late_receipt["does_not_become_universal_current"] is True
    assert requirement["scope_ref"] == "group:external_openings"
    assert statement["value"] != observation["value"]
    assert statement["authority"] != observation["authority"]
    assert "requirement_not_observation" in t2["invariants"]
    assert "observed_quantity_not_payable_quantity" in t2["invariants"]


def test_h5_8_partial_revit_coverage_cannot_create_deletion() -> None:
    corpus = _load()
    t3 = _moments(corpus)["T3"]
    revit = next(source for source in t3["sources"] if source["source_kind"] == "revit")
    unresolved = _events(t3, "unresolved_missing_occurrence")[0]

    assert revit["coverage"] == "partial_for_declared_scope"
    assert unresolved["reason"] == "level_01_not_traversed"
    assert unresolved["deletion_inferred"] is False
    assert "partial_revit_no_deletion" in t3["invariants"]


def test_h5_8_construction_preserves_physical_contractual_and_actor_boundaries() -> None:
    corpus = _load()
    t4 = _moments(corpus)["T4"]
    declaration = _events(t4, "contractor_declaration")[0]
    repair = _events(t4, "repair_provenance")[0]
    hidden = _events(t4, "hidden_work")[0]
    temporary = _events(t4, "temporary_state")[0]
    urgent = _events(t4, "urgent_attention")[0]

    assert declaration["authority_transfer"] is False
    assert repair["original_actor_ref"] != repair["repair_actor_ref"]
    assert repair["prior_history_preserved"] is True
    assert hidden["current_visibility"] == "inaccessible"
    assert hidden["prior_observation_retained"] is True
    assert temporary["physically_present"] is True
    assert temporary["intended_final_state"] is False
    assert urgent["automatic_external_action_authorized"] is False


def test_h5_8_reception_and_doe_append_without_rewriting_history() -> None:
    corpus = _load()
    t5 = _moments(corpus)["T5"]
    doe = _events(t5, "doe_assertion")[0]
    reception = _events(t5, "reception_reference")[0]
    residual = _events(t5, "residual_unknown")[0]
    recurrence = _events(t5, "recurrence")[0]
    appendability = _events(t5, "post_reception_appendability")[0]

    assert doe["becomes_observed_truth"] is False
    assert reception["state_owned_elsewhere"] is True
    assert residual["reason"] == "concealed_after_closure"
    assert recurrence["prior_apparent_resolution_ref"] != recurrence["new_observation_ref"]
    assert recurrence["rewrites_prior_history"] is False
    assert appendability["reception_era_history_mutable"] is False


def test_h5_8_never_infers_governance_authority_from_project_history() -> None:
    authority = _load()["cross_time_assertions"]["authority_boundaries"]
    assert authority == {
        "evidence_inferred": False,
        "approval_inferred": False,
        "decision_inferred": False,
        "reception_inferred": False,
        "liability_inferred": False,
        "payable_quantity_inferred": False,
    }
