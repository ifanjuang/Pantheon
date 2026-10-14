"""Behavior tests for targeted APU mapping reviews."""

from contextlib import nullcontext

import pytest

from mvp_vertical import apu_mapping_reviews, execution_results


EXECUTION = {
    "execution_result": {"execution_result_id": "execution.mapping.001"},
    "results": [
        {
            "result_id": "result.mapping.001",
            "result_kind": "apu_object_mapping",
            "payload": {
                "mappings": [
                    {
                        "mapping_id": "mapping.room.001",
                        "match_candidates": [
                            {"stable_object_ref": "space.room-a"},
                            {"stable_object_ref": "space.room-b"},
                        ],
                    }
                ]
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


def _patch_execution(monkeypatch):
    monkeypatch.setattr(
        execution_results,
        "get_execution_result",
        lambda _conn, _execution_result_id: EXECUTION,
    )
    monkeypatch.setattr(
        apu_mapping_reviews,
        "get_mapping_review",
        lambda _conn, review_id: {"review_id": review_id, "action": "select_existing_object"},
    )


def test_selection_must_reference_one_proposed_candidate(monkeypatch) -> None:
    _patch_execution(monkeypatch)
    with pytest.raises(apu_mapping_reviews.ApuMappingReviewError):
        apu_mapping_reviews.append_mapping_review(
            FakeConnection(),
            execution_result_id="execution.mapping.001",
            result_ref="result.mapping.001",
            mapping_ref="mapping.room.001",
            action="select_existing_object",
            selected_stable_object_ref="space.unknown",
            clarification_question=None,
            note=None,
            reviewer="human.ifj",
            idempotency_key="review-unknown",
        )


def test_valid_selection_records_only_review_event(monkeypatch) -> None:
    _patch_execution(monkeypatch)
    conn = FakeConnection()
    result = apu_mapping_reviews.append_mapping_review(
        conn,
        execution_result_id="execution.mapping.001",
        result_ref="result.mapping.001",
        mapping_ref="mapping.room.001",
        action="select_existing_object",
        selected_stable_object_ref="space.room-a",
        clarification_question=None,
        note="Sélection pour préparation.",
        reviewer="human.ifj",
        idempotency_key="review-room-a",
    )
    assert result["action"] == "select_existing_object"
    assert len(conn.statements) == 1
    statement = conn.statements[0][0]
    assert "INSERT INTO apu_mapping_review_events" in statement
    assert "INSERT INTO stable_objects" not in statement
    assert "INSERT INTO object_identity" not in statement


def test_clarification_requires_question(monkeypatch) -> None:
    _patch_execution(monkeypatch)
    with pytest.raises(apu_mapping_reviews.ApuMappingReviewError):
        apu_mapping_reviews.append_mapping_review(
            FakeConnection(),
            execution_result_id="execution.mapping.001",
            result_ref="result.mapping.001",
            mapping_ref="mapping.room.001",
            action="needs_clarification",
            selected_stable_object_ref=None,
            clarification_question=None,
            note=None,
            reviewer="human.ifj",
            idempotency_key="review-question",
        )
