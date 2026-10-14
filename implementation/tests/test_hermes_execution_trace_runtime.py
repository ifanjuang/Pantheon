"""PostgreSQL acceptance tests for execution-trace correlation and persistence."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    hermes_execution,
    hermes_handoff_preview,
    hermes_handoff_store,
    hermes_launch_context,
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
    connection.commit()
    yield connection
    connection.close()


def _running_with_reservation(conn) -> tuple[dict, dict, dict, str]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CODE").upper(),
        display_name="Execution trace project",
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
        "source_refs": [],
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
        actor="human-reviewer",
        idempotency_key=_id("handoff"),
        question="Analyse le dossier.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="human-reviewer",
        idempotency_key=_id("admit"),
        ttl_seconds=900,
    )
    reservation = hermes_launch_context.reserve_launch(
        conn,
        admission_id=admission["admission_id"],
        actor="hermes-run-binding",
        idempotency_key=_id("reserve"),
    )
    run_id = _id("run")
    started = hermes_execution.record_external_runtime_start(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-run-binding",
        expected_issue_version=reservation["work_issue_version"],
        idempotency_key=_id("start"),
        launch_reservation_id=reservation["launch_reservation_id"],
    )
    return admission, reservation, started["work_issue"], run_id


def _trace(admission: dict, reservation: dict, run_id: str) -> dict:
    return {
        "schema_version": "hermes-execution-trace-summary-v1",
        "correlation": {
            "admission_id": admission["admission_id"],
            "launch_reservation_id": reservation["launch_reservation_id"],
            "snapshot_id": reservation["snapshot_id"],
            "snapshot_digest": reservation["snapshot_digest"],
            "run_id": run_id,
        },
        "execution": {"terminal_status": "partial"},
        "trace_refs": [f"hermes://runs/{run_id}"],
        "provenance": {
            "pantheon_observed": [
                "correlation.admission_id",
                "correlation.launch_reservation_id",
                "correlation.snapshot_id",
                "correlation.snapshot_digest",
                "correlation.run_id",
            ],
            "binding_observed": ["trace_refs"],
            "runtime_reported": ["execution.terminal_status"],
        },
    }


def test_valid_partial_trace_is_persisted_without_authority_effect(conn) -> None:
    admission, reservation, issue, run_id = _running_with_reservation(conn)
    trace = _trace(admission, reservation, run_id)
    result = hermes_runtime_return.record_external_runtime_return(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-run-binding",
        expected_issue_version=issue["version"],
        idempotency_key=_id("return"),
        normalized_return={
            "outcome": "partial",
            "summary": "Résultat partiel.",
            "trace_refs": [f"hermes://runs/{run_id}"],
            "execution_trace_summary": trace,
        },
    )

    stored = conn.execute(
        "SELECT normalized_return FROM hermes_runs WHERE run_id = %s",
        (run_id,),
    ).fetchone()[0]
    assert stored["execution_trace_summary"] == trace
    assert result["work_issue"]["status"] == "waiting"
    assert result["evidence_admitted"] is False
    assert result["issue_closed"] is False
    assert result["external_effect_authorized"] is False


def test_foreign_snapshot_digest_is_refused_atomically(conn) -> None:
    admission, reservation, issue, run_id = _running_with_reservation(conn)
    trace = _trace(admission, reservation, run_id)
    trace["correlation"]["snapshot_digest"] = "digest-foreign"

    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnConflict,
        match="snapshot_digest",
    ):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-run-binding",
            expected_issue_version=issue["version"],
            idempotency_key=_id("return"),
            normalized_return={
                "outcome": "partial",
                "summary": "Résultat partiel.",
                "trace_refs": [f"hermes://runs/{run_id}"],
                "execution_trace_summary": trace,
            },
        )

    row = conn.execute(
        "SELECT status, normalized_return FROM hermes_runs WHERE run_id = %s",
        (run_id,),
    ).fetchone()
    assert row[0] == "running"
    assert row[1] is None


def test_trace_ref_outside_normalized_return_is_refused(conn) -> None:
    admission, reservation, issue, run_id = _running_with_reservation(conn)
    trace = _trace(admission, reservation, run_id)
    trace["trace_refs"] = ["hermes://runs/other"]

    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnConflict,
        match="not present in normalized return",
    ):
        hermes_runtime_return.record_external_runtime_return(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-run-binding",
            expected_issue_version=issue["version"],
            idempotency_key=_id("return"),
            normalized_return={
                "outcome": "partial",
                "summary": "Résultat partiel.",
                "trace_refs": [f"hermes://runs/{run_id}"],
                "execution_trace_summary": trace,
            },
        )
