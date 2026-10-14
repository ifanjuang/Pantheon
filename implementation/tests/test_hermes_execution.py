"""Acceptance tests for the governed external Hermes execution boundary."""

from __future__ import annotations

import uuid
import pytest

from mvp_vertical import agency_data, hermes_execution, hermes_handoff_preview, hermes_handoff_store, work_issues


def _id(prefix: str) -> str: return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        c = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    c.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    c.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    for migration in hermes_execution.MIGRATIONS:
        c.execute(migration.read_text(encoding="utf-8"))
    c.commit()
    yield c
    c.close()


def _submitted(conn) -> dict:
    project = agency_data.create_project(
        conn, project_id=_id("project"), code=_id("CODE").upper(),
        display_name="Projet Hermes Execution", actor="human-reviewer",
        actor_kind="human", idempotency_key=_id("project-create"),
    )
    envelope = {
        "root_entity": {"entity_id": f"project:{project['project_id']}", "entity_type": "project"},
        "descendants": [], "source_refs": [], "explicit_additions": [], "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question="Vérifie le dossier.", card_context_envelope=envelope, selected_context=[]
    )
    return hermes_handoff_store.submit_handoff(
        conn, actor="ifan", idempotency_key=_id("handoff-submit"), question="Vérifie le dossier.",
        preview=preview, card_context_envelope=envelope, selected_context=[], include_declared_descendants=False,
    )


def _admit(conn, handoff: dict, ttl: int = 900) -> dict:
    return hermes_execution.admit_handoff(
        conn, handoff_id=handoff["handoff_id"], actor="ifan",
        idempotency_key=_id("execution-admit"), ttl_seconds=ttl,
    )


def test_admission_is_bounded_immutable_and_does_not_start_runtime(conn) -> None:
    handoff = _submitted(conn)
    admission = _admit(conn, handoff)
    assert admission["admission_state"] == "admitted"
    assert admission["ttl_seconds"] == 900
    assert admission["expires_at"]
    assert admission["work_issue_version"] == handoff["work_issue"]["version"]
    assert admission["ready_for_external_runtime"] is True
    assert admission["runtime_started"] is False
    assert conn.execute("SELECT count(*) FROM hermes_runs WHERE issue_id=%s", (handoff["work_issue"]["issue_id"],)).fetchone()[0] == 0
    with pytest.raises(Exception, match="hermes_execution_admissions are immutable"):
        conn.execute("UPDATE hermes_execution_admissions SET admitted_by='x' WHERE admission_id=%s", (admission["admission_id"],))
    conn.rollback()


def test_revocation_is_append_only_and_blocks_envelope(conn) -> None:
    admission = _admit(conn, _submitted(conn))
    revoked = hermes_execution.revoke_admission(
        conn, admission_id=admission["admission_id"], actor="ifan",
        reason="Contexte à revoir", idempotency_key=_id("revoke"),
    )
    assert revoked["admission_state"] == "revoked"
    assert revoked["ready_for_external_runtime"] is False
    assert revoked["revocation_reason"] == "Contexte à revoir"
    with pytest.raises(hermes_execution.AdmissionConflict, match="not consumable"):
        hermes_execution.get_execution_envelope(conn, admission["admission_id"])
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM hermes_execution_admission_events WHERE admission_id=%s", (admission["admission_id"],))
    conn.rollback()


def test_issue_version_change_after_admission_makes_it_stale(conn) -> None:
    handoff = _submitted(conn)
    admission = _admit(conn, handoff)
    issue = handoff["work_issue"]
    changed_projection = work_issues.add_comment(
        conn,
        issue_id=issue["issue_id"],
        comment_id=_id("comment"),
        body="Contexte métier modifié après admission.",
        author="ifan",
        expected_version=issue["version"],
        idempotency_key=_id("issue-comment"),
    )
    changed = changed_projection["work_issue"]
    assert changed["status"] == "open"
    assert changed["version"] == issue["version"] + 1
    observed = hermes_execution.get_admission(conn, admission["admission_id"])
    assert observed["admission_state"] == "stale"
    with pytest.raises(hermes_execution.RuntimeStartConflict, match="not consumable"):
        hermes_execution.record_external_runtime_start(
            conn, admission_id=admission["admission_id"], run_id=_id("run"), actor="hermes-adapter",
            expected_issue_version=issue["version"], idempotency_key=_id("runtime-start"),
        )


def test_external_hermes_consumes_admission_once(conn) -> None:
    handoff = _submitted(conn)
    admission = _admit(conn, handoff)
    issue = handoff["work_issue"]
    run_id = _id("hermes-runtime")
    started = hermes_execution.record_external_runtime_start(
        conn, admission_id=admission["admission_id"], run_id=run_id, actor="hermes-adapter",
        expected_issue_version=issue["version"], idempotency_key=_id("runtime-start"),
    )
    assert started["work_issue"]["status"] == "in_progress"
    state = hermes_execution.get_admission(conn, admission["admission_id"])
    assert state["admission_state"] == "consumed"
    assert state["consumed_by_run_id"] == run_id
    replay = hermes_execution.record_external_runtime_start(
        conn, admission_id=admission["admission_id"], run_id=run_id, actor="hermes-adapter",
        expected_issue_version=issue["version"], idempotency_key=_id("runtime-replay"),
    )
    assert replay["replayed"] is True
    with pytest.raises(hermes_execution.RuntimeStartConflict):
        hermes_execution.record_external_runtime_start(
            conn, admission_id=admission["admission_id"], run_id=_id("other"), actor="hermes-adapter",
            expected_issue_version=issue["version"], idempotency_key=_id("runtime-conflict"),
        )
