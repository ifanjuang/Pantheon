from __future__ import annotations

import pytest

from mvp_vertical import (
    agency_data,
    apu_object_read,
    apu_owner,
    hermes_execution,
    hermes_handoff_store,
    store,
    work_issues,
)
from mvp_vertical.hermes_live_acceptance import CONTEXT_TOOLS, SYNTHETIC_MARKER
from tools import p2_live_admission_preparer as p2


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    for migration in hermes_execution.MIGRATIONS:
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.commit()
    yield connection
    connection.close()


def _prepare(conn, variant: str) -> dict:
    return p2.prepare_p2_live_admission(
        conn,
        variant=variant,
        actor="human:p2-test",
        ack="SYNTHETIC_ONLY",
        ttl_seconds=900,
    )


def _assert_live_guard_shape(conn, receipt: dict) -> dict:
    assert receipt["synthetic"] is True
    assert receipt["execution_started"] is False
    assert receipt["hermes_run_created"] is False
    assert receipt["technical_receipt_is_evidence"] is False
    assert receipt["production_authorization"] is False
    assert receipt["admission_state"] == "admitted"
    assert "synthetic" in receipt["project_id"]
    assert SYNTHETIC_MARKER in receipt["question"]
    for tool in CONTEXT_TOOLS:
        assert tool in receipt["question"]

    handoff = hermes_handoff_store.get_handoff_snapshot(conn, receipt["handoff_id"])
    assert handoff["question"] == receipt["question"] == p2.LIVE_QUESTION
    assert handoff["context_pack"]["root_entity"]["entity_type"] == "project"
    assert "synthetic" in handoff["context_pack"]["root_entity"]["entity_id"]

    run_count = conn.execute(
        "SELECT COUNT(*) FROM hermes_runs WHERE admission_ref = %s",
        (receipt["admission_id"],),
    ).fetchone()[0]
    assert run_count == 0
    return handoff


def _candidate_records(conn, receipt: dict) -> list[dict]:
    ambiguity = receipt["identity_ambiguity"]
    assert ambiguity is not None
    records = []
    for ref in ambiguity["candidate_target_refs"]:
        assert ref["entity_type"] == "stable_object"
        records.append(
            apu_object_read.get_stable_object_context(
                conn,
                object_id=ref["entity_id"].removeprefix("stable_object:"),
            )
        )
    return records


def _thicknesses(record: dict) -> list[float]:
    return [
        claim["value"]["value"]
        for claim in record["attribute_claims"]
        if claim["attribute_key"] == "geometry.thickness"
    ]


def test_ack_is_required_before_any_fixture_state(monkeypatch) -> None:
    def forbidden_scenario(*_args, **_kwargs):
        pytest.fail("scenario creation must not run without SYNTHETIC_ONLY acknowledgement")

    monkeypatch.setattr(p2, "_scenario", forbidden_scenario)
    with pytest.raises(p2.P2LiveFixtureError, match="SYNTHETIC_ONLY"):
        p2.prepare_p2_live_admission(
            None,  # type: ignore[arg-type]
            variant="A",
            actor="human:p2-test",
            ack="",
            ttl_seconds=900,
        )


def test_variant_a_prepares_one_unconsumed_local_context_admission(conn) -> None:
    receipt = _prepare(conn, "A")
    handoff = _assert_live_guard_shape(conn, receipt)

    assert receipt["variant"] == "A"
    assert receipt["identity_ambiguity"] is None
    assert len(receipt["selected_context"]) == 1
    assert receipt["selected_context"][0]["entity_type"] == "stable_object"
    assert receipt["unrelated_object_ref"] not in receipt["selected_context"]
    assert handoff["include_declared_descendants"] is False
    assert handoff["context_pack"]["scope_widened_implicitly"] is False


def test_variant_b_prepares_composed_context_without_unrelated_object_or_review_claim(conn) -> None:
    receipt = _prepare(conn, "B")
    handoff = _assert_live_guard_shape(conn, receipt)

    assert receipt["variant"] == "B"
    assert receipt["identity_ambiguity"] is None
    assert len(receipt["selected_context"]) == 8
    assert {item["entity_type"] for item in receipt["selected_context"]} == {
        "stable_object",
        "information",
        "document",
        "knowledge",
    }
    assert receipt["unrelated_object_ref"] not in receipt["selected_context"]
    assert receipt["knowledge_review_status"] == "generated_unreviewed"
    assert receipt["apu_review_ref_is_synthetic_fixture"] is True
    assert handoff["include_declared_descendants"] is False
    assert handoff["context_pack"]["scope_widened_implicitly"] is False

    knowledge_ref = next(
        item["entity_id"]
        for item in receipt["selected_context"]
        if item["entity_type"] == "knowledge"
    )
    knowledge_id = knowledge_ref.removeprefix("knowledge:")
    status = conn.execute(
        "SELECT review_status FROM knowledge_items WHERE knowledge_id = %s",
        (knowledge_id,),
    ).fetchone()[0]
    assert status == "generated_unreviewed"


def test_identity_nondeterminant_prepares_two_equal_candidates_without_starting_hermes(conn) -> None:
    receipt = _prepare(conn, p2.IDENTITY_NONDETERMINANT)
    handoff = _assert_live_guard_shape(conn, receipt)
    ambiguity = receipt["identity_ambiguity"]
    records = _candidate_records(conn, receipt)

    assert receipt["variant"] == p2.IDENTITY_NONDETERMINANT
    assert ambiguity["class"] == "non_determinant"
    assert ambiguity["qualification_expectation"] == "continue_with_explicit_uncertainty"
    assert ambiguity["safe_non_success_fallback"] is None
    assert ambiguity["silent_identity_selection_allowed"] is False
    assert ambiguity["cognitive_result_observed"] is False
    assert handoff["selected_context"] == ambiguity["candidate_target_refs"]
    assert receipt["selected_context"] == ambiguity["candidate_target_refs"]
    assert receipt["unrelated_object_ref"] not in receipt["selected_context"]

    assert records[0]["object_id"] != records[1]["object_id"]
    assert [
        record["stable_object"]["nomenclature"]["display_name"] for record in records
    ] == ["Cloison P2", "Cloison P2"]
    assert [_thicknesses(record) for record in records] == [[120], [120]]
    assert records[0]["source_representation_refs"] == records[1]["source_representation_refs"]
    assert [record["relation_claims"] for record in records] == [[], []]
    assert all(record["scope"]["relation_traversal_performed"] is False for record in records)
    assert all(record["scope"]["neighbour_records_materialized"] is False for record in records)


def test_identity_determinant_prepares_equal_candidates_with_different_consequence_context(conn) -> None:
    receipt = _prepare(conn, p2.IDENTITY_DETERMINANT)
    handoff = _assert_live_guard_shape(conn, receipt)
    ambiguity = receipt["identity_ambiguity"]
    records = _candidate_records(conn, receipt)

    assert receipt["variant"] == p2.IDENTITY_DETERMINANT
    assert ambiguity["class"] == "determinant"
    assert ambiguity["qualification_expectation"] == "ask_targeted_identity_clarification"
    assert ambiguity["safe_non_success_fallback"] == "explicitly_refuse_to_conclude"
    assert ambiguity["silent_identity_selection_allowed"] is False
    assert ambiguity["cognitive_result_observed"] is False
    assert set(
        (item["entity_type"], item["entity_id"])
        for item in ambiguity["candidate_target_refs"]
    ).issubset(
        {
            (item["entity_type"], item["entity_id"])
            for item in handoff["selected_context"]
        }
    )
    assert len(receipt["selected_context"]) == 6
    assert {item["entity_type"] for item in receipt["selected_context"]} == {"stable_object"}
    assert receipt["unrelated_object_ref"] not in receipt["selected_context"]

    assert records[0]["object_id"] != records[1]["object_id"]
    assert [
        record["stable_object"]["nomenclature"]["display_name"] for record in records
    ] == ["Cloison P2", "Cloison P2"]
    assert [_thicknesses(record) for record in records] == [[120], [120]]
    assert records[0]["source_representation_refs"] == records[1]["source_representation_refs"]
    assert len(records[0]["relation_claims"]) == 3
    assert {
        claim["relation_type"] for claim in records[0]["relation_claims"]
    } == {
        "spatial.adjacent_to",
        "architecture.hosted_by",
        "building_services.passes_through",
    }
    assert len(records[1]["relation_claims"]) == 1
    assert records[1]["relation_claims"][0]["relation_type"] == "spatial.adjacent_to"
    assert all(record["scope"]["relation_traversal_performed"] is False for record in records)
    assert all(record["scope"]["neighbour_records_materialized"] is False for record in records)


def test_each_variant_gets_a_fresh_project_and_admission(conn) -> None:
    a = _prepare(conn, "A")
    b = _prepare(conn, "B")

    assert a["question"] == b["question"] == p2.LIVE_QUESTION
    assert a["project_id"] != b["project_id"]
    assert a["handoff_id"] != b["handoff_id"]
    assert a["admission_id"] != b["admission_id"]
    assert a["selected_context"] != b["selected_context"]
