from __future__ import annotations

import hashlib
import importlib
import uuid
from pathlib import Path

import pytest

from mvp_vertical import agency_data, execution_results, pantheon_contracts


VENDOR_NAME = "project_change_variant_candidate"
VENDOR_SCHEMA = pantheon_contracts.schema_path(VENDOR_NAME)


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


def _implementation():
    return importlib.import_module("mvp_vertical.project_change_variants")


def test_project_change_variant_contract_uses_canonical_source() -> None:
    provenance = pantheon_contracts.provenance(VENDOR_NAME)
    assert provenance["source_repository"] == "ifanjuang/Pantheon"
    assert provenance["source_path"] == "schemas/project_change_variant_candidate.schema.yaml"
    assert provenance["posture"] == "canonical-repository"
    assert provenance["authority_transfer"] is False
    assert hashlib.sha256(VENDOR_SCHEMA.read_bytes()).hexdigest() == provenance["sha256"]


def test_execution_result_vocabulary_exposes_separate_variant_selection() -> None:
    assert "project_change_variant" in execution_results.RESULT_KINDS
    assert "selected_for_change_candidate" in execution_results.DISPOSITIONS


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    execution_results.ensure_schema(connection)
    connection.execute(
        "TRUNCATE execution_result_review_dispositions, execution_clarification_requests, "
        "execution_result_items, execution_results, agency_change_candidate_events, "
        "agency_change_candidates, agency_project_events, agency_projects "
        "RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("G")[:24],
        display_name="Projet variantes",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={
            "programme_summary": "Maison principale avec deux loggias.",
            "architectural_style": "Volumétrie en L.",
        },
    )


def _payload(
    project: dict,
    *,
    label: str,
    title: str,
    proposed_attributes: dict | None = None,
) -> dict:
    payload = {
        "candidate_kind": "project_change_variant",
        "request_ref": "variant-request.project.couverture",
        "request_scope_digest": (
            "sha256:4e8f6d83813b2ea13b39ecaf521f60ba820c217a963266eb4bcefc565f60c1cf"
        ),
        "project_ref": project["project_id"],
        "base_revision": project["revision"],
        "target_schema_id": "agency.project.v2",
        "variant_label": label,
        "variant_title": title,
        "proposed_attributes": proposed_attributes
        or {
            "architectural_style": f"Volumétrie en L sous {title.lower()}.",
            "programme_summary": f"Maison principale avec deux loggias et {title.lower()}.",
        },
        "rationale": f"Alternative {title} à comparer avant sélection humaine.",
        "assumptions": ["La structure porteuse reste compatible."],
        "compatibility_findings": [
            {
                "status": "uncertain",
                "subject": "prescription urbanistique",
                "detail": "Le matériau exact reste à vérifier dans le PLU.",
            }
        ],
        "open_questions": ["Quel vieillissement de surface est attendu ?"],
        "basis_refs": [
            {
                "entity_type": "project",
                "entity_id": project["project_id"],
                "observed_revision": project["revision"],
                "observed_status": project.get("status"),
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
    pantheon_contracts.validate(VENDOR_NAME, payload)
    return payload


def _store_siblings(conn, project: dict) -> tuple[str, str, str]:
    execution_id = _id("execution")
    zinc_id = _id("result-zinc")
    slate_id = _id("result-slate")
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract.project-variants",
            "project_ref": project["project_id"],
            "producer": {
                "capability": "compare_project_variants",
                "implementation": "hermes.skill.project-variants",
                "version": "0.20.0",
            },
            "produced_at": "2026-08-07T00:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": zinc_id,
                    "result_kind": "project_change_variant",
                    "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
                    "payload": _payload(
                        project,
                        label="option-zinc",
                        title="couverture zinc anthracite",
                    ),
                },
                {
                    "result_id": slate_id,
                    "result_kind": "project_change_variant",
                    "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
                    "payload": _payload(
                        project,
                        label="option-ardoise",
                        title="couverture ardoise naturelle",
                    ),
                },
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )
    return execution_id, zinc_id, slate_id


def test_sibling_variants_are_persisted_as_execution_results_before_selection(conn) -> None:
    project = _project(conn)
    execution_id, zinc_id, slate_id = _store_siblings(conn, project)

    stored = execution_results.get_execution_result(conn, execution_id)
    assert [item["result_id"] for item in stored["results"]] == [zinc_id, slate_id]
    assert {item["payload"]["request_ref"] for item in stored["results"]} == {
        "variant-request.project.couverture"
    }
    assert len({item["payload"]["request_scope_digest"] for item in stored["results"]}) == 1
    assert agency_data.get_project(conn, project["project_id"])["revision"] == project["revision"]


def test_human_selection_creates_existing_change_candidate_without_applying_project(conn) -> None:
    project = _project(conn)
    execution_id, zinc_id, _ = _store_siblings(conn, project)

    transition = _implementation().select_variant_for_change_candidate(
        conn,
        execution_id=execution_id,
        result_id=zinc_id,
        actor="human:architect",
        idempotency_key=_id("variant-selection"),
    )

    candidate = transition["change_candidate"]
    assert transition["project_mutated"] is False
    assert transition["evidence_admitted"] is False
    assert transition["decision_created"] is False
    assert candidate["status"] == "pending_review"
    assert candidate["entity_id"] == project["project_id"]
    assert candidate["source_execution_result_id"] == execution_id
    assert candidate["source_result_id"] == zinc_id
    assert candidate["source_review_disposition_id"] == transition["selection"]["disposition_id"]
    assert candidate["variant_request_ref"] == "variant-request.project.couverture"
    assert candidate["variant_label"] == "option-zinc"
    assert candidate["changes"]

    current = agency_data.get_project(conn, project["project_id"])
    assert current["revision"] == project["revision"]
    assert current["attributes"] == project["attributes"]


def test_one_request_scope_cannot_select_two_sibling_variants(conn) -> None:
    project = _project(conn)
    execution_id, zinc_id, slate_id = _store_siblings(conn, project)
    implementation = _implementation()

    implementation.select_variant_for_change_candidate(
        conn,
        execution_id=execution_id,
        result_id=zinc_id,
        actor="human:architect",
        idempotency_key=_id("variant-selection"),
    )

    with pytest.raises(implementation.ProjectChangeVariantConflict, match="already selected"):
        implementation.select_variant_for_change_candidate(
            conn,
            execution_id=execution_id,
            result_id=slate_id,
            actor="human:architect",
            idempotency_key=_id("variant-selection"),
        )


def test_selection_refuses_project_claim_or_other_non_editable_fields(conn) -> None:
    project = _project(conn)
    execution_id = _id("execution")
    result_id = _id("result-budget")
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract.project-variants",
            "project_ref": project["project_id"],
            "producer": {
                "capability": "compare_project_variants",
                "implementation": "hermes.skill.project-variants",
                "version": "0.20.0",
            },
            "produced_at": "2026-08-07T00:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "project_change_variant",
                    "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
                    "payload": _payload(
                        project,
                        label="option-budget",
                        title="budget révisé",
                        proposed_attributes={"budget": 1200000},
                    ),
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )
    implementation = _implementation()

    with pytest.raises(implementation.ProjectChangeVariantError, match="not editable|ProjectClaim"):
        implementation.select_variant_for_change_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:architect",
            idempotency_key=_id("variant-selection"),
        )


def test_selection_refuses_stale_project_revision_without_mutation(conn) -> None:
    project = _project(conn)
    execution_id, zinc_id, _ = _store_siblings(conn, project)
    agency_data.update_project(
        conn,
        project_id=project["project_id"],
        changes={"description": "Révision concurrente"},
        actor="human:other",
        actor_kind="human",
        expected_revision=project["revision"],
        idempotency_key=_id("project-update"),
    )
    before = agency_data.get_project(conn, project["project_id"])
    implementation = _implementation()

    with pytest.raises(implementation.ProjectChangeVariantConflict, match="stale"):
        implementation.select_variant_for_change_candidate(
            conn,
            execution_id=execution_id,
            result_id=zinc_id,
            actor="human:architect",
            idempotency_key=_id("variant-selection"),
        )

    after = agency_data.get_project(conn, project["project_id"])
    assert after["revision"] == before["revision"]
    assert after["attributes"] == before["attributes"]
