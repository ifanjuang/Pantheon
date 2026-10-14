from __future__ import annotations

from contextlib import nullcontext
from copy import deepcopy

import pytest

from mvp_vertical import apu_mapping_reviews, apu_owner, apu_write_preparation, execution_results


def _bundle_execution() -> dict:
    representation = {
        "representation_id": "rep.ifc.door-a",
        "project_ref": "project-1",
        "source_artifact_ref": "ifc:model-a",
        "source_version_ref": "sha256:" + "a" * 64,
        "source_kind": "ifc",
        "identifiers": [{"scheme": "ifc_guid", "value": "3DoorGuid"}],
        "observed_at": "2026-08-09T12:00:00Z",
        "binding_ref": "binding.ifc.test",
        "adapter_version": "1.0.0",
        "freshness_token": "sha256:" + "b" * 64,
        "content_digest": "sha256:" + "c" * 64,
        "proof_status": "candidate",
    }
    relation = {
        "relation_claim_id": "identity.ifc.door-a.obj-door-017",
        "subject_ref": {"entity_type": "source_representation", "entity_id": representation["representation_id"]},
        "relation_type": "identity.represents",
        "object_ref": {"entity_type": "stable_object", "entity_id": "OBJ-DOOR-017"},
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
        "certainty": "E3",
        "source_representation_refs": [representation["representation_id"]],
        "notes": "IFC occurrence may represent the existing project door.",
    }
    return {
        "execution_result": {
            "execution_result_id": "execution.bundle.001",
            "task_contract_ref": "task-contract.observe.ifc",
            "project_ref": "project-1",
        },
        "results": [
            {
                "result_id": "result.bundle.001",
                "result_kind": "observation_bundle",
                "payload": {
                    "project_ref": "project-1",
                    "source_representations": [representation],
                    "attribute_claim_candidates": [
                        {
                            "attribute_claim_id": "claim.ifc.width",
                            "subject_ref": {"entity_type": "source_representation", "entity_id": representation["representation_id"]},
                            "attribute_key": "geometry.width",
                            "value": {"value_type": "number", "value": 0.93},
                            "assertion_mode": "derived",
                            "source_authority": "model_interpretation_candidate",
                            "proof_status": "candidate",
                            "certainty": "E3",
                            "source_representation_refs": [representation["representation_id"]],
                        }
                    ],
                    "relation_claim_candidates": [relation],
                },
            }
        ],
    }


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_args, **_kwargs):
        return self

    def fetchone(self):
        return None


class FakeConnection:
    def __init__(self):
        self.statements = []

    def transaction(self):
        return nullcontext()

    def cursor(self, **_kwargs):
        return FakeCursor()

    def execute(self, statement, params=None):
        self.statements.append((statement, params))


def test_mapping_review_accepts_exact_observation_bundle_identity_candidate(monkeypatch) -> None:
    execution = _bundle_execution()
    monkeypatch.setattr(execution_results, "get_execution_result", lambda _conn, _id: execution)
    mapping = apu_mapping_reviews._mapping_candidate(
        execution,
        "result.bundle.001",
        "identity.ifc.door-a.obj-door-017",
    )
    assert mapping["candidate_object_ref"] == "rep.ifc.door-a"
    assert mapping["match_candidates"][0]["stable_object_ref"] == "OBJ-DOOR-017"
    assert mapping["source_relation_claim"]["proof_status"] == "candidate"


def test_write_preparation_uses_exact_bundle_representation_and_relation(monkeypatch) -> None:
    execution = _bundle_execution()
    relation = execution["results"][0]["payload"]["relation_claim_candidates"][0]
    representation = execution["results"][0]["payload"]["source_representations"][0]
    monkeypatch.setattr(execution_results, "get_execution_result", lambda _conn, _id: execution)
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_selected_review",
        lambda *_args, **_kwargs: {
            "review_id": "review.bundle.001",
            "action": "select_existing_object",
            "selected_stable_object_ref": "OBJ-DOOR-017",
        },
    )
    monkeypatch.setattr(
        apu_owner,
        "get_project_anatomy",
        lambda _conn, *, project_id: {"project_ref": project_id, "owner_revision": 7},
    )
    monkeypatch.setattr(
        apu_owner,
        "get_apu_object",
        lambda _conn, *, project_id, object_id: {
            "project_ref": project_id,
            "object_id": object_id,
            "revision": 3,
            "retired_at": None,
        },
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, command_id: {"command_id": command_id},
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_document_fragment_source_representation",
        lambda *_args, **_kwargs: pytest.fail("Observation Bundle path must not reconstruct Document Structure"),
    )
    conn = FakeConnection()

    apu_write_preparation.prepare_write_command(
        conn,
        execution_result_id="execution.bundle.001",
        result_ref="result.bundle.001",
        mapping_ref="identity.ifc.door-a.obj-door-017",
        prepared_by="human:architect",
        idempotency_key="prepare-bundle-ifc",
    )

    insert = next(item for item in conn.statements if "INSERT INTO apu_write_command_candidates" in item[0])
    command_jsonb = insert[1][12]
    command = command_jsonb.obj if hasattr(command_jsonb, "obj") else command_jsonb
    assert command["source_representation"] == representation
    assert command["identity_relation_claim"] == relation
    assert command["expected_owner_revision"] == 7
    assert command["expected_object_revision"] == 3
    assert command["identity_relation_claim"]["proof_status"] == "candidate"
    assert command["source_representation"]["proof_status"] == "candidate"
    assert execution["results"][0]["payload"]["attribute_claim_candidates"][0]["attribute_claim_id"] not in str(command)


def test_rejected_or_clarification_bundle_candidate_cannot_prepare_write(monkeypatch) -> None:
    execution = _bundle_execution()
    monkeypatch.setattr(execution_results, "get_execution_result", lambda _conn, _id: execution)
    for action in ("reject_mapping", "needs_clarification"):
        monkeypatch.setattr(
            apu_mapping_reviews,
            "list_mapping_reviews",
            lambda *_args, _action=action, **_kwargs: [{"review_id": "review.1", "action": _action}],
        )
        with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="select_existing_object"):
            apu_write_preparation._latest_selected_review(
                object(),
                execution_result_id="execution.bundle.001",
                result_ref="result.bundle.001",
                mapping_ref="identity.ifc.door-a.obj-door-017",
            )


def test_changed_bundle_identity_target_is_refused_at_preparation(monkeypatch) -> None:
    execution = _bundle_execution()
    changed = deepcopy(execution)
    changed["results"][0]["payload"]["relation_claim_candidates"][0]["object_ref"]["entity_id"] = "OBJ-DOOR-099"
    monkeypatch.setattr(execution_results, "get_execution_result", lambda _conn, _id: changed)
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_selected_review",
        lambda *_args, **_kwargs: {
            "review_id": "review.bundle.001",
            "action": "select_existing_object",
            "selected_stable_object_ref": "OBJ-DOOR-017",
        },
    )
    monkeypatch.setattr(
        apu_owner,
        "get_project_anatomy",
        lambda _conn, *, project_id: {"project_ref": project_id, "owner_revision": 7},
    )
    monkeypatch.setattr(
        apu_owner,
        "get_apu_object",
        lambda _conn, *, project_id, object_id: {
            "project_ref": project_id,
            "object_id": object_id,
            "revision": 3,
            "retired_at": None,
        },
    )
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="no longer present"):
        apu_write_preparation.prepare_write_command(
            FakeConnection(),
            execution_result_id="execution.bundle.001",
            result_ref="result.bundle.001",
            mapping_ref="identity.ifc.door-a.obj-door-017",
            prepared_by="human:architect",
            idempotency_key="prepare-stale-bundle",
        )
