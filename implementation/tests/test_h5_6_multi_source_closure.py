from __future__ import annotations

from contextlib import nullcontext
from copy import deepcopy

import pytest

from mvp_vertical import apu_write_preparation, execution_results
from mvp_vertical.project_anatomy_projection import build_project_anatomy_projection


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        return None

    def fetchone(self):
        return self._row


class _FakeConnection:
    """Enough connection for this unit check: a transaction and the command lock.

    `apply_authorized_write_command` takes the command row for update before it
    reads anything, so the sentinel this test used to pass no longer suffices.
    """

    def __init__(self, command_id: str) -> None:
        self._row = (command_id,)

    def transaction(self):
        return nullcontext()

    def cursor(self, **_kwargs):
        return _FakeCursor(self._row)



def _representation() -> dict:
    return {
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


def _relation() -> dict:
    return {
        "relation_claim_id": "identity.ifc.door-a.obj-door-017",
        "subject_ref": {
            "entity_type": "source_representation",
            "entity_id": "rep.ifc.door-a",
        },
        "relation_type": "identity.represents",
        "object_ref": {"entity_type": "stable_object", "entity_id": "OBJ-DOOR-017"},
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
        "certainty": "E3",
        "source_representation_refs": ["rep.ifc.door-a"],
        "notes": "IFC occurrence may represent the existing project door.",
    }


def _bundle_execution() -> dict:
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
                    "source_representations": [_representation()],
                    "attribute_claim_candidates": [],
                    "relation_claim_candidates": [_relation()],
                },
            }
        ],
    }


def _command() -> dict:
    payload = {
        "command_id": "apu-write-command.bundle.001",
        "operation": "add_match_to_existing_object",
        "project_ref": "project-1",
        "source_execution_result_ref": "execution.bundle.001",
        "source_mapping_result_ref": "result.bundle.001",
        "source_mapping_ref": "identity.ifc.door-a.obj-door-017",
        "source_review_ref": "review.bundle.001",
        "source_representation": _representation(),
        "identity_relation_claim": _relation(),
        "certainty": "E3",
        "expected_owner_revision": 7,
        "expected_object_revision": 3,
        "rationale": "IFC occurrence may represent the existing project door.",
        "prepared_by": "human:architect",
        "authority": dict(apu_write_preparation.COMMAND_AUTHORITY),
    }
    payload["payload_digest"] = apu_write_preparation._digest(payload)
    return payload


def test_candidate_identity_persisted_in_anatomy_is_visible_but_not_presented_as_mapped() -> None:
    anatomy = {
        "project_ref": "project-1",
        "model_version": 2,
        "model_authority_ref": "contracts@baseline",
        "owner_revision": 8,
        "stable_objects": [
            {
                "object_id": "OBJ-DOOR-017",
                "stable_object": {
                    "stable_object_id": "OBJ-DOOR-017",
                    "project_ref": "project-1",
                    "object_family": "element",
                    "nomenclature": {"display_name": "Door 017"},
                },
                "revision": 3,
            }
        ],
        "source_representations": [_representation()],
        "attribute_claims": [],
        "relation_claims": [_relation()],
        "authority": {
            "is_projection": True,
            "is_evidence": False,
            "is_decision": False,
            "authorizes_tasks": False,
            "permits_runtime_writes": False,
        },
    }

    projection = build_project_anatomy_projection(
        anatomy,
        model_doctrine_ref="doctrine@baseline",
    )

    source = projection["sources"][0]
    assert source["identity_claims"][0]["claim_id"] == _relation()["relation_claim_id"]
    assert source["identity_claims"][0]["proof_status"] == "candidate"
    assert source["mapped_object_refs"] == []
    assert projection["unmapped_material"][0]["representation_id"] == "rep.ifc.door-a"
    assert projection["authority"]["authorization_inferred"] is False
    assert projection["authority"]["absence_inferred"] is False


def test_application_refuses_changed_observation_bundle_source_after_preparation(monkeypatch) -> None:
    command = _command()
    command_row = {
        "command_id": command["command_id"],
        "payload_digest": command["payload_digest"],
        "expected_owner_revision": 7,
        "expected_object_revision": 3,
        "target_stable_object_ref": "OBJ-DOOR-017",
        "source_candidate_ref": "rep.ifc.door-a",
        "source_artifact_ref": "ifc:model-a",
        "command": command,
    }
    changed = deepcopy(_bundle_execution())
    changed["results"][0]["payload"]["source_representations"][0]["content_digest"] = (
        "sha256:" + "d" * 64
    )

    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, _command_id: command_row,
    )
    monkeypatch.setattr(
        execution_results,
        "get_execution_result",
        lambda _conn, _execution_id: changed,
    )

    with pytest.raises(
        apu_write_preparation.ApuWriteApplicationConflict,
        match="source representation changed after command preparation",
    ):
        apu_write_preparation.apply_authorized_write_command(
            _FakeConnection(command["command_id"]),
            command_id=command["command_id"],
            applied_by="human:architect",
            idempotency_key="apply-stale-bundle",
        )
