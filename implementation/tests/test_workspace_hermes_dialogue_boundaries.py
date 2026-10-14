from __future__ import annotations

from pathlib import Path

from mvp_vertical import (
    agency_data,
    hermes_handoff_store,
    hermes_result_candidate,
    work_issues,
    workspace_dialogue,
    workspace_qualification,
)


class _Connection:
    pass


def _patch_turn(monkeypatch, *, summary: str = "résumé", payload: dict | None = None) -> None:
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {"project_id": project_id},
    )
    monkeypatch.setattr(
        hermes_handoff_store,
        "get_handoff_snapshot",
        lambda _conn, _handoff_id: {
            "handoff_id": "handoff-prior-001",
            "work_issue_id": "work-prior-001",
            "case_ref": "project-a",
            "root_entity_id": "project:project-a",
            "root_entity_type": "project",
            "context_pack": {
                "source_refs": [
                    "workspace://vault/Archive/Plan.pdf?sha256=" + "a" * 64
                ]
            },
        },
    )
    monkeypatch.setattr(
        work_issues,
        "get_issue",
        lambda _conn, _issue_id: {
            "work_issue": {
                "issue_id": "work-prior-001",
                "status": "review",
                "version": 3,
            },
            "comments": [],
            "hermes_runs": [
                {
                    "run_id": "run-prior-001",
                    "status": "returned",
                    "normalized_return": {
                        "outcome": "result_candidate",
                        "summary": summary,
                        "trace_refs": ["trace:1"],
                    },
                }
            ],
            "events": [],
        },
    )
    monkeypatch.setattr(
        hermes_result_candidate,
        "get_result_candidate_for_run",
        lambda _conn, _run_id: {
            "result_candidate_id": "result-candidate-prior-001",
            "result_digest": "b" * 64,
            "candidate_payload": payload or {"index": "D"},
        },
    )


def test_historical_dialogue_read_does_not_require_source_file(tmp_path: Path, monkeypatch) -> None:
    _patch_turn(monkeypatch)
    # No Archive/Plan.pdf exists in tmp_path. The immutable handoff/result is
    # still readable; current bytes are required only by a future rework.
    turn = workspace_dialogue.read_workspace_dialogue_turn(
        _Connection(),
        workspace_roots={"vault": tmp_path},
        project_id="project-a",
        workspace_ref="vault",
        relative_path="Archive/Plan.pdf",
        handoff_id="handoff-prior-001",
    )
    assert turn["turn_state"] == "returned"
    assert turn["relative_path"] == "Archive/Plan.pdf"
    assert turn["source_basis_sha256"] == "a" * 64


def test_max_rework_context_stays_below_handoff_question_limit(tmp_path: Path, monkeypatch) -> None:
    archive = tmp_path / "Archive"
    archive.mkdir()
    (archive / "Plan.pdf").write_bytes(b"%PDF-1.7\ncurrent\n%%EOF\n")
    _patch_turn(
        monkeypatch,
        summary="s" * 20_000,
        payload={"large": "p" * 20_000},
    )
    captured: dict = {}

    def build_preview(_conn, **values):
        captured.update(values)
        return {
            "preview_digest": "c" * 64,
            "requested_effect": "read_only",
            "execution_authorized": False,
            "task_contract": {"task_contract_ref": "task-contract-candidate:bounded"},
            "context_pack": {"context_pack_ref": "context-pack-candidate:bounded"},
            "qualification_kind": "workspace_pdf_metadata",
            "workspace_observation": {"workspace_file": {"digest_sha256": "d" * 64}},
            "workspace_source_ref": "workspace://vault/Archive/Plan.pdf?sha256=" + "d" * 64,
            "prepare_markdown_candidate": False,
            "question": "replacement",
            "resolved_card_context_envelope": {"source_refs": []},
            "resolved_selected_context": [],
            "automatic_document_admission": False,
            "workspace_write_requested": False,
            "markdown_write_requested": False,
            "non_equivalences": [],
        }

    monkeypatch.setattr(workspace_qualification, "build_workspace_qualification_preview", build_preview)
    preview = workspace_dialogue.build_workspace_rework_preview(
        _Connection(),
        workspace_roots={"vault": tmp_path},
        project_id="project-a",
        workspace_ref="vault",
        relative_path="Archive/Plan.pdf",
        prior_handoff_id="handoff-prior-001",
        instruction="i" * 2_000,
    )

    # workspace_qualification adds this value to a larger question capped at 8000.
    # Keep ample room for its fixed qualification instructions and source basis.
    assert len(captured["user_instruction"]) < 6_000
    assert "[truncated for bounded rework context]" in captured["user_instruction"]
    assert "payload omitted" in captured["user_instruction"]
    assert preview["prior_context_truncated"] is True
