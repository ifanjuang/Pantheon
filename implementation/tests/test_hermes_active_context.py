"""PostgreSQL tests for admission-session active context resolution."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    hermes_active_context,
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


def _running(conn):
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CODE").upper(),
        display_name="Projet session context",
        actor="human",
        actor_kind="human",
        idempotency_key=_id("project"),
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
        question="Analyse bornée.",
        card_context_envelope=envelope,
        selected_context=[],
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff"),
        question="Analyse bornée.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="ifan",
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
    return project, admission, run_id, started["work_issue"]


def test_active_manifest_resolves_run_server_side_from_admission_session(conn) -> None:
    project, admission, run_id, _issue = _running(conn)
    manifest = hermes_active_context.get_active_context_manifest(
        conn,
        admission_id=admission["admission_id"],
        actor="hermes-plugin:pantheon-context-bridge",
    )
    assert manifest["run_id"] == run_id
    assert manifest["caller_supplied_run_id"] is False
    assert manifest["access_path"] == "admission_session_resolved_to_exact_running_run"
    assert manifest["entities"] == [
        {
            "entity_id": f"project:{project['project_id']}",
            "entity_type": "project",
            "materializable": True,
        }
    ]


def test_active_entity_still_requires_exact_context_membership(conn) -> None:
    project, admission, _run_id, _issue = _running(conn)
    allowed = hermes_active_context.get_active_context_entity(
        conn,
        admission_id=admission["admission_id"],
        entity_type="project",
        entity_id=f"project:{project['project_id']}",
        actor="hermes-plugin:pantheon-context-bridge",
    )
    assert allowed["record"]["project_id"] == project["project_id"]
    assert allowed["caller_supplied_run_id"] is False

    with pytest.raises(Exception, match="outside the exact admitted Context Pack"):
        hermes_active_context.get_active_context_entity(
            conn,
            admission_id=admission["admission_id"],
            entity_type="project",
            entity_id="project:other",
            actor="hermes-plugin:pantheon-context-bridge",
        )


def test_active_context_stops_after_runtime_return(conn) -> None:
    _project, admission, run_id, issue = _running(conn)
    returned = hermes_runtime_return.record_external_runtime_return(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        normalized_return={
            "outcome": "partial",
            "summary": "Terminé pour ce test.",
            "trace_refs": [f"hermes://runs/{run_id}"],
        },
        actor="hermes-runtime",
        expected_issue_version=issue["version"],
        idempotency_key=_id("return"),
    )
    assert returned["runtime_status"] == "partial"
    with pytest.raises(hermes_active_context.ActiveContextConflict, match="requires a running Hermes run"):
        hermes_active_context.get_active_context_manifest(
            conn,
            admission_id=admission["admission_id"],
            actor="hermes-plugin:pantheon-context-bridge",
        )
