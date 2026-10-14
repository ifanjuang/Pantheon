"""Acceptance tests for explicit Workspace PDF -> Hermes qualification preparation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from mvp_vertical import agency_data, hermes_handoff_store, workspace_collection_read
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def _write_pdf(path: Path, text: str = "synthetic-v1") -> bytes:
    payload = f"%PDF-1.4\n{text}\n%%EOF\n".encode()
    path.write_bytes(payload)
    return payload


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_composed_cockpit_app(
            connect_fn=_Connection,
            initialize_fn=None,
            api_key="read-key",
            editor_api_key="editor-key",
            workspace_roots={"agency-projects": tmp_path},
        )
    )


def _preview_body(path: str = "Plans/Plan-RDC-D.pdf", *, prepare_markdown: bool = True) -> dict:
    return {
        "project_id": "project-a",
        "workspace_ref": "agency-projects",
        "relative_path": path,
        "prepare_markdown": prepare_markdown,
        "user_instruction": "Repère en priorité les informations du cartouche.",
    }


def _headers(key: str = "read-key") -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def test_exact_observation_hashes_only_when_requested(tmp_path: Path) -> None:
    pdf = tmp_path / "Plan.pdf"
    payload = _write_pdf(pdf)
    roots = workspace_collection_read.prepare_workspace_roots({"vault": tmp_path})

    cheap = workspace_collection_read.observe_workspace_file(
        roots,
        "vault",
        "Plan.pdf",
        include_digest=False,
    )
    assert "digest_sha256" not in cheap["workspace_file"]

    exact = workspace_collection_read.observe_workspace_file(
        roots,
        "vault",
        "Plan.pdf",
        include_digest=True,
    )
    assert exact["workspace_file"]["digest_sha256"] == hashlib.sha256(payload).hexdigest()
    assert exact["governed_identity"] is False
    assert exact["observation_persisted"] is False


def test_preview_binds_exact_pdf_to_explicit_project_without_admission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plans = tmp_path / "Plans"
    plans.mkdir()
    pdf = plans / "Plan-RDC-D.pdf"
    payload = _write_pdf(pdf)
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {"project_id": project_id},
    )
    client = _client(tmp_path)

    response = client.post(
        "/cockpit/workspace-qualifications/preview",
        headers=_headers(),
        json=_preview_body(),
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["requested_effect"] == "read_only"
    assert body["execution_authorized"] is False
    assert body["qualification_kind"] == "workspace_pdf_metadata"
    assert body["prepare_markdown_candidate"] is True
    assert body["automatic_document_admission"] is False
    assert body["workspace_write_requested"] is False
    assert body["markdown_write_requested"] is False
    assert body["context_pack"]["root_entity"] == {
        "entity_id": "project:project-a",
        "entity_type": "project",
    }
    assert body["workspace_observation"]["workspace_file"]["digest_sha256"] == hashlib.sha256(payload).hexdigest()
    assert body["workspace_source_ref"].startswith(
        "workspace://agency-projects/Plans/Plan-RDC-D.pdf?sha256="
    )
    assert body["context_pack"]["source_refs"] == [body["workspace_source_ref"]]
    assert "do not write or overwrite any workspace file" in body["question"]
    assert "Do not invent a Document family/version identity" in body["question"]
    assert not (plans / "document.yaml").exists()
    assert not (plans / "Plan-RDC-D.md").exists()


def test_submit_rejects_stale_pdf_basis_before_creating_work(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plans = tmp_path / "Plans"
    plans.mkdir()
    pdf = plans / "Plan-RDC-D.pdf"
    _write_pdf(pdf, "version-one")
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {"project_id": project_id},
    )
    submitted = []
    monkeypatch.setattr(
        hermes_handoff_store,
        "submit_handoff",
        lambda *_args, **_kwargs: submitted.append(True),
    )
    client = _client(tmp_path)

    preview_response = client.post(
        "/cockpit/workspace-qualifications/preview",
        headers=_headers(),
        json=_preview_body(),
    )
    preview = preview_response.json()
    _write_pdf(pdf, "version-two-changed")

    response = client.post(
        "/cockpit/workspace-qualifications/submit",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json={
            **_preview_body(),
            "expected_preview_digest": preview["preview_digest"],
            "expected_task_contract_ref": preview["task_contract"]["task_contract_ref"],
            "expected_context_pack_ref": preview["context_pack"]["context_pack_ref"],
            "idempotency_key": "workspace-qualify-stale-0001",
        },
    )
    assert response.status_code == 409
    assert submitted == []
    assert not (plans / "document.yaml").exists()
    assert not (plans / "Plan-RDC-D.md").exists()


def test_submit_reuses_existing_handoff_store_and_does_not_start_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plans = tmp_path / "Plans"
    plans.mkdir()
    _write_pdf(plans / "Plan-RDC-D.pdf")
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {"project_id": project_id},
    )
    observed = {}

    def submit_handoff(_conn, **values):
        observed.update(values)
        return {
            "handoff_id": "handoff-workspace-1",
            "case_ref": "project-a",
            "task_contract_ref": values["preview"]["task_contract"]["task_contract_ref"],
            "context_pack_ref": values["preview"]["context_pack"]["context_pack_ref"],
            "preview_digest": values["preview"]["preview_digest"],
            "work_issue": {
                "issue_id": "work-workspace-1",
                "assigned_to": "hermes",
                "status": "open",
                "requested_effect": "read_only",
            },
            "execution_started": False,
            "hermes_run_created": False,
            "status": "submitted_work_issue",
        }

    monkeypatch.setattr(hermes_handoff_store, "submit_handoff", submit_handoff)
    client = _client(tmp_path)
    preview = client.post(
        "/cockpit/workspace-qualifications/preview",
        headers=_headers(),
        json=_preview_body(),
    ).json()

    response = client.post(
        "/cockpit/workspace-qualifications/submit",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json={
            **_preview_body(),
            "expected_preview_digest": preview["preview_digest"],
            "expected_task_contract_ref": preview["task_contract"]["task_contract_ref"],
            "expected_context_pack_ref": preview["context_pack"]["context_pack_ref"],
            "idempotency_key": "workspace-qualify-submit-0001",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "submitted_work_issue"
    assert body["work_issue"]["assigned_to"] == "hermes"
    assert body["execution_started"] is False
    assert body["hermes_run_created"] is False
    assert body["execution_authorized"] is False
    assert body["workspace_write_requested"] is False
    assert body["markdown_write_requested"] is False
    assert observed["actor"] == "ifan"
    assert observed["include_declared_descendants"] is False
    assert observed["card_context_envelope"]["source_refs"] == [
        preview["workspace_source_ref"]
    ]
    assert not (plans / "document.yaml").exists()
    assert not (plans / "Plan-RDC-D.md").exists()


def test_preview_refuses_non_pdf_and_path_traversal(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "note.md").write_text("# Note\n", encoding="utf-8")
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {"project_id": project_id},
    )
    client = _client(tmp_path)

    non_pdf = client.post(
        "/cockpit/workspace-qualifications/preview",
        headers=_headers(),
        json=_preview_body("note.md", prepare_markdown=False),
    )
    assert non_pdf.status_code == 422

    traversal = client.post(
        "/cockpit/workspace-qualifications/preview",
        headers=_headers(),
        json=_preview_body("../outside.pdf", prepare_markdown=False),
    )
    assert traversal.status_code == 422
