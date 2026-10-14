"""PostgreSQL acceptance tests for admission-bound Hermes context reads."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    agency_information,
    hermes_execution,
    hermes_handoff_preview,
    hermes_handoff_store,
    hermes_runtime_return,
    hermes_scoped_context,
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


def _person(conn, *, name: str) -> str:
    person_id = _id("person")
    conn.execute(
        """
        INSERT INTO agency_people (
            person_id, display_name, email, phone, created_by, updated_by
        ) VALUES (%s, %s, %s, %s, 'human', 'human')
        """,
        (person_id, name, f"{person_id}@example.test", "0600000000"),
    )
    conn.commit()
    return person_id


def _running(conn) -> tuple[dict, dict, str, str, str]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CODE").upper(),
        display_name="Projet contexte borné",
        description="Version initiale",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    admitted_person = _person(conn, name="Personne admise")
    unrelated_person = _person(conn, name="Personne hors contexte")
    selected = [
        {"entity_id": f"person:{admitted_person}", "entity_type": "person"},
    ]
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
        question="Analyse uniquement ce contexte.",
        card_context_envelope=envelope,
        selected_context=selected,
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff"),
        question="Analyse uniquement ce contexte.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=selected,
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="ifan",
        idempotency_key=_id("admit"),
        ttl_seconds=900,
    )
    run_id = _id("hermes-run")
    started = hermes_execution.record_external_runtime_start(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
        expected_issue_version=handoff["work_issue"]["version"],
        idempotency_key=_id("start"),
    )
    return admission, started["work_issue"], run_id, admitted_person, unrelated_person


def _running_information(conn) -> tuple[dict, str, dict, dict]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("INFO").upper(),
        display_name="Projet information bornée",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    first = agency_information.create_information(
        conn,
        project_id=project["project_id"],
        title="PLU",
        category="PLU",
        source_type="document",
        source_ref="paperless://doc/acted",
        index_label="A01",
        summary="Zone UDb actée",
        details="Règles actées",
        actor_kind="human",
    )
    acted = agency_information.act_working_information(
        conn,
        information_id=first["information_id"],
        expected_revision=first["revision"],
        actor_kind="human",
        actor="architecte",
    )
    working = agency_information.derive_working_version(
        conn,
        acted_information_id=acted["information_id"],
        new_index_label="A02",
        source_ref="paperless://doc/working",
        source_note=None,
        actor_kind="human",
    )
    envelope = {
        "root_entity": {
            "entity_id": f"information:{working['information_id']}",
            "entity_type": "information",
        },
        "descendants": [
            {
                "entity_id": f"information:{acted['information_id']}",
                "entity_type": "information",
            }
        ],
        "source_refs": ["paperless://doc/working", "paperless://doc/acted"],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question="Comparer la version de travail à l’état acté.",
        card_context_envelope=envelope,
        selected_context=[],
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff"),
        question="Comparer la version de travail à l’état acté.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=True,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="ifan",
        idempotency_key=_id("admit"),
        ttl_seconds=900,
    )
    run_id = _id("hermes-run")
    hermes_execution.record_external_runtime_start(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
        expected_issue_version=handoff["work_issue"]["version"],
        idempotency_key=_id("start"),
    )
    return admission, run_id, acted, working


def test_manifest_exposes_only_exact_admitted_identities_without_global_surfaces(conn) -> None:
    admission, _issue, run_id, admitted_person, unrelated_person = _running(conn)
    manifest = hermes_scoped_context.get_context_manifest(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
    )

    assert manifest["requested_effect"] == "read_only"
    assert manifest["run_status"] == "running"
    assert manifest["field_projection_version"] == "scoped-context-v1"
    assert manifest["global_search_available"] is False
    assert manifest["global_listing_available"] is False
    assert manifest["source_dereference_available"] is False
    assert manifest["write_effect"] is False
    assert manifest["read_semantics"] == "current_owner_read"
    assert {item["entity_id"] for item in manifest["entities"]} == {
        f"project:{admission['work_issue']['case_ref']}",
        f"person:{admitted_person}",
    }
    assert f"person:{unrelated_person}" not in {
        item["entity_id"] for item in manifest["entities"]
    }


def test_exact_admitted_person_can_be_read_but_existing_unrelated_person_is_refused(conn) -> None:
    admission, _issue, run_id, admitted_person, unrelated_person = _running(conn)

    allowed = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="person",
        entity_id=f"person:{admitted_person}",
        actor="hermes-runtime",
    )
    assert allowed["record"]["person_id"] == admitted_person
    assert allowed["record"]["display_name"] == "Personne admise"
    assert allowed["field_projection_version"] == "scoped-context-v1"
    assert allowed["record_owner_system"] == "postgres"
    assert allowed["source_binary_included"] is False
    assert "created_by" not in allowed["record"]
    assert "updated_by" not in allowed["record"]

    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="outside the exact admitted Context Pack",
    ):
        hermes_scoped_context.get_context_entity(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            entity_type="person",
            entity_id=f"person:{unrelated_person}",
            actor="hermes-runtime",
        )


def test_scoped_information_exposes_working_and_acted_as_distinct_admitted_entities(conn) -> None:
    admission, run_id, acted, working = _running_information(conn)
    manifest = hermes_scoped_context.get_context_manifest(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
    )
    ids = {item["entity_id"] for item in manifest["entities"]}
    assert f"information:{working['information_id']}" in ids
    assert f"information:{acted['information_id']}" in ids

    current = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="information",
        entity_id=f"information:{working['information_id']}",
        actor="hermes-runtime",
    )
    baseline = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="information",
        entity_id=f"information:{acted['information_id']}",
        actor="hermes-runtime",
    )
    assert current["record"]["status"] == "draft"
    assert current["record"]["index_label"] == "A02"
    assert current["representation"]["working_assumptions_are_not_acted"] is True
    assert baseline["record"]["status"] == "acted"
    assert baseline["record"]["index_label"] == "A01"
    assert baseline["representation"]["working_assumptions_are_not_acted"] is False


def test_context_entity_is_current_owner_reread_not_admission_snapshot(conn) -> None:
    admission, _issue, run_id, _admitted_person, _unrelated_person = _running(conn)
    project_id = admission["work_issue"]["case_ref"]

    updated = agency_data.update_project(
        conn,
        project_id=project_id,
        changes={"description": "Version modifiée après démarrage du run"},
        actor="human-reviewer",
        actor_kind="human",
        expected_revision=1,
        idempotency_key=_id("project-update"),
    )
    assert updated["revision"] == 2

    materialized = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="project",
        entity_id=f"project:{project_id}",
        actor="hermes-runtime",
    )
    assert materialized["record"]["description"] == "Version modifiée après démarrage du run"
    assert materialized["current_revision"] == 2
    assert materialized["read_semantics"] == "current_owner_read"
    assert materialized["context_pack_authorizes_identity_not_snapshot"] is True
    assert "created_by" not in materialized["record"]
    assert "updated_by" not in materialized["record"]


def test_wrong_run_and_completed_run_cannot_read_context(conn) -> None:
    admission, issue, run_id, _admitted_person, _unrelated_person = _running(conn)

    with pytest.raises(hermes_scoped_context.ScopedContextNotFound):
        hermes_scoped_context.get_context_manifest(
            conn,
            admission_id=admission["admission_id"],
            run_id="hermes-run-wrong",
            actor="hermes-runtime",
        )

    returned = hermes_runtime_return.record_external_runtime_return(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        normalized_return={
            "outcome": "partial",
            "summary": "Lecture terminée partiellement.",
            "trace_refs": ["hermes://trace/scoped-context"],
        },
        actor="hermes-runtime",
        expected_issue_version=issue["version"],
        idempotency_key=_id("return"),
    )
    assert returned["runtime_status"] == "partial"

    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="requires a running Hermes run",
    ):
        hermes_scoped_context.get_context_manifest(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            actor="hermes-runtime",
        )
