from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mvp_vertical import (
    agency_data,
    hermes_handoff_store,
    hermes_result_candidate,
    work_issues,
    workspace_dialogue,
    workspace_qualification,
)
from mvp_vertical.workspace_qualification_api import install_workspace_qualification_routes


class _Connection:
    def close(self) -> None:
        pass


def _pdf(root: Path, name: str = "Plan.pdf") -> Path:
    path = root / name
    path.write_bytes(b"%PDF-1.7\nworkspace-dialogue-test\n%%EOF\n")
    return path


def _handoff(path: str = "Plan.pdf", project_id: str = "project-a") -> dict:
    return {
        "handoff_id": "handoff-prior-001",
        "work_issue_id": "work-prior-001",
        "case_ref": project_id,
        "root_entity_id": f"project:{project_id}",
        "root_entity_type": "project",
        "context_pack": {
            "source_refs": [
                f"workspace://vault/{path}?sha256=" + "a" * 64,
            ]
        },
    }


def _work_projection(*, returned: bool = True) -> dict:
    normalized = (
        {
            "outcome": "result_candidate",
            "summary": "Indice D probable ; date principale 28/08/2026.",
            "trace_refs": ["trace:1"],
        }
        if returned
        else None
    )
    return {
        "work_issue": {
            "issue_id": "work-prior-001",
            "case_ref": "project-a",
            "status": "review" if returned else "open",
            "version": 3 if returned else 1,
        },
        "comments": [],
        "hermes_runs": (
            [
                {
                    "run_id": "run-prior-001",
                    "status": "returned",
                    "normalized_return": normalized,
                }
            ]
            if returned
            else []
        ),
        "events": [],
    }


def _candidate() -> dict:
    return {
        "result_candidate_id": "result-candidate-prior-001",
        "result_digest": "b" * 64,
        "result_type": "workspace_pdf_metadata",
        "candidate_payload": {
            "index": "D",
            "date": "2026-08-28",
            "title": "Plan du rez-de-chaussée",
        },
        "confidence_note": "Cartouche lisible.",
        "known_limits": [],
        "open_questions": [],
    }


def _patch_prior_turn(monkeypatch, *, path: str = "Plan.pdf", returned: bool = True) -> None:
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {"project_id": project_id},
    )
    monkeypatch.setattr(
        hermes_handoff_store,
        "get_handoff_snapshot",
        lambda _conn, _handoff_id: _handoff(path),
    )
    monkeypatch.setattr(
        work_issues,
        "get_issue",
        lambda _conn, _issue_id: _work_projection(returned=returned),
    )
    monkeypatch.setattr(
        hermes_result_candidate,
        "get_result_candidate_for_run",
        lambda _conn, _run_id: _candidate() if returned else None,
    )


def test_dialogue_read_projects_existing_work_and_candidate_without_authority(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _pdf(tmp_path)
    _patch_prior_turn(monkeypatch)

    turn = workspace_dialogue.read_workspace_dialogue_turn(
        _Connection(),
        workspace_roots={"vault": tmp_path},
        project_id="project-a",
        workspace_ref="vault",
        relative_path="Plan.pdf",
        handoff_id="handoff-prior-001",
    )

    assert turn["turn_state"] == "returned"
    assert turn["work_issue_id"] == "work-prior-001"
    assert turn["latest_result"]["normalized_return"]["summary"].startswith("Indice D")
    assert turn["latest_result"]["result_candidate"]["candidate_payload"]["index"] == "D"
    assert turn["candidate_only"] is True
    assert turn["is_evidence"] is False
    assert turn["professional_truth"] is False


def test_dialogue_read_refuses_prior_handoff_bound_to_another_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _pdf(tmp_path)
    _patch_prior_turn(monkeypatch, path="Other.pdf")

    with pytest.raises(workspace_dialogue.WorkspaceDialogueConflict, match="another Workspace source"):
        workspace_dialogue.read_workspace_dialogue_turn(
            _Connection(),
            workspace_roots={"vault": tmp_path},
            project_id="project-a",
            workspace_ref="vault",
            relative_path="Plan.pdf",
            handoff_id="handoff-prior-001",
        )


def test_rework_preview_reuses_prior_candidate_only_as_bounded_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _pdf(tmp_path)
    _patch_prior_turn(monkeypatch)
    captured = {}

    def build_preview(_conn, **values):
        captured.update(values)
        return {
            "preview_digest": "c" * 64,
            "requested_effect": "read_only",
            "execution_authorized": False,
            "task_contract": {"task_contract_ref": "task-contract-candidate:abc"},
            "context_pack": {"context_pack_ref": "context-pack-candidate:def"},
            "qualification_kind": "workspace_pdf_metadata",
            "workspace_observation": {
                "workspace_file": {"digest_sha256": "d" * 64}
            },
            "workspace_source_ref": "workspace://vault/Plan.pdf?sha256=" + "d" * 64,
            "prepare_markdown_candidate": False,
            "question": "replacement question",
            "resolved_card_context_envelope": {"source_refs": []},
            "resolved_selected_context": [],
            "automatic_document_admission": False,
            "workspace_write_requested": False,
            "markdown_write_requested": False,
            "non_equivalences": [],
        }

    monkeypatch.setattr(
        workspace_qualification,
        "build_workspace_qualification_preview",
        build_preview,
    )

    preview = workspace_dialogue.build_workspace_rework_preview(
        _Connection(),
        workspace_roots={"vault": tmp_path},
        project_id="project-a",
        workspace_ref="vault",
        relative_path="Plan.pdf",
        prior_handoff_id="handoff-prior-001",
        instruction="Revérifie uniquement la date avec une seconde méthode.",
    )

    instruction = captured["user_instruction"]
    assert "previous result remains a candidate only" in instruction
    assert "Indice D probable" in instruction
    assert '"index":"D"' in instruction
    assert "Revérifie uniquement la date" in instruction
    assert captured["prepare_markdown"] is False
    assert preview["prior_handoff_id"] == "handoff-prior-001"
    assert preview["prior_result_candidate_id"] == "result-candidate-prior-001"
    assert preview["automatic_acceptance"] is False
    assert preview["execution_authorized"] is False


def test_rework_refuses_turn_without_hermes_return(tmp_path: Path, monkeypatch) -> None:
    _pdf(tmp_path)
    _patch_prior_turn(monkeypatch, returned=False)

    with pytest.raises(workspace_dialogue.WorkspaceDialogueConflict, match="no Hermes return"):
        workspace_dialogue.build_workspace_rework_preview(
            _Connection(),
            workspace_roots={"vault": tmp_path},
            project_id="project-a",
            workspace_ref="vault",
            relative_path="Plan.pdf",
            prior_handoff_id="handoff-prior-001",
            instruction="Refais la vérification de la date.",
        )


def _client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    install_workspace_qualification_routes(
        app,
        workspace_roots={"vault": tmp_path},
        with_connection=lambda operation: operation(_Connection()),
        require_read_key=lambda: None,
        require_editor_key=lambda: None,
        require_human_actor=lambda: "ifan",
    )
    return TestClient(app)


def _rework_preview() -> dict:
    return {
        "preview_digest": "e" * 64,
        "task_contract": {"task_contract_ref": "task-contract-candidate:rework"},
        "context_pack": {"context_pack_ref": "context-pack-candidate:rework"},
        "requested_effect": "read_only",
        "execution_authorized": False,
        "question": "targeted rework",
        "resolved_card_context_envelope": {
            "root_entity": {"entity_id": "project:project-a", "entity_type": "project"},
            "source_refs": ["workspace://vault/Plan.pdf?sha256=" + "f" * 64],
        },
        "resolved_selected_context": [],
        "dialogue_kind": "workspace_pdf_targeted_rework",
        "prior_handoff_id": "handoff-prior-001",
        "prior_result_candidate_id": "result-candidate-prior-001",
        "prior_result_digest": "b" * 64,
        "prior_context_truncated": False,
        "human_rework_instruction": "Revérifie la date.",
        "workspace_observation": {"workspace_file": {"digest_sha256": "f" * 64}},
        "workspace_source_ref": "workspace://vault/Plan.pdf?sha256=" + "f" * 64,
    }


def test_rework_submit_creates_new_handoff_without_mutating_prior_issue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _pdf(tmp_path)
    preview = _rework_preview()
    monkeypatch.setattr(
        workspace_dialogue,
        "build_workspace_rework_preview",
        lambda *_args, **_kwargs: preview,
    )
    submitted = {}

    def submit_handoff(_conn, **values):
        submitted.update(values)
        return {
            "handoff_id": "handoff-rework-002",
            "case_ref": "project-a",
            "task_contract_ref": preview["task_contract"]["task_contract_ref"],
            "context_pack_ref": preview["context_pack"]["context_pack_ref"],
            "preview_digest": preview["preview_digest"],
            "work_issue": {
                "issue_id": "work-rework-002",
                "assigned_to": "hermes",
                "status": "open",
            },
            "execution_started": False,
            "hermes_run_created": False,
            "status": "submitted_work_issue",
        }

    monkeypatch.setattr(hermes_handoff_store, "submit_handoff", submit_handoff)
    client = _client(tmp_path)
    response = client.post(
        "/cockpit/workspace-dialogue/rework/submit",
        json={
            "project_id": "project-a",
            "workspace_ref": "vault",
            "relative_path": "Plan.pdf",
            "prior_handoff_id": "handoff-prior-001",
            "instruction": "Revérifie la date.",
            "expected_preview_digest": preview["preview_digest"],
            "expected_task_contract_ref": preview["task_contract"]["task_contract_ref"],
            "expected_context_pack_ref": preview["context_pack"]["context_pack_ref"],
            "idempotency_key": "workspace-rework-submit-0001",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["handoff_id"] == "handoff-rework-002"
    assert body["work_issue"]["issue_id"] == "work-rework-002"
    assert body["prior_handoff_id"] == "handoff-prior-001"
    assert body["execution_authorized"] is False
    assert submitted["question"] == "targeted rework"
    assert submitted["include_declared_descendants"] is False


def test_rework_submit_rejects_stale_preview_before_new_handoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _pdf(tmp_path)
    preview = _rework_preview()
    monkeypatch.setattr(
        workspace_dialogue,
        "build_workspace_rework_preview",
        lambda *_args, **_kwargs: preview,
    )
    submitted = []
    monkeypatch.setattr(
        hermes_handoff_store,
        "submit_handoff",
        lambda *_args, **_kwargs: submitted.append(True),
    )
    client = _client(tmp_path)
    response = client.post(
        "/cockpit/workspace-dialogue/rework/submit",
        json={
            "project_id": "project-a",
            "workspace_ref": "vault",
            "relative_path": "Plan.pdf",
            "prior_handoff_id": "handoff-prior-001",
            "instruction": "Revérifie la date.",
            "expected_preview_digest": "0" * 64,
            "expected_task_contract_ref": preview["task_contract"]["task_contract_ref"],
            "expected_context_pack_ref": preview["context_pack"]["context_pack_ref"],
            "idempotency_key": "workspace-rework-stale-0001",
        },
    )

    assert response.status_code == 409
    assert submitted == []
