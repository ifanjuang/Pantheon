"""PostgreSQL acceptance tests for submitted Cockpit -> Hermes handoffs."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    hermes_handoff_preview,
    hermes_handoff_store,
    work_issues,
)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    connection.commit()
    yield connection
    connection.close()


def _project(conn) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CODE").upper(),
        display_name="Projet Handoff",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )


def _preview(project_id: str) -> tuple[dict, dict]:
    envelope = {
        "root_entity": {"entity_id": f"project:{project_id}", "entity_type": "project"},
        "descendants": [],
        "source_refs": [],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question="Quels points faut-il examiner ?",
        card_context_envelope=envelope,
        selected_context=[],
    )
    return preview, envelope


def test_submit_creates_work_issue_and_immutable_snapshot_without_hermes_run(conn) -> None:
    project = _project(conn)
    preview, envelope = _preview(project["project_id"])
    key = _id("handoff-submit")

    result = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=key,
        question="Quels points faut-il examiner ?",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )

    assert result["status"] == "submitted_work_issue"
    assert result["execution_started"] is False
    assert result["hermes_run_created"] is False
    assert result["work_issue"]["assigned_to"] == "hermes"
    assert result["work_issue"]["requested_effect"] == "read_only"
    assert result["work_issue"]["task_contract_ref"] == preview["task_contract"]["task_contract_ref"]
    assert result["work_issue"]["context_pack_ref"] == preview["context_pack"]["context_pack_ref"]

    run_count = conn.execute(
        "SELECT count(*) FROM hermes_runs WHERE issue_id = %s",
        (result["work_issue"]["issue_id"],),
    ).fetchone()[0]
    assert run_count == 0

    snapshot = conn.execute(
        "SELECT task_contract, context_pack, preview_digest, created_by FROM cockpit_hermes_handoffs WHERE handoff_id = %s",
        (result["handoff_id"],),
    ).fetchone()
    assert snapshot[0]["task_contract_ref"] == preview["task_contract"]["task_contract_ref"]
    assert snapshot[1]["context_pack_ref"] == preview["context_pack"]["context_pack_ref"]
    assert snapshot[2] == preview["preview_digest"]
    assert snapshot[3] == "ifan"

    with pytest.raises(Exception, match="immutable contract snapshots"):
        conn.execute(
            "UPDATE cockpit_hermes_handoffs SET created_by = 'rewritten' WHERE handoff_id = %s",
            (result["handoff_id"],),
        )
    conn.rollback()


def test_submit_is_idempotent_and_conflicting_reuse_is_refused(conn) -> None:
    project = _project(conn)
    preview, envelope = _preview(project["project_id"])
    key = _id("handoff-submit")
    values = dict(
        actor="ifan",
        idempotency_key=key,
        question="Quels points faut-il examiner ?",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )

    first = hermes_handoff_store.submit_handoff(conn, **values)
    replay = hermes_handoff_store.submit_handoff(conn, **values)
    assert replay == first

    changed = dict(values)
    changed["question"] = "Autre question"
    with pytest.raises(hermes_handoff_store.HandoffIdempotencyConflict):
        hermes_handoff_store.submit_handoff(conn, **changed)
