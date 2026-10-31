"""Executable contract qualification for IFC/DWG/PDF/JPG observations.

No real binary source is parsed here. A qualified specialist reader must prove
its own fidelity, but all readers must converge on the EXISTING Observation
Bundle Candidate contract before APU review. In particular, this suite does
not qualify Hindsight ingestion, Hermes cognition or automatic identity binding.
"""

from __future__ import annotations

from pathlib import Path

import jsonschema
import pytest
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-project-understanding"
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
FIXTURE = EXAMPLES / "multiformat_context_qualification_corpus.yaml"


def _load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validator() -> jsonschema.Draft202012Validator:
    registry = Registry()
    for filename in (
        "shared.schema.yaml",
        "source_representation.schema.yaml",
        "attribute_claim.schema.yaml",
        "relation_claim.schema.yaml",
    ):
        registry = registry.with_resource(
            filename,
            Resource.from_contents(
                _load(SCHEMAS / filename),
                default_specification=DRAFT202012,
            ),
        )
    return jsonschema.Draft202012Validator(
        _load(SCHEMAS / "observation_bundle.schema.yaml"),
        registry=registry,
        format_checker=jsonschema.FormatChecker(),
    )


def _bundle(source: dict, project_ref: str) -> dict:
    representation_id = f"rep.synthetic.{source['id']}.opening"
    claim = source["claim"]
    observed_scope = {"document_refs": [source["source_ref"]]}
    return {
        "observation_bundle_id": f"observation-bundle.synthetic.{source['id']}",
        "project_ref": project_ref,
        "task_contract_ref": f"task-contract.synthetic.{source['id']}",
        "basis": {
            "source_artifact_refs": [source["source_ref"]],
            "source_version_refs": [source["version_ref"]],
            "exact_digests": [{
                "source_artifact_ref": source["source_ref"],
                "source_version_ref": source["version_ref"],
                "digest": source["digest"],
            }],
        },
        "method": {
            "capability_id": f"synthetic.observe.{source['source_kind']}",
            "binding_id": "binding.synthetic.qualification",
            "adapter_ref": "fixture.only.not_a_live_reader",
            "adapter_version": "0.0.fixture",
            "request_ref": f"request.synthetic.{source['id']}",
        },
        "observed_at": "2026-10-01T12:00:00Z",
        "freshness_token": source["digest"],
        "scope": observed_scope,
        "coverage": {
            "completeness": source["completeness"],
            "observed_scope": observed_scope,
            "excluded_reasons": source["exclusions"],
            "absence_inference_allowed": False,
        },
        "limitations": source["limitations"],
        "source_representations": [{
            "representation_id": representation_id,
            "project_ref": project_ref,
            "source_artifact_ref": source["source_ref"],
            "source_version_ref": source["version_ref"],
            "source_kind": source["source_kind"],
            "identifiers": [source["identifier"]],
            "locators": [source["locator"]],
            "observed_at": "2026-10-01T12:00:00Z",
            "binding_ref": "binding.synthetic.qualification",
            "adapter_version": "0.0.fixture",
            "freshness_token": source["digest"],
            "coordinate_frame": source["coordinate_frame"],
            "proof_status": "candidate",
            "limitations": source["limitations"],
        }],
        "attribute_claim_candidates": [{
            "attribute_claim_id": f"claim.synthetic.{source['id']}",
            "subject_ref": {
                "entity_type": "source_representation",
                "entity_id": representation_id,
            },
            "attribute_key": claim["key"],
            "value": claim["value"],
            "assertion_mode": claim["assertion_mode"],
            "source_authority": claim["source_authority"],
            "proof_status": "candidate",
            "source_representation_refs": [representation_id],
            "validity": {"source_version_ref": source["version_ref"]},
        }],
        "relation_claim_candidates": [],
        "gaps": (
            [{"code": "measurement.metric_scale_unresolved"}]
            if source["id"] in {"dwg", "jpg"}
            else []
        ),
        "withheld": (
            [{"code": "measurement.metric_value_withheld"}]
            if source["id"] in {"dwg", "jpg"}
            else []
        ),
        "warnings": [],
        "operational_outcome": "success",
        "authority": {
            "is_fact": False,
            "is_evidence": False,
            "is_decision": False,
            "is_memory": False,
            "is_apu_write": False,
            "authorizes_external_effect": False,
        },
    }


@pytest.fixture(scope="module")
def sources() -> dict[str, dict]:
    corpus = _load(FIXTURE)
    assert corpus["status"] == "qualification_only"
    return {row["id"]: row for row in corpus["sources"]}


@pytest.mark.parametrize("kind", ["ifc", "dwg", "pdf", "jpg"])
def test_each_source_enters_existing_observation_bundle_candidate_schema(
    sources: dict[str, dict], kind: str
) -> None:
    project_ref = _load(FIXTURE)["project_ref"]
    bundle = _bundle(sources[kind], project_ref)
    errors = sorted(_validator().iter_errors(bundle), key=lambda e: tuple(map(str, e.path)))
    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]
    assert bundle["project_ref"] == project_ref
    assert bundle["source_representations"][0]["project_ref"] == project_ref
    assert bundle["coverage"]["absence_inference_allowed"] is False
    assert all(not flag for flag in bundle["authority"].values())
    assert all(item["proof_status"] == "candidate" for item in bundle["source_representations"])
    assert bundle["relation_claim_candidates"] == []


def test_each_format_keeps_native_locator_and_original_version(sources: dict[str, dict]) -> None:
    locators = {kind: row["locator"]["type"] for kind, row in sources.items()}
    assert locators == {"ifc": "ifc_guid", "dwg": "drawing_sheet", "pdf": "page_bbox", "jpg": "other"}
    coordinates = {kind: row["coordinate_frame"] for kind, row in sources.items()}
    assert coordinates == {"ifc": "MODEL_LOCAL", "dwg": "MODEL_LOCAL", "pdf": "PAGE", "jpg": "PIXEL"}
    assert len({row["source_ref"] for row in sources.values()}) == 4
    assert len({row["digest"] for row in sources.values()}) == 4
    for row in sources.values():
        bundle = _bundle(row, _load(FIXTURE)["project_ref"])
        assert bundle["basis"]["exact_digests"][0]["digest"] == row["digest"]
        assert bundle["attribute_claim_candidates"][0]["subject_ref"]["entity_type"] == "source_representation"


def test_dwg_jpg_cannot_invent_metric_values_or_physical_completion(sources: dict[str, dict]) -> None:
    dwg, photo = sources["dwg"], sources["jpg"]
    assert dwg["claim"]["key"] == "cad.layer"
    assert photo["claim"]["key"] == "physical.apparent_condition"
    assert all(row["claim"]["value"]["value_type"] != "number" for row in (dwg, photo))
    for row in (dwg, photo):
        bundle = _bundle(row, _load(FIXTURE)["project_ref"])
        assert bundle["coverage"]["completeness"] == "partial_for_declared_scope"
        assert {item["code"] for item in bundle["withheld"]} == {"measurement.metric_value_withheld"}
        assert not bundle["coverage"]["absence_inference_allowed"]
    assert "no_metric_calibration" in photo["exclusions"]
    assert "external_references_not_resolved" in dwg["exclusions"]


def test_no_universal_width_winner_or_automatic_identity_link(sources: dict[str, dict]) -> None:
    width_claims = [
        (row["id"], row["claim"]["value"]["value"], row["version_ref"])
        for row in sources.values()
        if row["claim"]["key"] == "geometry.width"
    ]
    assert width_claims == [
        ("ifc", 2.1, "ifc:snapshot-07"),
        ("pdf", 1.8, "drawing:index-b"),
    ]
    corpus = _load(FIXTURE)
    assert corpus["known_stable_object_ref"] == "OBJ-OPENING-004"
    # Being in the same affaire, or mentioning an opening, does NOT establish
    # identity.represents between an IFC GUID, CAD handle, sheet label and photo.
    assert all(
        not _bundle(row, corpus["project_ref"])["relation_claim_candidates"]
        for row in sources.values()
    )
    assert corpus["acceptance"]["no_winner_from_recency_or_agreement"] is True
    assert corpus["acceptance"]["common_project_is_not_automatic_identity_match"] is True


def test_mixed_phase_and_occupied_renovation_remain_independent_context() -> None:
    corpus = _load(FIXTURE)
    context = corpus["context"]
    assert context["extension"]["mission_phase"] == "esq"
    assert context["occupied_existing_building"]["mission_phase"] == "det"
    assert context["occupied_existing_building"]["occupancy"] == "occupied"
    assert context["priority_condition"] == "maintain_access_and_water_during_works"
    assert corpus["acceptance"]["occupied_site_priorities_may_override_esq_default"] is True
    assert corpus["acceptance"]["no_automatic_retain_or_apu_write"] is True


def test_fixture_does_not_claim_a_real_reader_or_verified_hindsight_memory(sources: dict[str, dict]) -> None:
    for row in sources.values():
        assert row["digest"].startswith("sha256:synthetic-")
        assert _bundle(row, _load(FIXTURE)["project_ref"])["method"]["adapter_ref"] == (
            "fixture.only.not_a_live_reader"
        )
    assert _load(FIXTURE)["acceptance"]["hindsight_memory_is_not_evidence"] is True
