"""Acceptance tests for bounded Hermes returns and rich result candidates."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import (
    agency_data,
    hermes_execution,
    hermes_handoff_preview,
    hermes_handoff_store,
    hermes_result_candidate,
    hermes_runtime_return,
    work_issues,
)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    for migration in hermes_execution.MIGRATIONS:
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.execute(hermes_result_candidate.MIGRATION.read_text(encoding="utf-8"))
    connection.commit()
    yield connection
    connection.close()


def _running(conn, *, source_refs: list[str] | None = None) -> tuple[dict, dict, str]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CODE").upper(),
        display_name="Projet Hermes Return",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    envelope = {
        "root_entity": {
            "entity_id": f"project:{project['project_id']}",
            "entity_type": "project",
        },
        "descendants": [],
        "source_refs": list(source_refs or []),
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question="Analyse le dossier.",
        card_context_envelope=envelope,
        selected_context=[],
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff-submit"),
        question="Analyse le dossier.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="ifan",
        idempotency_key=_id("execution-admit"),
        ttl_seconds=900,
    )
    run_id = _id("hermes-run")
    started = hermes_execution.record_external_runtime_start(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-adapter",
        expected_issue_version=handoff["work_issue"]["version"],
        idempotency_key=_id("runtime-start"),
    )
    return admission, started["work_issue"], run_id


def _rich_candidate(*, source_refs: list[str] | None = None) -> dict:
    return {
        "result_type": "project_analysis",
        "candidate_payload": {"points": ["structure", "coordination"]},
        "confidence_note": "Synthèse à vérifier par un humain.",
        "known_limits": ["Plans structure non signés"],
        "open_questions": ["Le BET confirme-t-il la réservation ?"],
        "source_refs": list(source_refs or []),
        "missing_evidence": ["note de calcul définitive"],
    }


def test_result_candidate_is_separate_immutable_record_and_issue_only_keeps_ref(conn) -> None:
    source_ref = "nas://project/cctp.pdf"
    admission, issue, run_id = _running(conn, source_refs=[source_ref])
    result = hermes_runtime_return.record_external_runtime_return(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-adapter",
        expected_issue_version=issue["version"],
        idempotency_key=_id("runtime-return"),
        normalized_return={
            "outcome": "result_candidate",
            "summary": "Analyse terminée, à relire.",
            "result_refs": [],
            "trace_refs": ["hermes://trace/run-1"],
            "evidence_candidate_refs": ["evidence-candidate:structure"],
        },
        result_candidate=_rich_candidate(source_refs=[source_ref]),
    )

    candidate = result["result_candidate"]
    assert result["runtime_return_recorded"] is True
    assert result["runtime_status"] == "returned"
    assert result["work_issue"]["status"] == "review"
    assert result["result_status"] == "candidate"
    assert result["evidence_admitted"] is False
    assert result["issue_closed"] is False
    assert candidate["run_id"] == run_id
    assert candidate["admission_id"] == admission["admission_id"]
    assert candidate["governance_result_status"] == "candidate"
    assert candidate["evidence_status"] == "candidate"
    assert candidate["trace_is_not_proof"] is True
    assert candidate["approval_still_required"] is True
    assert candidate["human_decision_required"] is True
    assert candidate["source_refs"] == [source_ref]
    assert candidate["known_limits"] == ["Plans structure non signés"]
    assert candidate["open_questions"] == ["Le BET confirme-t-il la réservation ?"]

    stored_return = conn.execute(
        "SELECT normalized_return FROM hermes_runs WHERE run_id = %s",
        (run_id,),
    ).fetchone()[0]
    assert stored_return["result_refs"] == [candidate["result_candidate_id"]]
    assert "source_refs" not in stored_return
    assert "known_limits" not in stored_return
    assert "open_questions" not in stored_return
    assert "candidate_payload" not in stored_return

    # Isolate the following negative mutation checks from the implicit read
    # transaction opened by the SELECT above.
    conn.commit()
    with pytest.raises(psycopg.errors.RaiseException, match="immutable candidate snapshots"):
        conn.execute(
            "UPDATE hermes_result_candidates SET created_by = 'rewritten' WHERE result_candidate_id = %s",
            (candidate["result_candidate_id"],),
        )
    conn.rollback()
    with pytest.raises(psycopg.errors.RaiseException, match="immutable candidate snapshots"):
        conn.execute(
            "DELETE FROM hermes_result_candidates WHERE result_candidate_id = %s",
            (candidate["result_candidate_id"],),
        )
    conn.rollback()


def test_result_candidate_replay_returns_same_candidate(conn) -> None:
    source_ref = "nas://project/cctp.pdf"
    admission, issue, run_id = _running(conn, source_refs=[source_ref])
    values = dict(
        conn=conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-adapter",
        expected_issue_version=issue["version"],
        idempotency_key=_id("runtime-return"),
        normalized_return={
            "outcome": "result_candidate",
            "summary": "Analyse terminée, à relire.",
            "trace_refs": ["hermes://trace/run-replay"],
        },
        result_candidate=_rich_candidate(source_refs=[source_ref]),
    )
    first = hermes_runtime_return.record_external_runtime_return(**values)
    replay = hermes_runtime_return.record_external_runtime_return(**values)
    assert replay["result_candidate"]["result_candidate_id"] == first["result_candidate"]["result_candidate_id"]
    assert replay["work_issue"]["status"] == "review"


def test_result_candidate_source_outside_admitted_context_is_refused_atomically(conn) -> None:
    admission, issue, run_id = _running(conn, source_refs=["nas://project/admitted.pdf"])
    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnError,
        match="outside the admitted Context Pack",
    ):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-adapter",
            expected_issue_version=issue["version"],
            idempotency_key=_id("runtime-return"),
            normalized_return={
                "outcome": "result_candidate",
                "summary": "Analyse hors périmètre.",
                "trace_refs": ["hermes://trace/run-scope"],
            },
            result_candidate=_rich_candidate(source_refs=["nas://other/secret.pdf"]),
        )

    assert conn.execute(
        "SELECT count(*) FROM hermes_result_candidates WHERE run_id = %s",
        (run_id,),
    ).fetchone()[0] == 0
    assert conn.execute(
        "SELECT status FROM hermes_runs WHERE run_id = %s",
        (run_id,),
    ).fetchone()[0] == "running"


def test_result_candidate_outcome_requires_rich_candidate_payload(conn) -> None:
    admission, issue, run_id = _running(conn)
    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnError,
        match="requires a separate Hermes result_candidate payload",
    ):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-adapter",
            expected_issue_version=issue["version"],
            idempotency_key=_id("runtime-return"),
            normalized_return={
                "outcome": "result_candidate",
                "summary": "Analyse.",
                "trace_refs": ["hermes://trace/run-missing"],
            },
        )


def test_non_candidate_outcome_refuses_rich_candidate_payload(conn) -> None:
    admission, issue, run_id = _running(conn)
    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnError,
        match="accepted only when outcome=result_candidate",
    ):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-adapter",
            expected_issue_version=issue["version"],
            idempotency_key=_id("runtime-return"),
            normalized_return={
                "outcome": "partial",
                "summary": "Analyse partielle.",
                "trace_refs": ["hermes://trace/run-partial-rich"],
            },
            result_candidate=_rich_candidate(),
        )


def test_partial_return_waits_and_same_material_event_can_replay(conn) -> None:
    admission, issue, run_id = _running(conn)
    values = dict(
        conn=conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-adapter",
        expected_issue_version=issue["version"],
        idempotency_key=_id("runtime-return"),
        normalized_return={
            "outcome": "partial",
            "summary": "Analyse partielle.",
            "trace_refs": ["hermes://trace/run-partial"],
        },
    )
    first = hermes_runtime_return.record_external_runtime_return(**values)
    replay = hermes_runtime_return.record_external_runtime_return(**values)
    assert first["work_issue"]["status"] == "waiting"
    assert first["runtime_status"] == "partial"
    assert first["result_candidate"] is None
    assert replay["work_issue"]["status"] == "waiting"
    assert replay["runtime_status"] == "partial"


def test_direct_adapter_still_refuses_rich_fields_inside_bounded_return(conn) -> None:
    admission, issue, run_id = _running(conn)
    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnError,
        match="unsupported normalized Hermes return field",
    ):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-adapter",
            expected_issue_version=issue["version"],
            idempotency_key=_id("runtime-return"),
            normalized_return={
                "outcome": "result_candidate",
                "summary": "Analyse à relire.",
                "trace_refs": ["hermes://trace/run-rich"],
                "source_refs": ["nas://project/source.pdf"],
            },
            result_candidate=_rich_candidate(),
        )


def test_return_for_wrong_admission_is_refused(conn) -> None:
    _, issue, run_id = _running(conn)
    with pytest.raises(hermes_runtime_return.HermesRuntimeReturnConflict):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id="admission-wrong",
            run_id=run_id,
            actor="hermes-adapter",
            expected_issue_version=issue["version"],
            idempotency_key=_id("runtime-return"),
            normalized_return={
                "outcome": "result_candidate",
                "summary": "Analyse.",
                "trace_refs": ["hermes://trace/run-1"],
            },
            result_candidate=_rich_candidate(),
        )
