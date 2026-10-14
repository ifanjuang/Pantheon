"""Acceptance tests for reconstructible Workspace file metadata Cards."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from mvp_vertical.cockpit_composed import create_composed_cockpit_app


def _forbidden_connection():
    raise AssertionError("workspace file observation must not open a database connection")


def _client(root: Path) -> TestClient:
    return TestClient(
        create_composed_cockpit_app(
            connect_fn=_forbidden_connection,
            initialize_fn=None,
            api_key="read-key",
            workspace_roots={"agency-projects": root},
        )
    )


def _authorized_get(client: TestClient, path: str):
    return client.get(path, headers={"Authorization": "Bearer read-key"})


def _write_pdf(path: Path, payload: bytes = b"%PDF-1.4\nsynthetic-pdf\n%%EOF\n") -> None:
    path.write_bytes(payload)


def test_workspace_collection_projects_pdf_metadata_directly_on_existing_card(
    tmp_path: Path,
) -> None:
    plans = tmp_path / "Plans"
    plans.mkdir()
    pdf = plans / "Plan-RDC-D.pdf"
    _write_pdf(pdf)
    (plans / "Plan-RDC-D.yaml").write_text("not: a production schema\n", encoding="utf-8")

    client = _client(tmp_path)
    response = _authorized_get(
        client,
        "/cockpit/workspace-collections/agency-projects?path=Plans",
    )
    assert response.status_code == 200
    body = response.json()
    items = body["collection"]["items"]
    pdf_card = next(item for item in items if item["title"] == pdf.name)

    assert pdf_card["category"] == "PDF"
    assert pdf_card["workspace_entry_kind"] == "file"
    observed = pdf_card["workspace_file"]
    assert observed["filename"] == "Plan-RDC-D.pdf"
    assert observed["extension"] == ".pdf"
    assert observed["media_type"] == "application/pdf"
    assert observed["byte_size"] == pdf.stat().st_size
    assert observed["file_kind"] == "pdf"
    assert observed["filesystem_modified_at"].endswith("+00:00")
    assert observed["adjacent_document_sidecar"] == {
        "state": "present",
        "relative_path": "Plans/Plan-RDC-D.yaml",
        "parsed": False,
        "identity_mapping_resolved": False,
    }
    assert pdf_card["qualification"] == {
        "status": "workspace_observation_only",
        "identity_mapping": "not_resolved_by_workspace_projection",
        "automatic_document_admission": False,
    }
    assert pdf_card["authority"] == {
        "governed_identity": False,
        "is_evidence": False,
        "is_memory": False,
        "is_persisted": False,
    }
    assert ["Type MIME", "application/pdf"] in pdf_card["back"]
    assert ["Infos YAML adjacentes", "present"] in pdf_card["back"]

    assert body["cards_are_projections"] is True
    assert body["observation_persisted"] is False
    assert body["content_parsed"] is False
    assert body["hindsight_required"] is False

    serialized = json.dumps(body, ensure_ascii=False)
    for forbidden in (
        "digest_sha256",
        "document_family_id",
        "document_version_id",
        "current_for_execution",
        "current_contractual",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_workspace_file_observation_reconstructs_changed_size_and_timestamp_on_reread(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "Etude-G2.pdf"
    _write_pdf(pdf, b"%PDF-1.4\nversion-one\n%%EOF\n")
    client = _client(tmp_path)
    path = "/cockpit/workspace-collections/agency-projects"

    first = _authorized_get(client, path)
    assert first.status_code == 200
    first_card = next(item for item in first.json()["collection"]["items"] if item["title"] == pdf.name)

    _write_pdf(pdf, b"%PDF-1.4\nversion-two-with-more-content\n%%EOF\n")
    second = _authorized_get(client, path)
    assert second.status_code == 200
    second_card = next(item for item in second.json()["collection"]["items"] if item["title"] == pdf.name)

    assert first_card["entity_id"] == second_card["entity_id"]
    assert first_card["workspace_file"]["byte_size"] != second_card["workspace_file"]["byte_size"]
    assert second_card["workspace_file"]["byte_size"] == pdf.stat().st_size
    assert second.json()["observation_persisted"] is False


def test_workspace_observation_does_not_expose_hidden_or_symlink_entries(tmp_path: Path) -> None:
    visible = tmp_path / "Plans"
    visible.mkdir()
    _write_pdf(visible / "Plan.pdf")
    _write_pdf(tmp_path / ".secret.pdf")
    (tmp_path / "_VAULT.md").write_text("hidden", encoding="utf-8")
    (tmp_path / "link.pdf").symlink_to(visible / "Plan.pdf")

    client = _client(tmp_path)
    response = _authorized_get(client, "/cockpit/workspace-collections/agency-projects")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["collection"]["items"]]

    assert "Plans" in titles
    assert ".secret.pdf" not in titles
    assert "_VAULT.md" not in titles
    assert "link.pdf" not in titles


def test_workspace_observation_keeps_non_pdf_files_generic(tmp_path: Path) -> None:
    note = tmp_path / "Note.md"
    note.write_text("# Note\n", encoding="utf-8")
    client = _client(tmp_path)

    response = _authorized_get(client, "/cockpit/workspace-collections/agency-projects")
    assert response.status_code == 200
    card = next(item for item in response.json()["collection"]["items"] if item["title"] == note.name)

    assert card["category"] == "Fichier"
    assert card["workspace_file"]["media_type"] in {"text/markdown", "text/plain"}
    assert card["workspace_file"]["file_kind"] == "file"
    assert card["qualification"]["automatic_document_admission"] is False
