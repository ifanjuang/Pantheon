from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "implementation" / "workspace_cockpit" / "hindsight_producer.py"


def _module():
    spec = importlib.util.spec_from_file_location("workspace_hindsight_producer", PRODUCER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _snapshot(card: dict | None) -> dict:
    return {
        "workspaces": [
            {
                "name": "Affaires",
                "available": True,
                "cards": [] if card is None else [card],
                "errors": [],
            }
        ]
    }


def _card(path: str = "Notice.pdf", *, status: str = "COMPLETE", representation: str = "source") -> dict:
    return {
        "workspace": "Affaires",
        "kind": "document",
        "path": path,
        "name": Path(path).name,
        "status": status,
        "document_id": "doc-notice",
        "title": "Notice technique",
        "project": "VERGER",
        "scope_project": "VERGER",
        "project_declared": "VERGER",
        "project_scope_conflict": False,
        "project_scope_source": "cartouche",
        "cartouche": ".Notice.pdf.md",
        "cartouche_enrichment_admitted": True,
        "parent_path": str(Path(path).parent) if Path(path).parent != Path(".") else "",
        "folder_ancestry": list(Path(path).parts[:-1]),
        "document_identity_source": "cartouche",
        "phase": "DCE",
        "document_type": "NOTICE",
        "index": "C",
        "document_date": "2026-09-12",
        "issuer": "agency",
        "tags": ["structure", "ossature bois"],
        "summary": "Derived cartouche summary that must not become source metadata.",
        "source_sha256": None,
        "source_sha256_verified": None,
        "hindsight_eligible": status in {"COMPLETE", "FOLDER_SCOPED", "PENDING_SCOPE"},
        "hindsight_representation_candidate": representation,
    }


class FakeClient:
    def __init__(self, statuses: list[str] | None = None) -> None:
        self.bank_id = "affaires-test"
        self.statuses = list(statuses or ["completed"])
        self.retains: list[dict] = []
        self.polls: list[str] = []
        self.tag_updates: list[dict] = []
        self.deleted_documents: list[str] = []

    def retain_file(self, source: Path, **kwargs):
        self.retains.append({"source": source, **kwargs})
        return f"op-{len(self.retains)}"

    def operation_status(self, operation_id: str):
        self.polls.append(operation_id)
        status = self.statuses.pop(0) if self.statuses else "completed"
        return {"operation_id": operation_id, "status": status, "error_message": None}

    def get_document(self, document_id: str):
        return {"id": document_id, "original_text": "Contenu PDF correctement extrait."}

    def update_document_tags(self, document_id: str, tags: list[str]):
        self.tag_updates.append({"document_id": document_id, "tags": list(tags)})

    def delete_document(self, document_id: str):
        self.deleted_documents.append(document_id)


def _row(db: Path) -> dict:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM hindsight_sync").fetchone()
        assert row is not None
        return dict(row)
    finally:
        con.close()


def test_source_candidate_submits_then_completes_without_duplicate_retain(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-source-v1")
    db = tmp_path / "state" / "index.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
        max_submits_per_reconcile=4,
    )

    card = _card()
    card["revision_mode"] = "supersedes"
    card["revision_of"] = "doc-older"
    first = producer.reconcile(_snapshot(card))
    assert first["submitted"] == 1
    assert len(client.retains) == 1
    call = client.retains[0]
    assert call["source"] == source
    assert call["document_id"] == "doc-notice:source"
    assert call["metadata"]["pantheon_document_id"] == "doc-notice"
    assert call["metadata"]["project_hint"] == "VERGER"
    assert call["metadata"]["cartouche_path"] == ".Notice.pdf.md"
    assert call["metadata"]["cartouche_document_id"] == "doc-notice"
    assert call["metadata"]["cartouche_project"] == "VERGER"
    assert call["metadata"]["cartouche_phase"] == "DCE"
    assert call["metadata"]["cartouche_document_type"] == "NOTICE"
    assert call["metadata"]["cartouche_index"] == "C"
    assert call["metadata"]["cartouche_document_date"] == "2026-09-12"
    assert call["metadata"]["cartouche_issuer"] == "agency"
    assert "document_index" not in call["metadata"]
    assert "document_date" not in call["metadata"]
    assert "revision_mode" not in call["metadata"]
    assert "revision_of" not in call["metadata"]
    assert "summary" not in call["metadata"]
    assert "project_hint:verger" in call["tags"]
    assert "tag:ossature-bois" in call["tags"]
    assert _row(db)["status"] == "SUBMITTED"

    same_card = _card()
    same_card["revision_mode"] = "supersedes"
    same_card["revision_of"] = "doc-older"
    second = producer.reconcile(_snapshot(same_card))
    assert second["completed"] == 1
    assert client.polls == ["op-1"]
    assert len(client.retains) == 1
    assert _row(db)["status"] == "COMPLETED"
    assert client.tag_updates[-1]["document_id"] == "doc-notice:source"
    assert "ocr:raw" in client.tag_updates[-1]["tags"]


def test_raw_status_preserves_existing_derived_ocr_state() -> None:
    module = _module()
    assert module._with_raw_ocr_status(["project:alpha", "ocr:partial"]) == [
        "ocr:partial",
        "project:alpha",
    ]
    assert module._with_raw_ocr_status(["ocr:complete"]) == ["ocr:complete"]


def test_invalid_cartouche_fallback_does_not_emit_cartouche_metadata(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Projet Alpha" / "Notice.pdf"
    source.parent.mkdir()
    source.write_bytes(b"%PDF-source")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
        source_kind="project-sync",
    )
    card = _card("Projet Alpha/Notice.pdf", status="CHECK")
    card.update(
        workspace="project-platform",
        document_id="path-fallback",
        document_identity_source="workspace_path_fallback",
        scope_project="Projet Alpha",
        project="Projet Alpha",
        project_declared="Wrong project",
        project_scope_source="top_level_folder",
        cartouche=".Notice.pdf.md",
        cartouche_enrichment_admitted=False,
        hindsight_eligible=True,
        hindsight_representation_candidate="source",
    )

    producer.reconcile(_snapshot(card))

    metadata = client.retains[0]["metadata"]
    assert not any(key.startswith("cartouche_") for key in metadata)
    assert f"scope:project:{module._project_scope_token('Projet Alpha')}" in client.retains[0]["tags"]


def test_workspace_provenance_is_derived_instead_of_hardcoded(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-source")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
        source_kind="project-sync",
    )
    card = _card()
    card["workspace"] = "project-platform"

    producer.reconcile(_snapshot(card))

    call = client.retains[0]
    assert call["context"].startswith("project-platform professional source document")
    assert "workspace:project-platform" in call["tags"]
    assert "source:project-sync" in call["tags"]
    assert call["metadata"]["source_space"] == "project-platform"
    assert call["metadata"]["source_kind"] == "project-sync"


def test_tag_normalization_keeps_french_names_readable(tmp_path: Path) -> None:
    module = _module()
    assert module._tag_value("Médiathèque André") == "mediatheque-andre"


def test_pdf_cid_garbage_is_flagged_for_manual_per_file_ocr(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-cid-garbage")
    client = FakeClient(["completed"])
    client.get_document = lambda document_id: {
        "id": document_id,
        "original_text": "(cid:1)(cid:2)(cid:3)(cid:4)(cid:5)" * 20,
    }
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    snapshot = _snapshot(_card())
    result = producer.reconcile(snapshot)
    card = snapshot["workspaces"][0]["cards"][0]

    assert result["completed"] == 1
    assert result["ocr_needed"] == 1
    assert result["ocr_mode"] == "manual-per-file"
    assert card["hindsight_extraction_quality"] == "OCR_NEEDED"
    assert card["hindsight_ocr_needed"] is True
    assert card["hindsight_ocr_mode"] == "manual-per-file"


def test_pdf_with_usable_text_does_not_request_ocr(tmp_path: Path) -> None:
    module = _module()
    assert module._needs_ocr("Plan de niveau avec cotes et légende lisibles.") is False
    assert module._needs_ocr("") is True


def test_pdf_parse_failure_without_content_is_classified_for_manual_ocr(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-image-only")

    class EmptyPdfClient(FakeClient):
        def operation_status(self, operation_id: str):
            self.polls.append(operation_id)
            return {
                "operation_id": operation_id,
                "status": "failed",
                "error_message": "Failed to parse: No content extracted from 'Notice.pdf'",
            }

    client = EmptyPdfClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    snapshot = _snapshot(_card())
    result = producer.reconcile(snapshot)
    card = snapshot["workspaces"][0]["cards"][0]

    assert result["failed"] == 0
    assert result["ocr_needed"] == 1
    assert card["hindsight_status"] == "OCR_NEEDED"
    assert card["hindsight_extraction_quality"] == "OCR_NEEDED"
    assert card["hindsight_ocr_needed"] is True
    assert len(client.retains) == 1

    producer.reconcile(_snapshot(_card()))
    assert len(client.retains) == 1


def test_transient_document_quality_read_error_is_retried_without_retain(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-readable")

    class EventualDocumentClient(FakeClient):
        def __init__(self) -> None:
            super().__init__(["completed"])
            self.document_reads = 0

        def get_document(self, document_id: str):
            self.document_reads += 1
            if self.document_reads == 1:
                raise RuntimeError('Hindsight HTTP 404: {"detail":"Document not found"}')
            return {"id": document_id, "original_text": "Texte PDF correctement extrait."}

    client = EventualDocumentClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    first_check = _snapshot(_card())
    producer.reconcile(first_check)
    assert first_check["workspaces"][0]["cards"][0]["hindsight_extraction_quality"] == "CHECK_ERROR"

    recovered = _snapshot(_card())
    result = producer.reconcile(recovered)
    card = recovered["workspaces"][0]["cards"][0]
    assert result["failed"] == 0
    assert result["ocr_needed"] == 0
    assert card["hindsight_extraction_quality"] == "GOOD"
    assert client.document_reads == 2
    assert len(client.retains) == 1


def test_synced_source_must_be_identical_across_required_observations(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-partial")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
        settle_observations=2,
    )

    first = producer.reconcile(_snapshot(_card()))
    assert first["settling"] == 1
    assert client.retains == []

    source.write_bytes(b"%PDF-complete")
    changed = producer.reconcile(_snapshot(_card()))
    assert changed["settling"] == 1
    assert client.retains == []

    stable = producer.reconcile(_snapshot(_card()))
    assert stable["settling"] == 0
    assert len(client.retains) == 1


def test_folder_scoped_candidate_carries_project_and_ancestry_tags(tmp_path: Path) -> None:
    module = _module()
    relative = "Projet Alpha/DCE/Structure/Plan.pdf"
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.write_bytes(b"%PDF-folder-scoped")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
        source_kind="project-sync",
    )
    card = _card(relative, status="FOLDER_SCOPED")
    card.update(
        workspace="project-platform",
        document_id="path-123",
        project="Projet Alpha",
        scope_project="Projet Alpha",
        project_declared=None,
        project_scope_source="top_level_folder",
        document_identity_source="workspace_path",
        document_family_hint="family-example",
        filename_revision_hint="B",
    )

    producer.reconcile(_snapshot(card))

    call = client.retains[0]
    assert f"scope:project:{module._project_scope_token('Projet Alpha')}" in call["tags"]
    assert "folder:projet-alpha" in call["tags"]
    assert "folder:projet-alpha-dce" in call["tags"]
    assert "folder:projet-alpha-dce-structure" in call["tags"]
    assert "family:family-example" in call["tags"]
    assert "revision_hint:b" in call["tags"]
    assert call["metadata"]["parent_path"] == "Projet Alpha/DCE/Structure"
    assert call["metadata"]["folder_ancestry"] == "Projet Alpha / DCE / Structure"


def test_top_level_folder_scope_cannot_be_overridden_by_cartouche_project(tmp_path: Path) -> None:
    module = _module()
    relative = "Projet Alpha/Plans/Plan.pdf"
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.write_bytes(b"%PDF-folder-scope")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
        source_kind="project-sync",
    )
    card = _card(relative)
    card.update(
        workspace="project-platform",
        project="Autre Projet",
        project_declared="Autre Projet",
        scope_project="Projet Alpha",
        project_scope_source="top_level_folder",
        project_scope_conflict=True,
    )

    producer.reconcile(_snapshot(card))

    call = client.retains[0]
    assert f"scope:project:{module._project_scope_token('Projet Alpha')}" in call["tags"]
    assert f"scope:project:{module._project_scope_token('Autre Projet')}" not in call["tags"]
    assert "project_hint:autre-projet" in call["tags"]
    assert call["metadata"]["scope_project"] == "Projet Alpha"
    assert call["metadata"]["project_declared"] == "Autre Projet"
    assert call["metadata"]["project_scope_conflict"] == "true"


def test_unclassified_source_is_ingested_only_in_pending_scope(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "A-classer.pdf").write_bytes(b"%PDF-pending")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
    )
    card = _card("A-classer.pdf", status="PENDING_SCOPE")
    card.update(
        workspace="project-platform",
        document_id="path-pending",
        project=None,
        scope_project=None,
        project_declared=None,
        project_scope_source="pending_identification",
        document_identity_source="workspace_path",
    )

    producer.reconcile(_snapshot(card))

    assert "scope:pending-identification" in client.retains[0]["tags"]
    assert not any(tag.startswith("scope:project:") for tag in client.retains[0]["tags"])


def test_source_change_waits_for_active_operation_before_replacement(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-source-v1")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["processing", "completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    source.write_bytes(b"%PDF-source-v2")

    active = producer.reconcile(_snapshot(_card()))
    assert active["pending"] == 1
    assert len(client.retains) == 1

    replaced = producer.reconcile(_snapshot(_card()))
    assert replaced["submitted"] == 1
    assert len(client.retains) == 2
    assert client.retains[1]["document_id"] == "doc-notice:source"
    assert _row(db)["operation_id"] == "op-2"


def test_check_and_cartouche_candidates_never_submit_source_file(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card(status="CHECK")))
    producer.reconcile(_snapshot(_card(representation="cartouche")))
    assert client.retains == []


def test_missing_document_is_quarantined_then_deleted_remotely(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    quarantined = producer.reconcile(_snapshot(None))

    assert quarantined["quarantined"] == 1
    assert quarantined["delete_missing"] == "two-observation-quarantine"
    assert _row(db)["status"] == "QUARANTINED"
    assert _row(db)["missing_observations"] == 1
    assert client.tag_updates[-1] == {
        "document_id": "doc-notice:source",
        "tags": [
            "lifecycle:quarantined",
            "workspace:affaires",
            "reason:source-missing",
        ],
    }

    archived = producer.reconcile(_snapshot(None))
    assert archived["archived"] == 1
    assert _row(db)["status"] == "ARCHIVED"
    assert _row(db)["missing_observations"] == 2
    assert client.deleted_documents == ["doc-notice:source"]


def test_quarantined_document_is_restored_without_duplicate_retain(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client
    )

    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(None))
    restored = producer.reconcile(_snapshot(_card()))

    assert restored["completed"] == 1
    assert len(client.retains) == 1
    assert client.deleted_documents == []
    assert _row(db)["missing_observations"] == 0
    assert client.tag_updates[-1]["tags"] == client.retains[0]["tags"]


def test_unavailable_workspace_never_advances_missing_lifecycle(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client
    )
    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(_card()))

    unavailable = _snapshot(None)
    unavailable["workspaces"][0]["available"] = False
    producer.reconcile(unavailable)

    assert _row(db)["status"] == "COMPLETED"
    assert _row(db)["missing_observations"] == 0
    assert client.deleted_documents == []


def test_completed_document_becomes_blocked_when_bundle_still_exists_but_is_ineligible(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    blocked = producer.reconcile(_snapshot(_card(status="CHECK")))

    assert blocked["blocked"] == 1
    assert _row(db)["status"] == "BLOCKED"


def test_candidate_path_must_resolve_inside_exact_workspace_root(tmp_path: Path) -> None:
    module = _module()
    root = tmp_path / "AFFAIRES"
    root.mkdir()
    outside = tmp_path / "escape.pdf"
    outside.write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", root)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card("../escape.pdf")))
    assert client.retains == []


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def test_http_client_matches_hindsight_0101_file_retain_multipart_contract(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"EXACT-PDF-BYTES")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response({"operation_ids": ["op-123"]})

    client = module.HindsightHTTPClient(
        "http://127.0.0.1:8888",
        "affaires",
        parser="markitdown",
        timeout_seconds=7,
    )
    with patch.object(module, "urlopen", fake_urlopen):
        operation_id = client.retain_file(
            source,
            document_id="doc-notice:source",
            context="AFFAIRES professional source document",
            tags=["workspace:affaires"],
            metadata={"pantheon_document_id": "doc-notice"},
        )

    assert operation_id == "op-123"
    request = captured["request"]
    assert request.full_url.endswith("/v1/default/banks/affaires/files/retain")
    assert captured["timeout"] == 7
    assert request.get_header("Content-type").startswith("multipart/form-data; boundary=")
    body = request.data
    assert b'name="request"' in body
    assert b'name="files"; filename="Notice.pdf"' in body
    assert b"EXACT-PDF-BYTES" in body
    assert b'"parser":"markitdown"' in body
    assert b'"document_id":"doc-notice:source"' in body
    assert b'"timestamp":"unset"' in body


def test_http_client_updates_only_document_tags_for_same_project_move() -> None:
    module = _module()
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response({"success": True})

    client = module.HindsightHTTPClient(
        "http://127.0.0.1:8888", "PROJECTS", timeout_seconds=9
    )
    with patch.object(module, "urlopen", fake_urlopen):
        client.update_document_tags(
            "doc-1:source",
            ["source:project-sync", "scope:project:alpha", "folder:alpha-dce"],
        )

    request = captured["request"]
    assert request.method == "PATCH"
    assert request.full_url.endswith(
        "/v1/default/banks/PROJECTS/documents/doc-1%3Asource"
    )
    assert json.loads(request.data) == {
        "tags": ["source:project-sync", "scope:project:alpha", "folder:alpha-dce"]
    }
    assert captured["timeout"] == 9


def test_http_client_deletes_one_exact_hindsight_document() -> None:
    module = _module()
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response({"success": True})

    client = module.HindsightHTTPClient(
        "http://127.0.0.1:8888", "PROJECTS", timeout_seconds=9
    )
    with patch.object(module, "urlopen", fake_urlopen):
        client.delete_document("doc-1:source")

    assert captured["request"].method == "DELETE"
    assert captured["request"].full_url.endswith(
        "/v1/default/banks/PROJECTS/documents/doc-1%3Asource"
    )
    assert captured["timeout"] == 9


def test_poll_error_is_persisted_without_resubmitting_active_operation(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"

    class PollFailureClient(FakeClient):
        def operation_status(self, operation_id: str):
            self.polls.append(operation_id)
            raise RuntimeError("temporary Hindsight outage")

    client = PollFailureClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    state = producer.reconcile(_snapshot(_card()))

    assert len(client.retains) == 1
    assert client.polls == ["op-1"]
    assert state["submitted"] == 1
    assert _row(db)["last_error"] == "temporary Hindsight outage"


def test_http_client_rejects_oversize_source_before_buffering_or_network(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"12345")
    client = module.HindsightHTTPClient(
        "http://127.0.0.1:8888",
        "affaires",
        max_file_bytes=4,
    )

    with patch.object(module, "urlopen") as mocked:
        try:
            client.retain_file(
                source,
                document_id="doc-notice:source",
                context="AFFAIRES professional source document",
                tags=["workspace:affaires"],
                metadata={"pantheon_document_id": "doc-notice"},
            )
        except RuntimeError as exc:
            assert "exceeds Hindsight upload bound" in str(exc)
        else:
            raise AssertionError("oversize source should be rejected")

    mocked.assert_not_called()



def test_source_only_file_gets_technical_identity_and_is_retained(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-source-only")
    db = tmp_path / "state.sqlite3"
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    card = _card(status="SOURCE_ONLY")
    card["document_id"] = None
    card["hindsight_eligible"] = True
    card["hindsight_representation_candidate"] = "source"
    producer.reconcile(_snapshot(card))

    assert len(client.retains) == 1
    technical_id = card["technical_document_id"]
    assert technical_id.startswith("doc_auto_")
    assert card["identity_origin"] == "technical"
    assert client.retains[0]["document_id"] == f"{technical_id}:source"
    assert client.retains[0]["metadata"]["identity_origin"] == "technical"


def test_source_only_move_reuses_unique_technical_identity(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-same-bytes")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    first = _card(status="SOURCE_ONLY")
    first["document_id"] = None
    first["hindsight_eligible"] = True
    first["hindsight_representation_candidate"] = "source"
    producer.reconcile(_snapshot(first))
    first_id = first["technical_document_id"]

    source.rename(tmp_path / "Renamed.pdf")
    moved = _card("Renamed.pdf", status="SOURCE_ONLY")
    moved["document_id"] = None
    moved["hindsight_eligible"] = True
    moved["hindsight_representation_candidate"] = "source"
    producer.reconcile(_snapshot(moved))

    assert moved["technical_document_id"] == first_id
    assert moved["hindsight_document_id"] == f"{first_id}:source"
    assert len(client.retains) == 1
    assert client.tag_updates == [
        {"document_id": f"{first_id}:source", "tags": client.retains[0]["tags"]}
    ]


def test_source_only_cross_root_move_does_not_infer_technical_identity_continuity(tmp_path: Path) -> None:
    module = _module()
    active = tmp_path / "AFFAIRES"
    secondary = tmp_path / "SECONDARY"
    active_source = active / "VERGER" / "Notice.pdf"
    active_source.parent.mkdir(parents=True)
    secondary.mkdir(parents=True)
    active_source.write_bytes(b"%PDF-same-archived-bytes")
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", active), ("Secondary", secondary)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
    )

    first = _card("VERGER/Notice.pdf", status="FOLDER_SCOPED")
    first.update(
        workspace="Affaires",
        document_id=None,
        project="VERGER",
        scope_project="VERGER",
        project_declared=None,
        project_scope_source="top_level_folder",
        hindsight_eligible=True,
        hindsight_representation_candidate="source",
    )
    producer.reconcile(
        {
            "workspaces": [
                {"name": "Affaires", "available": True, "cards": [first], "errors": []},
                {"name": "Secondary", "available": True, "cards": [], "errors": []},
            ]
        }
    )
    first_id = first["technical_document_id"]

    secondary_source = secondary / "VERGER" / "Notice.pdf"
    secondary_source.parent.mkdir(parents=True)
    active_source.rename(secondary_source)
    moved = _card("VERGER/Notice.pdf", status="FOLDER_SCOPED")
    moved.update(
        workspace="Secondary",
        document_id=None,
        project="VERGER",
        scope_project="VERGER",
        project_declared=None,
        project_scope_source="top_level_folder",
        hindsight_eligible=True,
        hindsight_representation_candidate="source",
    )
    producer.reconcile(
        {
            "workspaces": [
                {"name": "Affaires", "available": True, "cards": [], "errors": []},
                {"name": "Secondary", "available": True, "cards": [moved], "errors": []},
            ]
        }
    )

    assert moved["technical_document_id"] != first_id
    assert moved["identity_origin"] == "technical"
    assert moved["hindsight_document_id"] != f"{first_id}:source"


def test_cross_project_move_requires_confirmation_and_keeps_old_memory_scope(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Projet Alpha" / "Notice.pdf"
    source.parent.mkdir()
    source.write_bytes(b"%PDF-cross-project")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)], state_db=db, client=client
    )

    first = _card("Projet Alpha/Notice.pdf", status="FOLDER_SCOPED")
    first.update(
        workspace="project-platform",
        document_id=None,
        project="Projet Alpha",
        scope_project="Projet Alpha",
        project_declared=None,
        project_scope_source="top_level_folder",
    )
    producer.reconcile(_snapshot(first))
    first_id = first["technical_document_id"]

    target = tmp_path / "Projet Beta" / "Notice.pdf"
    target.parent.mkdir()
    source.rename(target)
    moved = _card("Projet Beta/Notice.pdf", status="FOLDER_SCOPED")
    moved.update(
        workspace="project-platform",
        document_id=None,
        project="Projet Beta",
        scope_project="Projet Beta",
        project_declared=None,
        project_scope_source="top_level_folder",
    )
    producer.reconcile(_snapshot(moved))

    assert moved["technical_document_id"] == first_id
    assert moved["hindsight_status"] == "RECLASSIFICATION_REQUIRED"
    assert moved["hindsight_reclassification_required"] is True
    assert moved["hindsight_previous_project"] == "Projet Alpha"
    assert moved["hindsight_requested_project"] == "Projet Beta"
    assert len(client.retains) == 1
    assert client.tag_updates == []


def test_confirmed_cross_project_move_reuses_identity_and_reprocesses(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Projet Alpha" / "Notice.pdf"
    source.parent.mkdir()
    source.write_bytes(b"%PDF-confirmed-cross-project")
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("project-platform", tmp_path)], state_db=tmp_path / "state.sqlite3", client=client
    )

    first = _card("Projet Alpha/Notice.pdf", status="FOLDER_SCOPED")
    first.update(
        workspace="project-platform",
        document_id=None,
        project="Projet Alpha",
        scope_project="Projet Alpha",
        project_declared=None,
        project_scope_source="top_level_folder",
    )
    producer.reconcile(_snapshot(first))
    first_id = first["technical_document_id"]

    target = tmp_path / "Projet Beta" / "Notice.pdf"
    target.parent.mkdir()
    source.rename(target)
    moved = _card("Projet Beta/Notice.pdf", status="COMPLETE")
    moved.update(
        workspace="project-platform",
        document_id=first_id,
        project="Projet Beta",
        scope_project="Projet Beta",
        project_declared="Projet Beta",
        project_scope_source="top_level_folder",
        scope_move_confirmed=True,
    )
    producer.reconcile(_snapshot(moved))

    assert moved["technical_document_id"] == first_id
    assert len(client.retains) == 1
    assert client.tag_updates[-1]["document_id"] == f"{first_id}:source"
    assert f"scope:project:{module._project_scope_token('Projet Beta')}" in client.tag_updates[-1]["tags"]


def test_identical_simultaneous_copy_gets_distinct_technical_identity(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-identical")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
        max_submits_per_reconcile=4,
    )

    first = _card(status="SOURCE_ONLY")
    first["document_id"] = None
    first["hindsight_eligible"] = True
    first["hindsight_representation_candidate"] = "source"
    producer.reconcile(_snapshot(first))
    first_id = first["technical_document_id"]

    (tmp_path / "Copy.pdf").write_bytes(b"%PDF-identical")
    original = _card(status="SOURCE_ONLY")
    original["document_id"] = None
    original["hindsight_eligible"] = True
    original["hindsight_representation_candidate"] = "source"
    copy = _card("Copy.pdf", status="SOURCE_ONLY")
    copy["document_id"] = None
    copy["hindsight_eligible"] = True
    copy["hindsight_representation_candidate"] = "source"
    snapshot = {
        "workspaces": [
            {"name": "Affaires", "available": True, "cards": [original, copy], "errors": []}
        ]
    }
    producer.reconcile(snapshot)

    assert original["technical_document_id"] == first_id
    assert copy["technical_document_id"] != first_id
    assert copy["technical_document_id"].startswith("doc_auto_")



def test_project_scope_tokens_disambiguate_lossy_slug_collisions() -> None:
    module = _module()
    assert module._tag_value("Projet A") == module._tag_value("Projet-A")
    assert module._project_scope_token("Projet A") != module._project_scope_token("Projet-A")


def test_replacement_quality_is_not_checked_against_previous_fingerprint(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-old")
    db = tmp_path / "state.sqlite3"

    class ReplacementClient(FakeClient):
        def __init__(self) -> None:
            super().__init__(["completed", "completed"])
            self.document_reads = 0

        def get_document(self, document_id: str):
            self.document_reads += 1
            return {"id": document_id, "original_text": "Texte extrait."}

    client = ReplacementClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
    )

    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    assert client.document_reads == 1

    source.write_bytes(b"%PDF-new")
    producer.reconcile(_snapshot(_card()))
    assert client.document_reads == 1
    assert len(client.retains) == 2

    producer.reconcile(_snapshot(_card()))
    assert client.document_reads == 2
