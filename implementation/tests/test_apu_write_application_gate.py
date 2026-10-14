"""Unit tests for the APU command/review/authorization application gate."""

from __future__ import annotations

from copy import deepcopy
from contextlib import nullcontext

import pytest

from mvp_vertical import (
    apu_owner,
    apu_write_preparation,
    execution_results,
)


class _FakeCursor:
    def __init__(self, connection):
        self._connection = connection
        self._last = ""

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        self._last = " ".join(sql.split())
        self._connection.statements.append((self._last, params))

    def fetchone(self):
        # Answers the command-row lock and nothing else: an idempotency lookup
        # that came back with the lock's row would make the fake, not the code,
        # decide what happens next.
        return self._connection.row if "FOR UPDATE" in self._last else None


class _FakeConnection:
    """Enough connection for the unit gate: a transaction and the command lock.

    These tests passed `object()` while nothing in the chain touched the
    connection. Both write paths now take the command row for update before
    they read or write the decision, which is the repair — so the fake records
    what it was asked to run and the tests assert the lock is there, and first.
    """

    def __init__(self, command_id: str = "command-1") -> None:
        self.statements: list[tuple[str, object]] = []
        self.row: tuple[str, ...] = (command_id,)

    def transaction(self):
        return nullcontext()

    def cursor(self, **_kwargs):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        self.statements.append((" ".join(sql.split()), params))


def _lock_statement(command_id: str) -> tuple[str, object]:
    return (
        "SELECT command_id FROM apu_write_command_candidates"
        " WHERE command_id = %s FOR UPDATE",
        (command_id,),
    )


EXECUTION = {
    "execution_result": {"execution_result_id": "execution.mapping.001"},
    "results": [
        {
            "result_id": "result.mapping.001",
            "result_kind": "apu_object_mapping",
            "payload": {
                "project_ref": "project-1",
                "document_ref": "document-1",
                "structure_ref": "structure.001",
                "mappings": [
                    {
                        "mapping_id": "mapping.room.001",
                        "fragment_ref": "fragment.room.001",
                        "candidate_object_ref": "candidate.room.001",
                        "certainty": "E3",
                        "rationale": "Le fragment peut correspondre à l'espace existant.",
                        "match_candidates": [
                            {"stable_object_ref": "space.room-a"},
                            {"stable_object_ref": "space.room-b"},
                        ],
                    }
                ],
            },
        }
    ],
}
REVIEW = {
    "review_id": "review.mapping.001",
    "action": "select_existing_object",
    "selected_stable_object_ref": "space.room-a",
}


def _source_representation() -> dict:
    return {
        "representation_id": "candidate.room.001",
        "project_ref": "project-1",
        "source_artifact_ref": "document-1",
        "source_version_ref": "sha256:" + "a" * 64,
        "source_kind": "other",
        "identifiers": [
            {"scheme": "pantheon.document.fragment", "value": "fragment.room.001"},
            {"scheme": "pantheon.document.structure", "value": "structure.001"},
        ],
        "observed_at": "2026-08-09T09:00:00Z",
        "binding_ref": "pantheon-mvp.document-structure:test",
        "adapter_version": "1",
        "freshness_token": "sha256:" + "b" * 64,
        "content_digest": "sha256:" + "c" * 64,
        "proof_status": "candidate",
        "limitations": [
            "Document Structure fragment candidate; stable project identity is not established."
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


def _command() -> dict:
    payload = {
        "command_id": "apu-write-command.001",
        "operation": "add_match_to_existing_object",
        "project_ref": "project-1",
        "source_execution_result_ref": "execution.mapping.001",
        "source_mapping_result_ref": "result.mapping.001",
        "source_mapping_ref": "mapping.room.001",
        "source_review_ref": "review.mapping.001",
        "certainty": "E3",
        "expected_owner_revision": 4,
        "expected_object_revision": 2,
        "rationale": "Le fragment peut correspondre à l'espace existant.",
        "prepared_by": "human:architect",
        "limitations": [
            "Une autorisation humaine distincte est requise avant toute application.",
            "L'application doit refuser une révision APU ou objet devenue obsolète.",
        ],
        "authority": dict(apu_write_preparation.COMMAND_AUTHORITY),
    }
    payload["source_representation"] = _source_representation()
    payload["identity_relation_claim"] = apu_write_preparation._identity_relation_claim(
        command_id=payload["command_id"],
        source_execution_result_ref=payload["source_execution_result_ref"],
        source_mapping_result_ref=payload["source_mapping_result_ref"],
        source_mapping_ref=payload["source_mapping_ref"],
        source_review_ref=payload["source_review_ref"],
        source_representation_ref=payload["source_representation"]["representation_id"],
        target_stable_object_ref="space.room-a",
        certainty=payload["certainty"],
        rationale=payload["rationale"],
    )
    payload["payload_digest"] = apu_write_preparation._digest(payload)
    return payload


def _command_row(command: dict) -> dict:
    return {
        "command_id": command["command_id"],
        "payload_digest": command["payload_digest"],
        "expected_owner_revision": command["expected_owner_revision"],
        "expected_object_revision": command["expected_object_revision"],
        "target_stable_object_ref": command["identity_relation_claim"]["object_ref"]["entity_id"],
        "source_candidate_ref": command["source_representation"]["representation_id"],
        "source_artifact_ref": command["source_representation"]["source_artifact_ref"],
        "command": command,
    }


def test_prepare_captures_owner_and_object_revisions(monkeypatch) -> None:
    monkeypatch.setattr(
        execution_results,
        "get_execution_result",
        lambda _conn, _execution_id: EXECUTION,
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_document_fragment_source_representation",
        lambda *_args, **_kwargs: _source_representation(),
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_selected_review",
        lambda *_args, **_kwargs: REVIEW,
    )
    monkeypatch.setattr(
        apu_owner,
        "get_project_anatomy",
        lambda _conn, *, project_id: {"project_ref": project_id, "owner_revision": 4},
    )
    monkeypatch.setattr(
        apu_owner,
        "get_apu_object",
        lambda _conn, *, project_id, object_id: {
            "project_ref": project_id,
            "object_id": object_id,
            "revision": 2,
            "retired_at": None,
        },
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, command_id: {"command_id": command_id},
    )
    conn = FakeConnection()

    apu_write_preparation.prepare_write_command(
        conn,
        execution_result_id="execution.mapping.001",
        result_ref="result.mapping.001",
        mapping_ref="mapping.room.001",
        prepared_by="human:architect",
        idempotency_key="prepare-1",
    )

    insert = next(item for item in conn.statements if "INSERT INTO apu_write_command_candidates" in item[0])
    params = insert[1]
    assert params[14] == 4
    assert params[15] == 2
    command_payload = params[12]
    value = command_payload.obj if hasattr(command_payload, "obj") else command_payload
    assert value["expected_owner_revision"] == 4
    assert value["expected_object_revision"] == 2
    assert "target_model_version" not in value
    assert "target_stable_object_ref" not in value
    assert "source_candidate_ref" not in value
    assert "source_artifact_ref" not in value
    assert value["source_representation"] == _source_representation()


def test_prepare_carries_exact_candidate_source_and_identity_relation(monkeypatch) -> None:
    execution = deepcopy(EXECUTION)
    execution["results"][0]["payload"]["structure_ref"] = "structure.001"
    execution["results"][0]["payload"]["mappings"][0]["fragment_ref"] = (
        "fragment.room.001"
    )
    monkeypatch.setattr(
        execution_results,
        "get_execution_result",
        lambda _conn, _execution_id: execution,
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_selected_review",
        lambda *_args, **_kwargs: REVIEW,
    )
    monkeypatch.setattr(
        apu_owner,
        "get_project_anatomy",
        lambda _conn, *, project_id: {
            "project_ref": project_id,
            "model_version": 2,
            "owner_revision": 4,
        },
    )
    monkeypatch.setattr(
        apu_owner,
        "get_apu_object",
        lambda _conn, *, project_id, object_id: {
            "project_ref": project_id,
            "object_id": object_id,
            "revision": 2,
            "retired_at": None,
        },
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_document_fragment_source_representation",
        lambda *_args, **_kwargs: _source_representation(),
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, command_id: {"command_id": command_id},
    )
    conn = FakeConnection()

    apu_write_preparation.prepare_write_command(
        conn,
        execution_result_id="execution.mapping.001",
        result_ref="result.mapping.001",
        mapping_ref="mapping.room.001",
        prepared_by="human:architect",
        idempotency_key="prepare-canonical",
    )

    insert = next(
        item
        for item in conn.statements
        if "INSERT INTO apu_write_command_candidates" in item[0]
    )
    command_payload = insert[1][12]
    command = (
        command_payload.obj if hasattr(command_payload, "obj") else command_payload
    )
    relation = command["identity_relation_claim"]
    assert "target_model_version" not in command
    assert command["source_representation"] == _source_representation()
    assert relation["relation_type"] == "identity.represents"
    assert relation["subject_ref"] == {
        "entity_type": "source_representation",
        "entity_id": "candidate.room.001",
    }
    assert relation["object_ref"] == {
        "entity_type": "stable_object",
        "entity_id": "space.room-a",
    }
    assert relation["assertion_mode"] == "proposed"
    assert relation["source_authority"] == "model_interpretation_candidate"
    assert relation["proof_status"] == "candidate"
    assert relation["certainty"] == "E3"


def test_effect_reuses_one_owner_and_keeps_identity_candidate() -> None:
    command = _command()

    apu_write_preparation._validate_command_payload(command)
    representation, relation = apu_owner._source_match_effect(
        command,
        project_id="project-1",
        object_id="space.room-a",
    )

    assert representation == command["source_representation"]
    assert relation == command["identity_relation_claim"]
    assert representation["proof_status"] == "candidate"
    assert relation["proof_status"] == "candidate"


def test_owner_refuses_effect_targeting_another_object() -> None:
    command = _command()
    command["identity_relation_claim"]["object_ref"]["entity_id"] = "space.room-b"
    command["payload_digest"] = apu_write_preparation._digest(
        {key: value for key, value in command.items() if key != "payload_digest"}
    )
    with pytest.raises(
        apu_owner.ApuOwnerError,
        match="must target the selected stable object",
    ):
        apu_owner._source_match_effect(
            command,
            project_id="project-1",
            object_id="space.room-a",
        )


def test_application_revalidates_review_authorization_and_candidate_membership(monkeypatch) -> None:
    command = _command()
    command_row = _command_row(command)
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, _command_id: command_row,
    )
    monkeypatch.setattr(
        execution_results,
        "get_execution_result",
        lambda _conn, _execution_id: EXECUTION,
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_selected_review",
        lambda *_args, **_kwargs: REVIEW,
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_application_authorization",
        lambda _conn, _command: {
            "authorization_id": "authorization-1",
            "action": "authorize_application",
            "command_payload_digest": command["payload_digest"],
        },
    )
    called = {}

    def apply(_conn, **kwargs):
        called.update(kwargs)
        return {"status": "applied", "authority": dict(apu_owner.APPLICATION_AUTHORITY)}

    monkeypatch.setattr(apu_owner, "apply_source_match", apply)
    connection = _FakeConnection(command["command_id"])
    result = apu_write_preparation.apply_authorized_write_command(
        connection,
        command_id=command["command_id"],
        applied_by="human:architect",
        idempotency_key="apply-1",
    )
    assert result["status"] == "applied"
    assert connection.statements == [
        _lock_statement(command["command_id"])
    ], "the apply path must take the command row before it reads the decision"
    assert called["command"] == command
    assert called["authorization_id"] == "authorization-1"
    assert called["actor"] == "human:architect"


def test_application_refuses_superseded_review(monkeypatch) -> None:
    command = _command()
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, _command_id: _command_row(command),
    )
    monkeypatch.setattr(
        execution_results,
        "get_execution_result",
        lambda _conn, _execution_id: EXECUTION,
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "_latest_selected_review",
        lambda *_args, **_kwargs: REVIEW | {"review_id": "review.mapping.newer"},
    )
    connection = _FakeConnection(command["command_id"])
    with pytest.raises(
        apu_write_preparation.ApuWriteApplicationConflict,
        match="newer mapping review",
    ):
        apu_write_preparation.apply_authorized_write_command(
            connection,
            command_id=command["command_id"],
            applied_by="human:architect",
            idempotency_key="apply-stale-review",
        )


def test_application_refuses_tampered_command_digest(monkeypatch) -> None:
    command = _command()
    command["rationale"] = "Contenu modifié après autorisation."
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, _command_id: _command_row(command),
    )
    connection = _FakeConnection(command["command_id"])
    with pytest.raises(
        apu_write_preparation.ApuWriteApplicationConflict,
        match="digest",
    ):
        apu_write_preparation.apply_authorized_write_command(
            connection,
            command_id=command["command_id"],
            applied_by="human:architect",
            idempotency_key="apply-tampered",
        )


def test_appending_an_authorization_takes_the_same_command_row(monkeypatch) -> None:
    """A lock orders nothing unless both writers take it.

    The apply path re-reads the decision under the command row. A rejection
    appended without taking that row would still be free to commit inside the
    very window the re-read was added to close, so this asserts the other half
    — and that the lock comes before the event is written, not after.
    """
    command = _command()
    monkeypatch.setattr(
        apu_write_preparation,
        "get_write_command",
        lambda _conn, _command_id: _command_row(command),
    )
    monkeypatch.setattr(
        apu_write_preparation,
        "get_authorization",
        lambda _conn, authorization_id: {"authorization_id": authorization_id},
    )
    connection = _FakeConnection(command["command_id"])
    apu_write_preparation.append_authorization(
        connection,
        command_id=command["command_id"],
        action="reject_application",
        note="Rejeté après revue.",
        authorized_by="human:architect",
        idempotency_key="reject-1",
    )
    assert connection.statements[0] == _lock_statement(command["command_id"])
    written = [
        index
        for index, (sql, _params) in enumerate(connection.statements)
        if "INSERT INTO apu_write_authorization_events" in sql
    ]
    assert written == [len(connection.statements) - 1], (
        "the rejection must be written after the command row is held, once"
    )


def test_latest_rejection_blocks_application(monkeypatch) -> None:
    command = _command()
    monkeypatch.setattr(
        apu_write_preparation,
        "list_authorizations",
        lambda _conn, _command_id: [
            {
                "authorization_id": "authorization-reject",
                "action": "reject_application",
                "command_payload_digest": command["payload_digest"],
            }
        ],
    )
    with pytest.raises(
        apu_write_preparation.ApuWritePreparationError,
        match="authorize_application",
    ):
        apu_write_preparation._latest_application_authorization(object(), command)
