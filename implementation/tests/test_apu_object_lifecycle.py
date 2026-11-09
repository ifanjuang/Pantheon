"""Objects follow the project: added or retired at a new index, through the reviewed chain.

A new index of a drawing or a model may show an object the Project Anatomy does
not know yet, or no longer show one it knows. Both become Observation Bundle
candidates: a new-object candidate (the object and the occurrence observing it)
and a retirement candidate (absence is a reason to propose, never a proof). Each
goes review -> write command -> human authorization -> application, and the
batch applies new objects before the claims that name them. A retired object is
kept with its history; it is no longer current.
"""

from __future__ import annotations

import pytest

from mvp_vertical import apu_batch, apu_mapping_reviews, apu_owner, apu_write_preparation, execution_results
from test_apu_progressive_claims import (  # noqa: F401 - conn is a fixture
    DOOR,
    REP,
    WALL,
    _id,
    _import,
    _project,
    _width,
    conn,
)

WINDOW = "OBJ-WINDOW-021"
REP_C = "rep.drawing.window-021.t2"
HUMAN = "human:architect"


def _representation(project_id: str) -> dict:
    return {
        "representation_id": REP_C,
        "project_ref": project_id,
        "source_artifact_ref": "source.pdf.a101",
        "source_version_ref": "drawing:a101:index-c",
        "source_kind": "drawing",
        "identifiers": [{"scheme": "drawing.local_label", "value": "F21"}],
        "observed_at": "2026-04-02T09:00:00Z",
        "binding_ref": "binding.synthetic.drawing",
        "adapter_version": "1.0.0",
        "freshness_token": "sha256:a101-c",
        "content_digest": "sha256:a101-f21",
        "proof_status": "candidate",
    }


def _window(project_id: str) -> dict:
    return {
        "object_candidate_id": "candidate.window-021",
        "stable_object": {
            "stable_object_id": WINDOW,
            "project_ref": project_id,
            "object_family": "element",
            "nomenclature": {"internal_code": "F21", "display_name": "Fenêtre cuisine"},
        },
        "source_representation_ref": REP_C,
        "certainty": "E3",
        "rationale": "La fenêtre F21 apparaît à l'indice C.",
    }


def _retire_wall() -> dict:
    return {
        "retirement_candidate_id": "candidate.retire-wall-004",
        "stable_object_ref": WALL,
        "reason": "Mur absent de l'indice C, qui couvre tout le niveau.",
        "evidence_refs": [REP_C],
        "rationale": "Démolition prévue au plan MAC-DEM indice C.",
    }


def _bundle(conn, project_id: str, *, objects=(), claims=(), retirements=(), representations=()) -> tuple[str, str]:
    execution_id, result_id = _id("execution-lifecycle"), _id("result-lifecycle")
    payload = {
        "observation_bundle_id": _id("observation-bundle"),
        "project_ref": project_id,
        "task_contract_ref": "task-contract:lifecycle",
        "basis": {
            "source_artifact_refs": ["source.pdf.a101"],
            "source_version_refs": ["drawing:a101:index-c"],
            "exact_digests": [{"source_artifact_ref": "source.pdf.a101",
                               "source_version_ref": "drawing:a101:index-c", "digest": "sha256:a101-c"}],
        },
        "method": {"capability_id": "drawing.observe.objects", "binding_id": "binding.synthetic.drawing",
                   "operation_id": "drawing.observe.objects.v1", "adapter_ref": "pantheon.synthetic.drawing",
                   "adapter_version": "1.0.0", "request_ref": "request:lifecycle"},
        "observed_at": "2026-04-02T09:00:00Z",
        "freshness_token": "sha256:a101-c",
        "scope": {"document_refs": ["drawing:a101"]},
        "coverage": {"completeness": "partial_for_declared_scope", "observed_scope": {"document_refs": ["drawing:a101"]},
                     "excluded_reasons": [], "absence_inference_allowed": False},
        "limitations": ["Synthetic lifecycle bundle."],
        "source_representations": list(representations),
        "object_candidates": list(objects),
        "attribute_claim_candidates": list(claims),
        "relation_claim_candidates": [],
        "retirement_candidates": list(retirements),
        "gaps": [], "withheld": [], "warnings": [], "operational_outcome": "success",
        "authority": {"is_fact": False, "is_evidence": False, "is_decision": False, "is_memory": False,
                      "is_apu_write": False, "authorizes_external_effect": False},
    }
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id, "task_contract_ref": "task-contract:lifecycle",
            "project_ref": project_id, "producer": {"kind": "fixture", "version": "1"},
            "produced_at": "2026-04-02T09:00:00Z", "authority": dict(execution_results.AUTHORITY),
            "results": [{"result_id": result_id, "result_kind": "observation_bundle",
                         "schema_ref": execution_results.OBSERVATION_BUNDLE_SCHEMA_REF, "payload": payload}],
            "clarification_requests": [],
        },
        idempotency_key=_id("bundle"),
    )
    return execution_id, result_id


def _batch(conn, execution_id, result_id, reject=None):
    digest = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id, reject=reject)["batch_digest"]
    return apu_batch.apply_batch(conn, execution_result_id=execution_id, result_ref=result_id, batch_digest=digest,
                                 reviewer=HUMAN, authorized_by=HUMAN, applied_by="system:test", reject=reject)


def _events(conn, project_id: str) -> list[str]:
    rows = conn.execute("SELECT event_type FROM agency_apu_events WHERE project_id = %s ORDER BY resulting_revision", (project_id,)).fetchall()
    return [row[0] for row in rows]


def test_an_index_adds_an_object_and_its_values_in_one_batch(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    width = {**_width("claim.window.width.t2", 1.2, source_representation_refs=[REP_C]),
             "subject_ref": {"entity_type": "stable_object", "entity_id": WINDOW}}
    execution_id, result_id = _bundle(conn, project_id, objects=[_window(project_id)], claims=[width],
                                      representations=[_representation(project_id)])
    preview = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)
    assert [apu_batch.preview_row(item)["change"] for item in preview["items"]] == ["+ objet", "+ valeur"]

    result = _batch(conn, execution_id, result_id)
    assert result["applied"] == ["candidate.window-021", "claim.window.width.t2"]
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert WINDOW in {item["object_id"] for item in anatomy["stable_objects"]}
    assert "claim.window.width.t2" in {item["attribute_claim_id"] for item in anatomy["attribute_claims"]}
    identity = [r for r in anatomy["relation_claims"] if r["relation_type"] == "identity.represents"
                and r["object_ref"]["entity_id"] == WINDOW]
    assert identity and identity[0]["proof_status"] == "candidate"
    assert _events(conn, project_id)[-2:] == ["object_added", "claim_added"]


def test_a_retirement_keeps_the_object_and_its_history(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, retirements=[_retire_wall()])
    assert _batch(conn, execution_id, result_id)["applied"] == ["candidate.retire-wall-004"]

    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert WALL not in {item["object_id"] for item in anatomy["stable_objects"]}
    wall = apu_owner.get_apu_object(conn, project_id=project_id, object_id=WALL)
    assert wall["retired_at"] is not None and wall["revision"] == 2
    assert _events(conn, project_id)[-1] == "object_retired"
    # A retired object takes no new claim.
    claim = {**_width("claim.wall.width.t2", 0.2, source_representation_refs=[REP]),
             "subject_ref": {"entity_type": "stable_object", "entity_id": WALL}}
    execution_id, result_id = _bundle(conn, project_id, claims=[claim])
    with pytest.raises(Exception):
        _batch(conn, execution_id, result_id)


def test_absence_is_never_retired_without_acceptance(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, retirements=[_retire_wall()])
    result = _batch(conn, execution_id, result_id, reject=["candidate.retire-wall-004"])
    assert (result["applied"], result["rejected"]) == ([], ["candidate.retire-wall-004"])
    assert apu_owner.get_apu_object(conn, project_id=project_id, object_id=WALL)["retired_at"] is None


def test_review_actions_follow_the_lifecycle_candidate_kind(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, objects=[_window(project_id)], retirements=[_retire_wall()],
                                      representations=[_representation(project_id)])
    review = dict(execution_result_id=execution_id, result_ref=result_id, selected_stable_object_ref=None,
                  clarification_question=None, note=None, reviewer=HUMAN)
    with pytest.raises(apu_mapping_reviews.ApuMappingReviewError, match="object candidate"):
        apu_mapping_reviews.append_mapping_review(conn, mapping_ref="candidate.window-021",
                                                  action="accept_claim_candidate", idempotency_key=_id("r"), **review)
    with pytest.raises(apu_mapping_reviews.ApuMappingReviewError, match="retirement candidate"):
        apu_mapping_reviews.append_mapping_review(conn, mapping_ref="candidate.retire-wall-004",
                                                  action="accept_object_candidate", idempotency_key=_id("r"), **review)
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="accept_retirement"):
        apu_write_preparation.prepare_write_command(conn, execution_result_id=execution_id, result_ref=result_id,
                                                    mapping_ref="candidate.retire-wall-004", prepared_by="system:test",
                                                    idempotency_key=_id("p"))


def test_adding_an_object_that_already_exists_is_refused_and_leaves_nothing(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    duplicate = _window(project_id)
    duplicate["stable_object"] = {**duplicate["stable_object"], "stable_object_id": DOOR}
    execution_id, result_id = _bundle(conn, project_id, objects=[duplicate], representations=[_representation(project_id)])
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="already exists"):
        _batch(conn, execution_id, result_id)
    assert apu_owner.get_project_anatomy(conn, project_id=project_id)["owner_revision"] == 1


def test_an_object_candidate_needs_its_occurrence_in_the_bundle(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, objects=[_window(project_id)])
    with pytest.raises(apu_mapping_reviews.ApuMappingReviewError, match="unknown source representation"):
        apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)
