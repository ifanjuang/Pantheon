"""Regression test for the handoff transaction boundary used by launch reservation."""

from __future__ import annotations

import uuid

import pytest
from psycopg.pq import TransactionStatus

from mvp_vertical import agency_data, hermes_handoff_preview, hermes_handoff_store, work_issues


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
    connection.commit()
    yield connection
    connection.close()


def test_top_level_handoff_returns_connection_to_idle_transaction_state(conn) -> None:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CODE").upper(),
        display_name="Projet transaction boundary",
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
        question="Prépare un handoff borné.",
        card_context_envelope=envelope,
        selected_context=[],
    )
    hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff"),
        question="Prépare un handoff borné.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )
    assert conn.info.transaction_status == TransactionStatus.IDLE
