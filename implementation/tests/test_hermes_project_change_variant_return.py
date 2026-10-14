"""PostgreSQL tests for typed Project alternatives returned by Hermes."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    execution_results,
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
    execution_results.ensure_schema(connection)
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    for migration in hermes_execution.MIGRATIONS:
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.execute(hermes_result_candidate.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(
        "TRUNCATE execution_result_review_dispositions, execution_clarification_requests, "
        "execution_result_items, execution_results, hermes_result_candidates, "
        "hermes_runs, hermes_run_launch_reservations, hermes_execution_admission_events, "
        "hermes_execution_admissions, cockpit_hermes_handoffs, work_card_metadata, "
        "issue_events, work_issues, agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _running(conn) -> tuple[dict, dict, str, dict, str]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("G2").upper()[:24],
        display_name="Projet variantes Hermes",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={
            "programme_summary": "Maison principale avec deux loggias.",
            "architectural_style": "Volumétrie en L.",
        },
    )
    entity_id = f"project:{project['project_id']}"
    envelope = {
        "root_entity": {"entity_id": entity_id, "entity_type": "project"},
        "descendants": [],
        "source_refs": [],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question="Compare deux alternatives de couverture.",
        card_context_envelope=envelope,
        selected_context=[],
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="human-reviewer",
        idempotency_key=_id("handoff-submit"),
        question="Compare deux alternatives de couverture.",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=[],
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="human-reviewer",
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
    task_contract_ref = conn.execute(
        "SELECT task_contract_ref FROM hermes_execution_admissions WHERE admission_id=%s",
        (admission["admission_id"],),
    ).fetchone()[0]
    conn.commit()
    return admission, started["work_issue"], run_id, project, task_contract_ref


def _payload(project: dict, *, label: str, title: str, basis_id: str | None = None) -> dict:
    return {
        "candidate_kind": "project_change_variant",
        "request_ref": "variant-request.project.couverture",
        "request_scope_digest": "sha256:" + "4" * 64,
        "project_ref": project["project_id"],
        "base_revision": project["revision"],
        "target_schema_id": "agency.project.v2",
        "variant_label": label,
        "variant_title": title,
        "proposed_attributes": {
            "architectural_style": f"Volumétrie en L sous {title.lower()}.",
            "programme_summary": f"Maison avec deux loggias et {title.lower()}.",
        },
        "rationale": "Alternative à comparer avant une sélection humaine.",
        "assumptions": ["La structure porteuse reste compatible."],
        "compatibility_findings": [],
        "open_questions": [],
        "basis_refs": [
            {
                "entity_type": "project",
                "entity_id": basis_id or project["project_id"],
                "observed_revision": project["revision"],
            }
        ],
        "limitations": ["Aucun chiffrage comparatif validé."],
        "authority": {
            "creates_change_candidate": False,
            "selects_variant": False,
            "applies_project_change": False,
            "creates_project_claim": False,
            "adopts_project_truth": False,
            "creates_decision": False,
            "admits_evidence": False,
            "authorizes_effect": False,
        },
    }


def _execution_result(project: dict, task_contract_ref: str, *, basis_id: str | None = None) -> dict:
    def item(result_id: str, label: str, title: str) -> dict:
        return {
            "result_id": result_id,
            "result_kind": "project_change_variant",
            "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
            "payload": _payload(
                project,
                label=label,
                title=title,
                basis_id=basis_id,
            ),
        }

    return {
        "execution_result_id": _id("execution-result"),
        "task_contract_ref": task_contract_ref,
        "project_ref": project["project_id"],
        "producer": {
            "capability": "compare_project_variants",
            "implementation": "hermes.skill.project-variants",
            "version": "0.20.0",
        },
        "produced_at": "2026-08-07T00:00:00+00:00",
        "authority": dict(execution_results.AUTHORITY),
        "results": [
            item(_id("result-zinc"), "option-zinc", "couverture zinc anthracite"),
            item(_id("result-ardoise"), "option-ardoise", "couverture ardoise naturelle"),
        ],
        "clarification_requests": [],
    }


def _result_candidate() -> dict:
    return {
        "result_type": "project_change_variant_execution_result",
        "candidate_payload": {"variant_count": 2},
        "confidence_note": None,
        "known_limits": ["Alternatives non sélectionnées."],
        "open_questions": [],
        "source_refs": [],
        "missing_evidence": [],
    }


def _return_values(conn):
    admission, issue, run_id, project, task_contract_ref = _running(conn)
    execution_result = _execution_result(project, task_contract_ref)
    values = {
        "conn": conn,
        "admission_id": admission["admission_id"],
        "run_id": run_id,
        "actor": "hermes-adapter",
        "expected_issue_version": issue["version"],
        "idempotency_key": _id("runtime-return"),
        "normalized_return": {
            "outcome": "result_candidate",
            "summary": "Deux alternatives produites, à sélectionner séparément.",
            "trace_refs": [f"hermes://runs/{run_id}"],
            "result_refs": [],
            "evidence_candidate_refs": [],
        },
        "result_candidate": _result_candidate(),
        "execution_result": execution_result,
    }
    return values, project, execution_result


def test_hermes_return_stores_sibling_variants_without_selection_or_project_write(conn) -> None:
    values, project, execution_result = _return_values(conn)
    before = agency_data.get_project(conn, project["project_id"])

    result = hermes_runtime_return.record_external_runtime_return(**values)

    assert result["runtime_return_recorded"] is True
    assert result["execution_result_stored"] is True
    assert result["variant_selected"] is False
    assert result["project_mutated"] is False
    assert result["decision_created"] is False
    assert result["evidence_admitted"] is False
    assert result["external_effect_authorized"] is False
    stored = execution_results.get_execution_result(
        conn, execution_result["execution_result_id"]
    )
    assert len(stored["results"]) == 2
    assert {item["result_kind"] for item in stored["results"]} == {
        "project_change_variant"
    }
    assert stored["review_dispositions"] == []
    assert conn.execute(
        "SELECT count(*) FROM agency_change_candidates"
    ).fetchone()[0] == 0
    after = agency_data.get_project(conn, project["project_id"])
    assert after["revision"] == before["revision"]
    assert after["attributes"] == before["attributes"]


def test_hermes_variant_return_replays_same_execution_result(conn) -> None:
    values, _, execution_result = _return_values(conn)
    first = hermes_runtime_return.record_external_runtime_return(**values)
    replay = hermes_runtime_return.record_external_runtime_return(**values)
    assert replay["execution_result"]["execution_result"]["execution_result_id"] == (
        first["execution_result"]["execution_result"]["execution_result_id"]
    )
    assert conn.execute(
        "SELECT count(*) FROM execution_results WHERE execution_result_id=%s",
        (execution_result["execution_result_id"],),
    ).fetchone()[0] == 1


def test_outside_basis_reference_refuses_all_return_persistence(conn) -> None:
    admission, issue, run_id, project, task_contract_ref = _running(conn)
    execution_result = _execution_result(
        project,
        task_contract_ref,
        basis_id="project-outside",
    )
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
                "summary": "Alternative hors scope.",
                "trace_refs": [f"hermes://runs/{run_id}"],
            },
            result_candidate=_result_candidate(),
            execution_result=execution_result,
        )
    assert conn.execute("SELECT count(*) FROM execution_results").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM hermes_result_candidates").fetchone()[0] == 0
    assert conn.execute(
        "SELECT status FROM hermes_runs WHERE run_id=%s", (run_id,)
    ).fetchone()[0] == "running"


def test_task_contract_mismatch_refuses_before_persistence(conn) -> None:
    values, _, _ = _return_values(conn)
    values["execution_result"]["task_contract_ref"] = "task-contract.other"
    with pytest.raises(
        hermes_runtime_return.HermesRuntimeReturnConflict,
        match="task_contract_ref differs",
    ):
        hermes_runtime_return.record_external_runtime_return(**values)
    assert conn.execute("SELECT count(*) FROM execution_results").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM hermes_result_candidates").fetchone()[0] == 0
