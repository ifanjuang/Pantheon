"""Qualification-only boundaries for issue Pantheon-Next#949 spatial perception + episodic memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "spatial_perception_episodic_memory_qualification.yaml"
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _bundle_validator() -> jsonschema.Draft202012Validator:
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


def _fixture() -> dict[str, Any]:
    return _load(FIXTURE)


def _episodes(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["episode_id"]: item for item in data["free_episodes"]}


def test_q949_is_qualification_only_and_adopts_no_new_authority() -> None:
    data = _fixture()

    assert data["status"] == "qualification_only"
    assert data["issue_ref"] == 949
    assert set(data["authority"].values()) == {False}
    assert data["non_goals"] == [
        "no SpatialGraph owner",
        "no EpisodicMemory Pantheon primitive",
        "no fifth Project Anatomy primitive",
        "no universal persisted scene graph",
        "no automatic stable-object creation",
        "no automatic Evidence or Decision promotion",
        "no SAM, YOLO, Depth Anything or multiview provider adoption",
        "no pixel-level or point-level canonical claim explosion",
        "no claim that monocular depth is a professional measurement",
    ]


def test_q949_keeps_four_cognitive_layers_with_governance_orthogonal() -> None:
    data = _fixture()
    layer_items = data["cognitive_layers"]
    layer_ids = [item["layer_id"] for item in layer_items]

    assert len(layer_items) == 4
    assert len(set(layer_ids)) == len(layer_ids)

    layers = {item["layer_id"]: item for item in layer_items}
    assert set(layers) == {
        "perception",
        "episodic_memory",
        "structured_semantics",
        "working_context",
    }
    assert layers["perception"]["persistence_posture"] == "derived_representation_only"
    assert layers["episodic_memory"]["persistence_posture"] == "runtime_memory_only"
    assert layers["structured_semantics"]["persistence_posture"] == "existing_governed_owners_only"
    assert layers["working_context"]["persistence_posture"] == "task_local"
    assert "promotion" in data["governance_boundary"]["principle"]


def test_q949_perception_stages_are_replaceable_and_non_semantic_by_default() -> None:
    data = _fixture()
    stages = data["perception_stages"]

    assert set(stages) == {
        "segmentation",
        "detection",
        "monocular_depth",
        "surface_normals",
        "multi_view_geometry",
    }
    assert "SAM-family" in stages["segmentation"]["candidate_families"]
    assert "YOLO-family" in stages["detection"]["candidate_families"]
    assert "Depth-Anything-family" in stages["monocular_depth"]["candidate_families"]
    assert stages["segmentation"]["semantic_limit"] == "mask_does_not_define_stable_identity"
    assert stages["detection"]["semantic_limit"] == "detector_class_does_not_define_project_object"
    assert stages["multi_view_geometry"]["semantic_limit"] == "multiview_track_does_not_accept_project_identity"


def test_q949_coordinate_ladder_refuses_unframed_project_geometry() -> None:
    data = _fixture()

    assert data["coordinate_ladder"] == [
        "PIXEL",
        "CAMERA",
        "LOCAL_RECONSTRUCTION",
        "PROJECT",
    ]
    rules = "\n".join(data["coordinate_rules"])
    assert "explicit alignment or calibration provenance" in rules
    assert "Local XYZ without a declared frame is not project geometry" in rules
    assert "Relative monocular depth" in rules

    multiview = next(
        item
        for item in data["derived_representations"]
        if item["stage"] == "multi_view_geometry"
    )
    assert multiview["coordinate_frame"] == "LOCAL_RECONSTRUCTION"
    assert multiview["project_alignment_status"] == "unresolved"


def test_q949_dense_outputs_remain_derived_and_not_professional_measurements() -> None:
    data = _fixture()
    derived = data["derived_representations"]

    assert derived
    assert all(item["authoritative"] is False for item in derived)
    assert all(item["professional_measurement"] is False for item in derived)
    assert all(item.get("source_ref") or item.get("source_refs") for item in derived)
    assert all(item["model_identity"].startswith("synthetic.") for item in derived)
    assert all(item["model_version"] == "qualification-only" for item in derived)

    depth = next(item for item in derived if item["stage"] == "monocular_depth")
    assert depth["depth_mode"] == "relative"
    assert depth["metric_scale_resolved"] is False


def test_q949_free_episode_can_survive_without_stable_identity_or_semantic_promotion() -> None:
    data = _fixture()
    episodes = _episodes(data)
    episode = episodes["episode.zone-a.irregular-wall"]

    assert episode["free_payload"]
    assert episode["stable_identity_status"] == "unresolved"
    assert not any(ref["kind"].startswith("anatomy") for ref in episode["refs"])

    case = next(
        item for item in data["qualification_cases"] if item["case_id"] == "Q949-FREE-NO-IDENTITY"
    )
    assert case["expected"] == {
        "free_payload_retained": True,
        "stable_object_required": False,
        "semantic_promotion_required": False,
    }


def test_q949_cross_episode_association_is_not_relation_or_identity_admission() -> None:
    data = _fixture()
    episodes = _episodes(data)
    episode = episodes["episode.zone-a.same-feature-cluster"]
    episode_refs = [
        ref["ref"]
        for ref in episode["refs"]
        if ref["kind"] == "episode"
    ]

    assert len(episode_refs) == 2
    assert len(set(episode_refs)) == len(episode_refs)
    assert all(ref in episodes for ref in episode_refs)
    assert episode["association"] == {
        "status": "candidate",
        "proposed_same_feature": True,
        "identity_represents_admitted": False,
    }
    case = next(
        item
        for item in data["qualification_cases"]
        if item["case_id"] == "Q949-CROSS-EPISODE-ASSOCIATION"
    )
    assert case["expected"]["linked_episode_count"] == len(episode_refs)
    assert "relation_claim" not in episode
    assert "stable_object_id" not in episode


def test_q949_structured_context_may_enrich_recall_without_promotion() -> None:
    data = _fixture()
    case = next(
        item
        for item in data["qualification_cases"]
        if item["case_id"] == "Q949-STRUCTURED-CONTEXT-RECALL"
    )

    assert case["query_context_ref"] == "stable-object:window-17"
    assert set(case["expected_episode_refs"]) == {
        "episode.zone-a.contextual-recall",
        "episode.zone-a.ambiguous-opening",
    }
    assert case["expected"]["structured_context_may_improve_recall"] is True
    assert case["expected"]["recalled_episode_becomes_project_truth"] is False


def test_q949_ambiguity_survives_instead_of_silent_identity_choice() -> None:
    data = _fixture()
    episode = _episodes(data)["episode.zone-a.ambiguous-opening"]

    assert episode["resolution_status"] == "unresolved"
    assert episode["selected_identity"] is None
    assert len(episode["identity_candidates"]) == 2
    assert set(episode["identity_candidates"]) == {
        "stable-object:window-17",
        "stable-object:window-18",
    }


def test_q949_retrieval_comparison_claims_qualitative_scope_not_benchmark_superiority() -> None:
    data = _fixture()
    comparison = data["retrieval_comparison"]

    assert comparison["benchmark_claim"] == "none"
    assert comparison["qualification_goal"] == "useful_additional_recall_without_authority_transfer"
    assert len(comparison["structured_plus_episodic_spatial"]["context_refs"]) > len(
        comparison["structured_only"]["context_refs"]
    )


def test_q949_selected_free_observation_can_use_existing_observation_bundle_without_identity_fabrication() -> None:
    data = _fixture()
    promotion = data["selected_promotion"]
    bundle = promotion["observation_bundle_candidate"]

    _bundle_validator().validate(bundle)

    assert promotion["source_episode_ref"] == "episode.zone-a.irregular-wall"
    assert set(bundle["authority"].values()) == {False}
    assert bundle["relation_claim_candidates"] == []
    assert bundle["coverage"]["absence_inference_allowed"] is False

    representation = bundle["source_representations"][0]
    claim = bundle["attribute_claim_candidates"][0]

    assert representation["source_kind"] == "photo"
    assert representation["coordinate_frame"] == "PIXEL"
    assert representation["proof_status"] == "candidate"
    assert claim["subject_ref"] == {
        "entity_type": "source_representation",
        "entity_id": representation["representation_id"],
    }
    assert claim["source_authority"] == "model_interpretation_candidate"
    assert claim["proof_status"] == "candidate"
    assert "certainty" not in claim
    assert any(item["code"] == "identity.stable_object_unresolved" for item in bundle["gaps"])
    assert any(item["code"] == "measurement.professional_geometry_withheld" for item in bundle["withheld"])


def test_q949_does_not_explode_dense_perception_into_canonical_claims() -> None:
    data = _fixture()
    bundle = data["selected_promotion"]["observation_bundle_candidate"]

    assert len(data["derived_representations"]) == 4
    assert len(bundle["attribute_claim_candidates"]) == 1
    assert len(bundle["relation_claim_candidates"]) == 0
    assert all("pixel_claims" not in item for item in data["derived_representations"])
    assert all("point_claims" not in item for item in data["derived_representations"])
