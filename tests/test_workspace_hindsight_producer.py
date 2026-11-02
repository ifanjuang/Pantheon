from __future__ import annotations

from concurrent.futures import Future
import importlib.util
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pytest
import sqlite3
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "implementation" / "workspace_cockpit" / "hindsight_producer.py"


_created_producers = []


@pytest.fixture(autouse=True)
def _close_test_workers():
    yield
    while _created_producers:
        _created_producers.pop().close()


def _module():
    sys.path.insert(0, str(PRODUCER.parent))
    spec = importlib.util.spec_from_file_location("workspace_hindsight_producer", PRODUCER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    base_producer = module.HindsightProducer

    class ManagedProducer(base_producer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _created_producers.append(self)

    module.HindsightProducer = ManagedProducer
    return module


def _snapshot(card: dict | None, workspace: str = "Affaires") -> dict:
    return {
        "workspaces": [
            {
                "name": workspace,
                "available": True,
                "complete": True,
                "cards": [] if card is None else [card],
                "errors": [],
            }
        ]
    }


def _card(path: str = "Notice.pdf", *, status: str = "COMPLETE", representation: str = "source", workspace: str = "Affaires", document_id: str = "doc-notice") -> dict:
    return {
        "workspace": workspace,
        "kind": "document",
        "path": path,
        "name": Path(path).name,
        "status": status,
        "document_id": document_id,
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
        self.operations: list[dict] = []
        self.project_pages: dict[str, dict] = {}
        self.project_observations_ready = False
        self.created_project_pages: list[dict] = []

    def retain_file(self, source: Path, **kwargs):
        self.retains.append({"source": source, **kwargs})
        operation_id = f"op-{len(self.retains)}"
        self.operations.append({
            "id": operation_id,
            "operation_type": "file_convert_retain",
            "document_id": kwargs["document_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return operation_id

    def list_file_retain_operations(self, *, limit: int = 100):
        return list(reversed(self.operations[-limit:]))

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

    def knowledge_base_tree(self, scope_tag: str):
        page = self.project_pages.get(scope_tag)
        return [page] if page else []

    def has_project_observations(self, scope_tag: str):
        return self.project_observations_ready

    def create_knowledge_page(self, *, name: str, source_query: str, scope_tag: str, max_tokens: int = 1400):
        result = {"page_id": f"kp-{len(self.created_project_pages) + 1}", "operation_id": "op-page"}
        self.created_project_pages.append({
            "name": name, "source_query": source_query, "scope_tag": scope_tag,
            "max_tokens": max_tokens, **result,
        })
        self.project_pages[scope_tag] = {
            "kind": "page", "id": result["page_id"], "name": name, "tags": [scope_tag]
        }
        return result

    def update_knowledge_page_prompt(self, page_id: str, source_query: str):
        return {"operation_id": "op-page-refresh"}


def _wait_preflight(producer, document_ids, timeout=5):
    """Wait for the real worker's terminal result without advancing Hindsight."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rows = producer.processing_queue.list_items(include_memorized=True)["items"]
        selected = [row for row in rows if row["document_id"] in document_ids]
        if len(selected) == len(document_ids) and all(
            row["preflight_status"] == "ANALYZED" for row in selected
        ):
            return
        assert not any(row["preflight_status"] == "FAILED" for row in selected), selected
        time.sleep(0.01)
    raise AssertionError(f"preflight did not finish: {selected}")


def _first_queued_reconcile(producer, snapshot):
    """Observe, let the independent preflight finish, then dispatch once."""
    first = producer.reconcile(snapshot)
    if first["submitted"]:
        return first
    document_ids = {
        card["document_id"]
        for workspace in snapshot["workspaces"] for card in workspace["cards"]
    }
    _wait_preflight(producer, document_ids)
    return producer.reconcile(snapshot)


def _row(db: Path) -> dict:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM hindsight_sync").fetchone()
        assert row is not None
        return dict(row)
    finally:
        con.close()


def _row_for(db: Path, document_id: str) -> dict | None:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT * FROM hindsight_sync WHERE document_id=?", (document_id,)
        ).fetchone()
        return dict(row) if row is not None else None
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


def test_project_overview_waits_for_consolidated_observations_and_uses_project_prompt(tmp_path: Path) -> None:
    module = _module()
    project_root = tmp_path / "VERGER"
    project_root.mkdir()
    source = project_root / "Notice.pdf"
    source.write_bytes(b"%PDF-source-v1")
    db = tmp_path / "state" / "index.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=db,
        client=client,
        max_submits_per_reconcile=1,
        project_overview_prompts={
            "Affaires": "Aperçu « {project} » : faits établis, incertitudes et pièces sources.",
        },
    )
    card = _card("VERGER/Notice.pdf")
    producer.reconcile(_snapshot(card))
    client.project_observations_ready = False
    producer.reconcile(_snapshot(card))

    connection = sqlite3.connect(db)
    try:
        state = connection.execute(
            "SELECT status, scope_tag, source_query FROM hindsight_project_overview"
        ).fetchone()
    finally:
        connection.close()
    assert state == (
        "WAITING_OBSERVATIONS",
        f"scope:project:{module._project_scope_token('VERGER')}",
        "Aperçu « VERGER » : faits établis, incertitudes et pièces sources.",
    )
    assert client.created_project_pages == []

    client.project_observations_ready = True
    producer.reconcile(_snapshot(card))
    assert len(client.created_project_pages) == 1
    assert client.created_project_pages[0]["scope_tag"] == state[1]
    assert client.created_project_pages[0]["source_query"] == state[2]
    assert client.created_project_pages[0]["max_tokens"] == 1400
    producer.reconcile(_snapshot(card))
    assert len(client.created_project_pages) == 1


def test_connection_refusal_is_retryable_without_manual_queue_retry(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-definite-submission-error")
    db = tmp_path / "state.sqlite3"
    queue_db = tmp_path / "queue.sqlite3"

    class InitiallyUnavailableClient(FakeClient):
        unavailable = True

        def retain_file(self, source: Path, **kwargs):
            if self.unavailable:
                raise RuntimeError("Hindsight unavailable: connection refused")
            return super().retain_file(source, **kwargs)

    client = InitiallyUnavailableClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)

    _first_queued_reconcile(producer, _snapshot(_card()))
    item = queue.list_items(include_memorized=True)["items"][0]
    assert _row(db)["status"] == "UNAVAILABLE"
    assert item["hindsight_status"] == "UNAVAILABLE"
    assert "connection refused" in item["error"]

    producer.reconcile(_snapshot(_card()))
    assert len(client.retains) == 0
    assert _row(db)["status"] == "UNAVAILABLE"

    client.unavailable = False
    _first_queued_reconcile(producer, _snapshot(_card()))
    assert len(client.retains) == 1
    producer.reconcile(_snapshot(_card()))
    assert _row(db)["status"] == "COMPLETED"
    assert client.tag_updates[-1]["document_id"] == "doc-notice:source"
    assert "ocr:raw" in client.tag_updates[-1]["tags"]


def test_connection_refusal_holds_submission_lane_on_failed_document(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "First.pdf").write_bytes(b"%PDF-first")
    (tmp_path / "Second.pdf").write_bytes(b"%PDF-second")
    db = tmp_path / "state.sqlite3"

    class InitiallyUnavailableClient(FakeClient):
        unavailable = True

        def retain_file(self, source: Path, **kwargs):
            if self.unavailable:
                raise RuntimeError("Hindsight unavailable: connection refused")
            return super().retain_file(source, **kwargs)

    client = InitiallyUnavailableClient(["completed", "completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client
    )
    snapshot = _snapshot(_card(path="First.pdf", document_id="doc-first"))
    snapshot["workspaces"][0]["cards"].append(
        _card(path="Second.pdf", document_id="doc-second")
    )

    producer.reconcile(snapshot)
    assert _row_for(db, "doc-first")["status"] == "UNAVAILABLE"
    assert _row_for(db, "doc-second") is None

    producer.reconcile(snapshot)
    assert _row_for(db, "doc-second") is None
    client.unavailable = False
    producer.reconcile(snapshot)
    assert len(client.retains) == 1
    assert client.retains[0]["document_id"] == "doc-first:source"


def test_restart_recovers_accepted_upload_operation_without_resubmitting(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-crash-after-remote-accept")
    db = tmp_path / "state.sqlite3"

    class CrashAfterAcceptClient(FakeClient):
        def retain_file(self, source: Path, **kwargs):
            super().retain_file(source, **kwargs)
            raise SystemExit("simulated process stop after remote acceptance")

    client = CrashAfterAcceptClient()
    producer = module.HindsightProducer(roots=[("Affaires", tmp_path)], state_db=db, client=client)
    try:
        producer.reconcile(_snapshot(_card()))
    except SystemExit as exc:
        assert "simulated process stop" in str(exc)
    else:
        raise AssertionError("the simulated process stop should interrupt reconciliation")

    assert _row(db)["status"] == "SUBMITTING"
    recovered = producer.reconcile(_snapshot(_card()))

    assert recovered["completed"] == 1
    assert len(client.retains) == 1
    assert client.polls == ["op-1"]
    assert _row(db)["status"] == "COMPLETED"


def test_stale_unmatched_submission_is_held_for_verification_even_if_source_changes(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-original")
    db = tmp_path / "state.sqlite3"

    class CrashBeforeResponseClient(FakeClient):
        def retain_file(self, source: Path, **kwargs):
            self.retains.append({"source": source, **kwargs})
            raise SystemExit("simulated interrupted submission")

    client = CrashBeforeResponseClient()
    queue_db = tmp_path / "queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client,
        processing_queue_db=queue_db,
    )
    try:
        _first_queued_reconcile(producer, _snapshot(_card()))
    except SystemExit:
        pass
    else:
        raise AssertionError("the simulated interruption should occur")

    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "UPDATE hindsight_sync SET updated_at='2020-01-01T00:00:00Z'"
        )
        connection.commit()
    finally:
        connection.close()

    source.write_bytes(b"%PDF-replaced-while-outcome-unknown")
    producer.reconcile(_snapshot(_card()))

    assert _row(db)["status"] == "SUBMITTING"
    assert len(client.retains) == 1
    queue = module.ProcessingQueue(queue_db).list_items(include_memorized=True)
    assert queue["items"][0]["hindsight_status"] == "VERIFY"


def test_late_visible_operation_is_recovered_after_verification_warning(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-late-visible-operation")
    db = tmp_path / "state.sqlite3"

    class CrashBeforeResponseClient(FakeClient):
        def retain_file(self, source: Path, **kwargs):
            self.retains.append({"source": source, **kwargs})
            raise SystemExit("simulated interrupted submission")

    client = CrashBeforeResponseClient(["completed"])
    producer = module.HindsightProducer(roots=[("Affaires", tmp_path)], state_db=db, client=client)
    try:
        producer.reconcile(_snapshot(_card()))
    except SystemExit:
        pass
    else:
        raise AssertionError("the simulated interruption should occur")

    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "UPDATE hindsight_sync SET updated_at='2020-01-01T00:00:00Z'"
        )
        connection.commit()
    finally:
        connection.close()

    producer.reconcile(_snapshot(_card()))
    assert _row(db)["status"] == "SUBMITTING"

    client.operations.append({
        "id": "op-late",
        "operation_type": "file_convert_retain",
        "document_id": "doc-notice:source",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    recovered = producer.reconcile(_snapshot(_card()))

    assert recovered["completed"] == 1
    assert client.polls == ["op-late"]
    assert len(client.retains) == 1
    assert _row(db)["status"] == "COMPLETED"


def test_submission_error_classification_is_conservative_for_ambiguous_responses() -> None:
    module = _module()

    assert not module._submission_outcome_uncertain("Hindsight HTTP 400: invalid parser")
    assert not module._submission_outcome_uncertain("Hindsight unavailable: [Errno 111] Connection refused")
    assert module._submission_outcome_uncertain("Hindsight HTTP 408: request timeout")
    assert module._submission_outcome_uncertain("Hindsight HTTP 429: rate limited")
    assert module._submission_outcome_uncertain("Hindsight HTTP 503: service unavailable")
    assert module._submission_outcome_uncertain("Hindsight unavailable: socket read timed out")


def test_ambiguous_upload_keeps_intent_and_stops_the_submission_lane(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "A.pdf").write_bytes(b"%PDF-a")
    (tmp_path / "B.pdf").write_bytes(b"%PDF-b")
    db = tmp_path / "state.sqlite3"

    class AmbiguousClient(FakeClient):
        def retain_file(self, source: Path, **kwargs):
            self.retains.append({"source": source, **kwargs})
            raise RuntimeError("Hindsight unavailable: socket read timed out")

    client = AmbiguousClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client
    )
    snapshot = _snapshot(_card("A.pdf", document_id="doc-a"))
    snapshot["workspaces"][0]["cards"].append(_card("B.pdf", document_id="doc-b"))

    producer.reconcile(snapshot)
    producer.reconcile(snapshot)
    rows = producer._states()

    assert len(client.retains) == 1
    assert rows["doc-a:source"]["status"] == "SUBMITTING"
    assert "doc-b:source" not in rows


def test_processing_queue_tracks_hindsight_lifecycle_and_removes_memorized_row(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-queue")
    queue_db = tmp_path / "shared-queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=FakeClient(["completed"]),
        processing_queue_db=queue_db,
    )
    _first_queued_reconcile(producer, _snapshot(_card()))
    queue = module.ProcessingQueue(queue_db)
    active = queue.list_items()
    assert len(active["items"]) == 1
    assert active["items"][0]["preflight_status"] == "ANALYZED"
    assert active["items"][0]["hindsight_status"] == "MEMORIZING"
    assert active["items"][0]["operation_id"] == "op-1"

    producer.reconcile(_snapshot(_card()))
    assert queue.list_items()["items"] == []
    assert queue.list_items(include_memorized=True)["items"][0]["hindsight_status"] == "MEMORIZED"


def test_completed_operation_without_exact_document_readback_stays_verifying_without_resubmit(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-readback-missing")
    queue_db = tmp_path / "shared-queue.sqlite3"

    class MissingReadbackClient(FakeClient):
        def get_document(self, document_id: str):
            raise RuntimeError("Hindsight HTTP 404: Document not found")

    client = MissingReadbackClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)

    _first_queued_reconcile(producer, _snapshot(_card()))
    producer.reconcile(_snapshot(_card()))

    item = queue.list_items()["items"][0]
    assert item["hindsight_status"] == "VERIFYING"
    assert "read-back failed" in item["error"]
    assert _row(tmp_path / "affaires.sqlite3")["status"] == "VERIFYING"

    # A completed conversion with a missing document stays attached to the
    # same operation and is checked again; it is never retained twice.
    producer.reconcile(_snapshot(_card()))
    assert len(client.retains) == 1
    assert queue.list_items()["items"][0]["hindsight_status"] == "VERIFYING"


def test_completed_operation_with_wrong_document_identity_requires_verification(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-wrong-readback-id")
    queue_db = tmp_path / "shared-queue.sqlite3"

    class WrongReadbackClient(FakeClient):
        def get_document(self, document_id: str):
            return {"id": "a-different-document", "original_text": "Texte"}

    client = WrongReadbackClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)

    _first_queued_reconcile(producer, _snapshot(_card()))
    producer.reconcile(_snapshot(_card()))

    item = queue.list_items()["items"][0]
    assert item["hindsight_status"] == "VERIFY"
    assert "exact document was not confirmed" in item["error"]
    assert _row(tmp_path / "affaires.sqlite3")["status"] == "VERIFY"

    producer.reconcile(_snapshot(_card()))
    assert len(client.retains) == 1


def test_cockpit_verification_request_rechecks_exact_document_without_resubmitting(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-operator-verification")
    queue_db = tmp_path / "shared-queue.sqlite3"

    class CorrectedReadbackClient(FakeClient):
        return_correct_document = False

        def get_document(self, document_id: str):
            if self.return_correct_document:
                return {"id": document_id, "original_text": "Contenu retrouvé."}
            return {"id": "unexpected-document", "original_text": "Texte"}

    client = CorrectedReadbackClient(["completed", "completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)

    _first_queued_reconcile(producer, _snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    item = queue.list_items(include_memorized=True)["items"][0]
    assert item["hindsight_status"] == "VERIFY"

    queue.request_verification("Affaires", "doc-notice")
    client.return_correct_document = True
    producer.reconcile(_snapshot(_card()))

    assert _row(tmp_path / "affaires.sqlite3")["status"] == "COMPLETED"
    assert len(client.retains) == 1
    assert client.polls == ["op-1", "op-1"]
    assert queue.list_items(include_memorized=True)["items"][0]["hindsight_status"] == "MEMORIZED"
    assert queue.verification_requests() == []


def test_cockpit_verification_recovers_late_operation_without_known_operation_id(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-late-operation-manual-check")
    queue_db = tmp_path / "shared-queue.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)

    _first_queued_reconcile(producer, _snapshot(_card()))
    connection = sqlite3.connect(tmp_path / "affaires.sqlite3")
    try:
        connection.execute("UPDATE hindsight_sync SET status='VERIFY', operation_id=NULL")
        connection.commit()
    finally:
        connection.close()
    queue.set_status("Affaires", "doc-notice", hindsight_status="VERIFY", error="operation ID missing")
    queue.request_verification("Affaires", "doc-notice")

    result = producer.reconcile(_snapshot(_card()))

    assert result["completed"] == 1
    assert _row(tmp_path / "affaires.sqlite3")["status"] == "COMPLETED"
    assert client.polls == ["op-1"]
    assert len(client.retains) == 1
    assert queue.list_items(include_memorized=True)["items"][0]["hindsight_status"] == "MEMORIZED"
    assert queue.verification_requests() == []


def test_approved_ocr_recovery_confirms_exact_existing_artifact_without_retain(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-existing-ocr-recovery")
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    artifact_name = "ocr-exact-artifact.md"
    cache_dir = tmp_path / "ocr-cache"
    cache_dir.mkdir()
    artifact = cache_dir / artifact_name
    artifact.write_text("Texte OCR déjà mémorisé.\n", encoding="utf-8")
    artifact_sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()

    class ExactOcrDocumentClient(FakeClient):
        def get_document(self, document_id: str):
            return {
                "id": document_id,
                "content_hash": artifact_sha256,
                "tags": ["ocr:complete"],
                "document_metadata": {
                    "source_sha256": source_sha256,
                    "ocr_source_sha256": source_sha256,
                    "ocr_artifact_name": artifact_name,
                    "ocr_derived_from": "Notice.pdf",
                },
            }

    client = ExactOcrDocumentClient(["completed"])
    queue_db = tmp_path / "queue.sqlite3"
    state_db = tmp_path / "state.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=state_db,
        processing_queue_db=queue_db,
        client=client,
        ocr_processor=SimpleNamespace(cache_dir=cache_dir),
    )
    queue = module.ProcessingQueue(queue_db)
    snapshot = _snapshot(_card())
    _first_queued_reconcile(producer, snapshot)
    assert len(client.retains) == 1

    queue.set_status(
        "Affaires", "doc-notice", hindsight_status="VERIFY",
        error="Hindsight document already exists; OCR replacement requires operator review",
        clear_operation_id=True,
    )
    queue.set_ocr_status(
        "Affaires", "doc-notice", status="READY",
        output_filename=artifact_name, engine="vision:test", queue_status="OCR_READY",
    )
    with sqlite3.connect(queue_db) as connection:
        connection.execute(
            """UPDATE processing_queue SET ocr_preflight_source_sha256=?,
                ocr_replace_approved=1, request_action='replace_ocr',
                hindsight_status='VERIFY',
                error='Hindsight document already exists; OCR replacement requires operator review'
               WHERE workspace='Affaires' AND document_id='doc-notice'""",
            (source_sha256,),
        )
    with sqlite3.connect(state_db) as connection:
        connection.execute(
            """UPDATE hindsight_sync SET status='SUBMITTING', operation_id=NULL,
                last_error='Hindsight document already exists; OCR replacement requires operator review'
               WHERE document_id='doc-notice'"""
        )
    client.operations.clear()

    pending = queue.get_item("Affaires", "doc-notice")
    assert pending["ocr_status"] == "READY"
    assert pending["ocr_replace_approved"] == 1
    assert pending["request_action"] == "replace_ocr"
    assert pending["ocr_preflight_source_sha256"] == source_sha256
    recovered = producer._recover_submission(producer._states()["doc-notice:source"])
    assert recovered["status"] == "COMPLETED"

    queue_item = queue.get_item("Affaires", "doc-notice")
    assert _row_for(state_db, "doc-notice")["status"] == "COMPLETED"
    assert queue_item["hindsight_status"] == "MEMORIZED"
    assert queue_item["ocr_status"] == "DONE"
    assert queue_item["ocr_replace_approved"] == 0
    assert len(client.retains) == 1


def test_verification_request_survives_hindsight_outage_until_a_check_succeeds(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-operator-verification-outage")
    queue_db = tmp_path / "shared-queue.sqlite3"

    class IntermittentClient(FakeClient):
        fail_status = False

        def operation_status(self, operation_id: str):
            if self.fail_status:
                raise RuntimeError("Hindsight unavailable: connection refused")
            return super().operation_status(operation_id)

        def get_document(self, document_id: str):
            return {"id": document_id, "original_text": "Contenu retrouvé."}

    client = IntermittentClient(["completed", "completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)

    _first_queued_reconcile(producer, _snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    connection = sqlite3.connect(tmp_path / "affaires.sqlite3")
    try:
        connection.execute("UPDATE hindsight_sync SET status='VERIFY', last_error='manual review'")
        connection.commit()
    finally:
        connection.close()
    queue.set_status("Affaires", "doc-notice", hindsight_status="VERIFY", error="manual review")
    queue.request_verification("Affaires", "doc-notice")
    client.fail_status = True

    producer.reconcile(_snapshot(_card()))
    request = queue.verification_requests()
    assert len(request) == 1
    assert "connection refused" in queue.list_items(include_memorized=True)["items"][0]["error"]
    assert len(client.retains) == 1

    client.fail_status = False
    producer.reconcile(_snapshot(_card()))
    assert queue.verification_requests() == []
    assert queue.list_items(include_memorized=True)["items"][0]["hindsight_status"] == "MEMORIZED"
    assert len(client.retains) == 1


def test_processing_queue_pause_prevents_new_hindsight_submission(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-queue-paused")
    queue_db = tmp_path / "shared-queue.sqlite3"
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "affaires.sqlite3",
        client=client,
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)
    queue.set_paused("vault:Affaires", True)

    producer.reconcile(_snapshot(_card()))

    assert client.retains == []
    item = queue.list_items()["items"][0]
    assert item["preflight_status"] == "TO_PROCESS"
    assert item["hindsight_status"] == "NOT_SENT"


def test_preflight_keeps_priority_and_advances_while_hindsight_is_busy(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    for name in ("first.pdf", "second.pdf", "third.pdf", "fourth.pdf"):
        (tmp_path / name).write_bytes(b"%PDF-" + name.encode())
    queue_db = tmp_path / "shared-queue.sqlite3"
    queue = module.ProcessingQueue(queue_db)
    queue.set_paused("global", True)
    for name, document_id in ((name + ".pdf", "doc-" + name) for name in ("first", "second", "third", "fourth")):
        queue.upsert_candidate(
            workspace="Affaires", document_id=document_id, source_path=name,
            source_sha256=hashlib.sha256((tmp_path / name).read_bytes()).hexdigest(),
            preflight_status="TO_PROCESS",
        )
    queue.reorder([("Affaires", "doc-" + name) for name in ("second", "first", "third", "fourth")])
    preflight_paths = []
    first_started, release_first = threading.Event(), threading.Event()

    def fake_preflight(source, **kwargs):
        preflight_paths.append(source.name)
        if source.name == "first.pdf":
            first_started.set()
            assert release_first.wait(5), "test did not release preflight"
        return module.PreflightResult(profile="affaires", status="no_explicit_fields", fields={})

    monkeypatch.setattr(module, "preflight_pdf_metadata", fake_preflight)
    client = FakeClient(["processing"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=tmp_path / "state.sqlite3",
        client=client, processing_queue_db=queue_db,
    )
    cards = [_card(name + ".pdf", document_id="doc-" + name) for name in ("first", "second", "third", "fourth")]
    snapshot = {"workspaces": [{"name": "Affaires", "available": True, "cards": cards, "errors": []}]}
    try:
        producer.reconcile(snapshot)
        assert preflight_paths == []
        queue.set_paused("global", False)
        assert first_started.wait(5), (preflight_paths, queue.list_items(include_memorized=True))
        assert preflight_paths == ["second.pdf", "first.pdf"]
        producer.reconcile(snapshot)
        assert [item["source"].name for item in client.retains] == ["second.pdf"]
        assert queue.get_item("Affaires", "doc-first")["preflight_status"] == "ANALYZING"
        queue.reorder([("Affaires", "doc-" + name) for name in ("fourth", "third", "first", "second")])
        release_first.set()
        _wait_preflight(producer, {"doc-first", "doc-third", "doc-fourth"})
        assert preflight_paths == ["second.pdf", "first.pdf", "fourth.pdf", "third.pdf"]
        assert queue.get_item("Affaires", "doc-second")["hindsight_status"] == "MEMORIZING"
        producer.reconcile(snapshot)
        assert len(client.retains) == 1
        assert queue.get_item("Affaires", "doc-first")["preflight_status"] == "ANALYZED"
    finally:
        release_first.set()


def test_one_producer_routes_each_vault_to_its_own_hindsight_bank(tmp_path: Path) -> None:
    module = _module()
    affaires_root = tmp_path / "affaires"
    library_root = tmp_path / "library"
    affaires_root.mkdir()
    library_root.mkdir()
    (affaires_root / "Notice.pdf").write_bytes(b"%PDF-affaires")
    (library_root / "Guide.pdf").write_bytes(b"%PDF-library")
    affaires_client = FakeClient()
    library_client = FakeClient()
    affaires_client.bank_id = "PROJECTS"
    library_client.bank_id = "KNOWLEDGE"
    producer = module.HindsightProducer(
        roots=[("Affaires", affaires_root), ("Bibliothèque", library_root)],
        state_db=tmp_path / "shared.sqlite3",
        clients={"Affaires": affaires_client, "Bibliothèque": library_client},
        source_kinds={"Affaires": "kroqui-sync", "Bibliothèque": "library-sync"},
        metadata_profiles={"Affaires": "affaires", "Bibliothèque": "bibliotheque"},
        settle_observations=1,
        processing_queue_db=tmp_path / "shared.sqlite3",
    )
    cards = [
        _card(),
        _card("Guide.pdf", workspace="Bibliothèque", document_id="doc-guide"),
    ]
    snapshot = {"workspaces": [
        {"name": "Affaires", "available": True, "cards": [cards[0]], "errors": []},
        {"name": "Bibliothèque", "available": True, "cards": [cards[1]], "errors": []},
    ]}

    _first_queued_reconcile(producer, snapshot)
    assert len(affaires_client.retains) == 1
    assert library_client.retains == []
    assert affaires_client.retains[0]["metadata"]["source_kind"] == "kroqui-sync"

    producer.reconcile(snapshot)
    assert len(library_client.retains) == 1
    assert library_client.retains[0]["metadata"]["source_kind"] == "library-sync"
    assert library_client.retains[0]["metadata"]["metadata_preflight_profile"] == "bibliotheque"


def test_missing_pdftotext_still_retains_the_pdf_without_preflight_metadata(tmp_path: Path) -> None:
    """A missing Poppler utility leaves the normal source-retain path untouched."""
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-no-poppler")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=client,
        processing_queue_db=tmp_path / "queue.sqlite3",
    )
    with patch("shutil.which", return_value=None):
        _first_queued_reconcile(producer, _snapshot(_card()))
    assert len(client.retains) == 1
    assert client.retains[0]["metadata"]["metadata_preflight_status"] == "extractor_unavailable"


def test_raw_status_preserves_existing_derived_ocr_state() -> None:
    module = _module()
    assert module._with_raw_ocr_status(["project:alpha", "ocr:partial"]) == [
        "ocr:partial",
        "project:alpha",
    ]
    assert module._with_raw_ocr_status(["ocr:complete"]) == ["ocr:complete"]


def test_ocr_source_missing_from_scan_stays_queued_for_reappearance(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-ocr-wait")
    queue_db = tmp_path / "queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        processing_queue_db=queue_db,
        ocr_processor=SimpleNamespace(cache_dir=tmp_path / "ocr-cache"),
    )
    queue = module.ProcessingQueue(queue_db)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    queue.upsert_candidate(
        workspace="Affaires", document_id="doc-notice", source_path="Notice.pdf",
        source_sha256=source_sha256, preflight_status="ANALYZED", hindsight_status="OCR_QUEUED",
    )
    queue.set_ocr_status("Affaires", "doc-notice", status="QUEUED", queue_status="OCR_QUEUED")

    producer._advance_ocr({})

    item = queue.list_items(include_memorized=True)["items"][0]
    assert item["ocr_status"] == "QUEUED"
    assert item["hindsight_status"] == "OCR_QUEUED"


def test_completed_ocr_for_absent_source_is_archived_after_complete_scan(tmp_path: Path) -> None:
    module = _module()
    queue_db = tmp_path / "queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        processing_queue_db=queue_db,
    )
    # This test exercises one request directly; stop the asynchronous worker so
    # it cannot claim that same request between insertion and inspection.
    producer._preflight_stop.set()
    producer._preflight_thread.join(timeout=2)
    queue = module.ProcessingQueue(queue_db)
    queue.upsert_candidate(
        workspace="Affaires", document_id="doc-notice", source_path="Notice.pdf",
        source_sha256="a" * 64, preflight_status="ANALYZED", hindsight_status="OCR_READY",
    )
    queue.set_ocr_status(
        "Affaires", "doc-notice", status="READY", output_filename="ocr-result.md",
        engine="docling", queue_status="OCR_READY",
    )

    producer.reconcile(_snapshot(None))

    item = queue.get_item("Affaires", "doc-notice")
    assert item is not None
    assert item["hindsight_status"] == "ARCHIVED"
    assert item["ocr_status"] == "NONE"
    assert item["ocr_filename"] is None


def test_ocr_filesystem_error_is_requeued_with_backoff(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-ocr-transient-error")
    queue_db = tmp_path / "queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        processing_queue_db=queue_db,
        ocr_processor=SimpleNamespace(cache_dir=tmp_path / "ocr-cache"),
    )
    queue = module.ProcessingQueue(queue_db)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    queue.upsert_candidate(
        workspace="Affaires", document_id="doc-notice", source_path="Notice.pdf",
        source_sha256=source_sha256, preflight_status="ANALYZED", hindsight_status="OCR_PROCESSING",
    )
    queue.set_ocr_status("Affaires", "doc-notice", status="PROCESSING", queue_status="OCR_PROCESSING")
    future = Future()
    future.set_exception(FileNotFoundError("temporary NAS read failure"))
    producer._ocr_futures[("Affaires", "doc-notice")] = future

    producer._advance_ocr({})

    item = queue.list_items(include_memorized=True)["items"][0]
    assert item["ocr_status"] == "QUEUED"
    assert item["hindsight_status"] == "OCR_QUEUED"
    assert ("Affaires", "doc-notice") in producer._ocr_waiting_source


def test_metadata_preflight_accepts_only_unique_explicit_labels(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "piece.pdf"
    source.write_bytes(b"%PDF-test")
    with patch.object(
        preflight.shutil,
        "which",
        return_value="/usr/bin/pdftotext",
    ), patch.object(
        preflight.subprocess,
        "run",
        return_value=type(
            "Completed", (), {"returncode": 0, "stdout": "Date du document : 12/09/2026\nIndice : B\nÉmetteur : Atelier Exemple\nDestinataire : Maître d'ouvrage\n\f"}
        )(),
    ):
        result = preflight.preflight_pdf_metadata(
            source,
            source_kind="project-sync",
            workspace="Affaires",
        )

    assert result.profile == "affaires"
    assert result.fields["document_date"].value == "12/09/2026"
    assert result.fields["index"].value == "B"
    assert result.fields["issuer"].value == "Atelier Exemple"
    assert result.fields["recipient"].value == "Maître d'ouvrage"
    assert result.fields["recipient"].page == 1
    assert result.fields["document_date"].source == "document_text"


def test_metadata_preflight_samples_final_page_for_missing_date_and_issuer(tmp_path: Path) -> None:
    _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "piece.pdf"
    source.write_bytes(b"%PDF-test")

    def which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in {"pdftotext", "pdfinfo"} else None

    def run(args: list[str], **_kwargs):
        if args[0].endswith("pdfinfo"):
            stdout = "Pages: 77\nCreationDate: 2024-10-11T06:40:13Z\n"
        elif args[args.index("-f") + 1] == "1":
            stdout = "DEVIS D-240446\nTravaux de rénovation\n\fPage 2\n\f"
        else:
            stdout = "Devis n° D-240446 du 18/09/2024\nÉmetteur : LEBLIC Rénovation\n"
        return type("Completed", (), {"returncode": 0, "stdout": stdout})()

    with patch.object(preflight.shutil, "which", side_effect=which), patch.object(
        preflight.subprocess, "run", side_effect=run
    ):
        result = preflight.preflight_pdf_metadata(source, workspace="Affaires")

    assert result.fields["document_date"].value == "18/09/2024"
    assert result.fields["document_date"].page == 77
    assert result.fields["issuer"].value == "LEBLIC Rénovation"
    assert result.fields["issuer"].page == 77
    assert "pdf_creation_date" not in result.fields


def test_metadata_preflight_skips_final_page_when_opening_page_is_sufficient(tmp_path: Path) -> None:
    _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "devis.pdf"
    source.write_bytes(b"%PDF-test")
    raw = (
        '<html xmlns="http://www.w3.org/1999/xhtml"><body><page width="600" height="1000">'
        '<line xMin="20" yMin="20" xMax="500" yMax="40"><word xMin="20" yMin="20" '
        'xMax="500" yMax="40">Devis n° D-240446 du 18/09/2024</word></line>'
        '<line xMin="20" yMin="60" xMax="500" yMax="80"><word xMin="20" yMin="60" '
        'xMax="500" yMax="80">LEBLIC Rénovation au capital de 10000 €</word></line>'
        '</page></body></html>'
    )
    with patch.object(preflight.shutil, "which", return_value="/usr/bin/pdftotext"), patch.object(
        preflight.subprocess,
        "run",
        return_value=type("Completed", (), {"returncode": 0, "stdout": raw})(),
    ) as run:
        result = preflight.preflight_pdf_metadata(source, workspace="Affaires")

    assert result.fields["document_date"].value == "18/09/2024"
    assert any(candidate.value == "LEBLIC Rénovation" for candidate in result.issuer_candidates)
    assert run.call_count == 1


def test_metadata_preflight_uses_pdf_creation_date_only_as_fallback(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "piece.pdf"
    source.write_bytes(b"%PDF-test")

    def which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in {"pdftotext", "pdfinfo"} else None

    def run(args: list[str], **_kwargs):
        if args[0].endswith("pdfinfo"):
            return type(
                "Completed",
                (),
                {"returncode": 0, "stdout": "CreationDate: 2026-09-17T12:30:00+02:00\n"},
            )()
        return type(
            "Completed",
            (),
            {"returncode": 0, "stdout": "Notice technique\n\f"},
        )()

    with patch.object(preflight.shutil, "which", side_effect=which), patch.object(
        preflight.subprocess, "run", side_effect=run
    ):
        result = preflight.preflight_pdf_metadata(
            source,
            source_kind="project-sync",
            workspace="Affaires",
        )

    candidate = result.fields["pdf_creation_date"]
    assert candidate.value == "17/09/2026"
    assert candidate.page == 0
    assert candidate.source == "pdf_creation_metadata"
    assert "CreationDate" in candidate.evidence
    assert "document_date" not in result.fields


def test_pdf_creation_date_is_available_without_native_text(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-test")

    def which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in {"pdftotext", "pdfinfo"} else None

    def run(args: list[str], **_kwargs):
        if args[0].endswith("pdfinfo"):
            return type(
                "Completed",
                (),
                {"returncode": 0, "stdout": "CreationDate: 2026-09-17T12:30:00+02:00\n"},
            )()
        return type("Completed", (), {"returncode": 0, "stdout": ""})()

    with patch.object(preflight.shutil, "which", side_effect=which), patch.object(
        preflight.subprocess, "run", side_effect=run
    ):
        result = preflight.preflight_pdf_metadata(source)

    assert result.status == "partial"
    assert result.fields["pdf_creation_date"].value == "17/09/2026"
    assert "document_date" not in result.fields


def test_pdf_creation_date_candidate_rejects_partial_and_invalid_dates() -> None:
    preflight = sys.modules["document_metadata_preflight"]
    assert preflight._pdf_creation_date_candidate("CreationDate: 2026-09-17T12:30:00Z") is not None
    assert preflight._pdf_creation_date_candidate("CreationDate: D:20260917123000+02'00'") is not None
    assert preflight._pdf_creation_date_candidate("CreationDate: 2026-02-31T12:30:00Z") is None
    assert preflight._pdf_creation_date_candidate("CreationDate: unknown") is None


def test_library_preflight_omits_recipient_and_flags_conflicting_values(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "piece.pdf"
    source.write_bytes(b"%PDF-test")
    with patch.object(preflight.shutil, "which", return_value="/usr/bin/pdftotext"), patch.object(
        preflight.subprocess,
        "run",
        return_value=type(
            "Completed", (), {"returncode": 0, "stdout": "Indice : A\nIndice : B\nDestinataire : AGENCE\n\f"}
        )(),
    ):
        result = preflight.preflight_pdf_metadata(
            source,
            source_kind="bibliotheque",
            workspace="Bibliothèque",
        )

    assert result.profile == "bibliotheque"
    assert "recipient" not in result.fields
    assert result.unresolved == ("index",)
    assert result.status == "partial"


def test_metadata_preflight_reads_simple_revision_table_on_cover(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "study.pdf"
    source.write_bytes(b"%PDF-test")
    output = (
        "Indice           Date                           Modification\n"
        "   A        07/11/2025                         1ère diffusion\f"
    )
    with patch.object(preflight.shutil, "which", return_value="/usr/bin/pdftotext"), patch.object(
        preflight.subprocess,
        "run",
        return_value=type("Completed", (), {"returncode": 0, "stdout": output})(),
    ) as run:
        result = preflight.preflight_pdf_metadata(source, source_kind="project-sync", workspace="Affaires")

    assert result.fields["index"].value == "A"
    assert result.fields["document_date"].value == "07/11/2025"
    assert result.fields["index"].page == 1
    assert "-l" in run.call_args_list[0].args[0]
    first_call = run.call_args_list[0].args[0]
    assert first_call[first_call.index("-l") + 1] == "3"


def test_metadata_preflight_searches_page_two_only_when_cover_lacks_field() -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    result = preflight._extract_labelled_fields(
        ["VOTRE DEVIS", "NOS COORDONNÉES\nEn date du : 29/09/2026"],
        "affaires",
    )

    assert result.fields["document_date"].value == "29/09/2026"
    assert result.fields["document_date"].page == 2


def test_metadata_preflight_prefers_cover_over_later_references() -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    result = preflight._extract_labelled_fields(
        ["CCTP Indice : B Date : 21.09.2026", "Étude géotechnique indice A — 07/11/2025"],
        "affaires",
    )

    assert result.fields["index"].value == "B"
    assert result.fields["document_date"].value == "21.09.2026"


def test_preflight_cache_links_source_path_and_digest_for_cockpit(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-test")
    result = preflight.PreflightResult(
        "affaires",
        "complete",
        {"document_date": preflight.FieldCandidate("27/01/2025", 1, "Date : 27/01/2025")},
        document_title_candidate=preflight.FieldCandidate("Notice technique", 1, "NOTICE TECHNIQUE"),
    )
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        source_kind="project-sync",
    )
    with patch.object(module, "preflight_pdf_metadata", return_value=result):
        producer._metadata_preflight(source, source_sha256="digest-1", workspace="Affaires")

    import sqlite3

    connection = sqlite3.connect(tmp_path / "state.sqlite3")
    try:
        row = connection.execute(
            "SELECT workspace, source_path, source_sha256 FROM hindsight_metadata_preflight_source"
        ).fetchone()
    finally:
        connection.close()
    assert row == ("Affaires", "Notice.pdf", "digest-1")


def test_unlabelled_issuer_is_a_separate_review_candidate(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-test")
    candidate = preflight.IssuerCandidate(
        "Atelier Exemple", 1, "name_and_address", "Atelier Exemple - 10 rue des Arts"
    )
    result = preflight.PreflightResult(
        "affaires", "no_explicit_fields", {}, issuer_candidates=(candidate,)
    )
    restored = preflight.PreflightResult.from_dict(result.as_dict())
    assert restored.issuer_candidates == (candidate,)

    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        source_kind="project-sync",
    )
    with patch.object(module, "preflight_pdf_metadata", return_value=result):
        card = _card()
        card["issuer"] = None
        retained = producer._candidate(card, current_paths=set(), claimed_auto_ids=set())

    assert retained is not None
    assert "document_emetteur" not in retained.metadata
    suggested = json.loads(retained.metadata["metadata_preflight_issuer_candidates"])
    assert suggested == [candidate.__dict__]
    assert suggested[0]["status"] == "candidate_unconfirmed"


def test_unlabelled_issuer_detector_uses_contact_and_excludes_software() -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    xhtml = '''<html xmlns="http://www.w3.org/1999/xhtml"><body><doc><page width="600" height="800">
      <flow><block><line yMin="40" yMax="50"><word>Atelier</word><word>Exemple</word><word>-</word><word>10</word><word>rue</word><word>des</word><word>Arts</word></line>
      <line yMin="60" yMax="70"><word>contact@atelier-exemple.fr</word></line>
      <line yMin="72" yMax="82"><word>M.</word><word>ou</word><word>Mme</word><word>LEVOYER/JAGOREL</word></line>
      <line yMin="84" yMax="94"><word>N°</word><word>D2026043</word></line>
      <line yMin="96" yMax="106"><word>S</word><word>OMMAIRE</word></line>
      <line yMin="710" yMax="720"><word>ClimaWin</word><word>2020</word><word>-</word><word>licence</word><word>BIMOPSI</word></line></block></flow>
    </page></doc></body></html>'''
    document = preflight.ElementTree.fromstring(xhtml)
    candidates = preflight._unlabelled_issuer_candidates(document)

    assert any(
        c.value == "Atelier Exemple (atelier-exemple.fr)"
        and c.signal == "organization_name_and_domain"
        and c.status == "candidate_unconfirmed"
        for c in candidates
    )
    assert not any("ClimaWin" in c.value or "BIMOPSI" in c.value for c in candidates)
    assert not any("LEVOYER" in c.value or "D2026043" in c.value or "OMMAIRE" in c.value for c in candidates)


def test_preflight_uses_one_bbox_extraction_and_merges_matching_company_domain(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "piece.pdf"
    source.write_bytes(b"%PDF-test")
    xhtml = '''<html xmlns="http://www.w3.org/1999/xhtml"><body><doc><page width="600" height="800">
      <flow><block><line yMin="40" yMax="50"><word>ENTREPRISE</word><word>EXEMPLE</word></line>
      <line yMin="60" yMax="70"><word>contact@entreprise-exemple.fr</word></line>
      <line yMin="72" yMax="82"><word>Indice</word><word>:</word><word>B</word></line></block></flow>
    </page></doc></body></html>'''
    with patch.object(
        preflight.shutil,
        "which",
        side_effect=lambda name: "/usr/bin/pdftotext" if name == "pdftotext" else None,
    ), patch.object(
        preflight.subprocess,
        "run",
        return_value=type("Completed", (), {"returncode": 0, "stdout": xhtml})(),
    ) as run:
        result = preflight.preflight_pdf_metadata(source, source_kind="project-sync", workspace="Affaires")

    assert run.call_count == 1
    assert "-bbox-layout" in run.call_args.args[0]
    assert result.fields["index"].value == "B"
    assert len(result.issuer_candidates) == 1
    assert result.issuer_candidates[0].value == "ENTREPRISE EXEMPLE (entreprise-exemple.fr)"
    assert result.issuer_candidates[0].signal == "organization_name_and_domain"
    assert result.issuer_candidates[0].status == "candidate_unconfirmed"


def test_bbox_text_rejoins_aligned_revision_table_cells() -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    xhtml = '''<html xmlns="http://www.w3.org/1999/xhtml"><body><doc><page width="600" height="800">
      <flow><block>
        <line yMin="100" yMax="110" xMin="20"><word>Indice</word></line>
        <line yMin="100" yMax="110" xMin="80"><word>Date</word></line>
        <line yMin="100" yMax="110" xMin="150"><word>Modification</word></line>
        <line yMin="120" yMax="130" xMin="20"><word>A</word></line>
        <line yMin="120" yMax="130" xMin="80"><word>07/11/2025</word></line>
        <line yMin="120" yMax="130" xMin="150"><word>Diffusion</word></line>
      </block></flow>
    </page></doc></body></html>'''
    _document, pages = preflight._bbox_pages_and_text(xhtml)
    result = preflight._extract_labelled_fields(pages, "affaires")

    assert result.fields["index"].value == "A"
    assert result.fields["document_date"].value == "07/11/2025"


def test_candidate_sends_only_missing_preflight_values_with_provenance(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-test")
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        source_kind="project-sync",
    )
    expected = preflight.PreflightResult(
        "affaires",
        "complete",
        {
            "document_date": preflight.FieldCandidate("12/09/2026", 1, "Date du document : 12/09/2026"),
            "index": preflight.FieldCandidate("B", 1, "Indice : B"),
            "issuer": preflight.FieldCandidate("Wrong issuer", 1, "Émetteur : Wrong issuer"),
            "recipient": preflight.FieldCandidate("Client", 1, "Destinataire : Client"),
        },
        corps_etat_candidates=(
            preflight.DocumentFacetCandidate("menuiserie_exterieure", 1, "Lot 03 — Menuiseries extérieures"),
        ),
        sujet_technique_candidates=(
            preflight.DocumentFacetCandidate("structure", 1, "Étude structure bois"),
        ),
        document_title_candidate=preflight.FieldCandidate(
            "Réfection de la couverture", 1, "Titre : Réfection de la couverture"
        ),
        document_summary_candidate=preflight.FieldCandidate(
            "Le présent devis décrit les travaux de réfection de la couverture et précise les matériaux ainsi que les conditions de réalisation.",
            1,
            "Le présent devis décrit les travaux de réfection de la couverture et précise les matériaux ainsi que les conditions de réalisation.",
            "extractive_preview",
        ),
    )
    card = _card()
    with patch.object(module, "preflight_pdf_metadata", return_value=expected) as run_preflight:
        candidate = producer._candidate(card, current_paths=set(), claimed_auto_ids=set())
        assert candidate is not None
        cached = producer._metadata_preflight(
            source,
            source_sha256=candidate.source_sha256,
            workspace="Affaires",
        )

    assert cached == expected
    assert run_preflight.call_count == 1
    assert candidate.metadata["document_date"] == "12/09/2026"
    assert "document_date_source" not in candidate.metadata
    assert candidate.metadata["document_indice"] == "B"
    assert candidate.metadata["issuer"] == "agency"
    assert candidate.metadata["document_emetteur"] == "Wrong issuer"
    assert candidate.metadata["document_destinataire"] == "Client"
    assert candidate.metadata["metadata_preflight_profile"] == "affaires"
    assert candidate.metadata["metadata_preflight_document_title_candidate"] == "Réfection de la couverture"
    assert candidate.metadata["metadata_preflight_summary_candidate"].startswith("Le présent devis décrit")
    assert json.loads(candidate.metadata["metadata_preflight_summary_evidence"])["source"] == "extractive_preview"
    assert json.loads(candidate.metadata["metadata_preflight_document_title_evidence"])["status"] == "candidate_unconfirmed"
    assert "metadata_preflight_evidence" in candidate.metadata
    assert json.loads(candidate.metadata["metadata_preflight_corps_etat_candidates"])[0]["value"] == "menuiserie_exterieure"
    assert json.loads(candidate.metadata["metadata_preflight_sujets_techniques_candidates"])[0]["value"] == "structure"
    assert "construction trade candidates=menuiserie_exterieure" in candidate.context
    assert "document title candidate=Réfection de la couverture" in candidate.context
    assert "not an AI summary" in candidate.context


def test_preflight_extracts_a_verbatim_one_sentence_preview() -> None:
    preflight = sys.modules["document_metadata_preflight"]
    sentence = (
        "Le présent document décrit les travaux prévus pour la rénovation du bâtiment et précise les modalités "
        "de réalisation, les matériaux retenus ainsi que les contraintes du chantier."
    )
    result = preflight._extract_document_summary_candidate(["DEVIS\n" + sentence])
    assert result is not None
    assert result.value == sentence
    assert result.source == "extractive_preview"


def test_pdf_creation_date_fallback_is_marked_in_hindsight_metadata(tmp_path: Path) -> None:
    module = _module()
    preflight = sys.modules["document_metadata_preflight"]
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-test")
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        source_kind="project-sync",
    )
    result = preflight.PreflightResult(
        "affaires",
        "complete",
        {
            "pdf_creation_date": preflight.FieldCandidate(
                "17/09/2026",
                0,
                "PDF metadata CreationDate: 2026-09-17T12:30:00+02:00",
                "pdf_creation_metadata",
            )
        },
    )
    with patch.object(module, "preflight_pdf_metadata", return_value=result):
        candidate = producer._candidate(_card(), current_paths=set(), claimed_auto_ids=set())

    assert candidate is not None
    assert "document_date" not in candidate.metadata
    assert candidate.metadata["document_creation_date"] == "17/09/2026"
    assert candidate.metadata["document_creation_date_source"] == "pdf_info_creation_date"
    assert "not the document issue date" in candidate.context


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


@pytest.mark.parametrize("workspace", ["Affaires", "Bibliotheque"])
def test_explicit_ocr_resubmits_markdown_under_stable_identity_and_preserves_pdf(tmp_path: Path, workspace: str) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    original_bytes = b"%PDF-image-only-source"
    source.write_bytes(original_bytes)
    cache_dir = tmp_path / "state" / "ocr-cache"

    class FailedThenCompletedClient(FakeClient):
        def __init__(self) -> None:
            super().__init__(["failed", "completed"])

        def operation_status(self, operation_id: str):
            self.polls.append(operation_id)
            status = self.statuses.pop(0) if self.statuses else "completed"
            error = "No content extracted from PDF" if status == "failed" else None
            return {"operation_id": operation_id, "status": status, "error_message": error}

        def get_document(self, document_id: str):
            if len(self.retains) == 1:
                raise RuntimeError('Hindsight HTTP 404: {"detail":"Document not found"}')
            return {"id": document_id, "original_text": "Texte OCR exploitable avec assez de contenu." * 8}

    class FakeOcr:
        def __init__(self) -> None:
            self.cache_dir = cache_dir

        def process(self, path: Path, *, expected_source_sha256: str, output_path: Path):
            from document_ocr import OcrResult

            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_source_sha256
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("# Procès-verbal\n\nTexte transcrit." * 20, encoding="utf-8")
            return OcrResult(output_path, "vision:test", expected_source_sha256, 3)

    client = FailedThenCompletedClient()
    queue_db = tmp_path / "state" / "queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path), ("Bibliotheque", tmp_path)],
        state_db=tmp_path / "state" / "index.sqlite3",
        processing_queue_db=queue_db,
        client=client,
        ocr_processor=FakeOcr(),
    )
    card = _card(workspace=workspace)

    assert _first_queued_reconcile(producer, _snapshot(card, workspace))["submitted"] == 1
    producer.reconcile(_snapshot(card, workspace))
    queue = module.ProcessingQueue(queue_db)
    assert queue.get_item(workspace, "doc-notice")["hindsight_status"] == "FAILED"
    queue.request_ocr(workspace, "doc-notice")

    producer.reconcile(_snapshot(card, workspace))
    assert queue.get_item(workspace, "doc-notice")["hindsight_status"] == "OCR_PROCESSING"
    producer._ocr_futures[(workspace, "doc-notice")].result(timeout=5)
    producer.reconcile(_snapshot(card, workspace))

    # OCR must pass its own metadata preflight before the Markdown is retained.
    assert len(client.retains) == 1
    _wait_preflight(producer, {"doc-notice"})
    assert queue.get_item(workspace, "doc-notice")["ocr_preflight_source_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    producer.reconcile(_snapshot(card, workspace))

    assert len(client.retains) == 2
    ocr_call = client.retains[1]
    assert ocr_call["source"].suffix == ".md"
    assert ocr_call["document_id"] == "doc-notice:source"
    assert ocr_call["metadata"]["ocr_derived_from"] == "Notice.pdf"
    assert ocr_call["metadata"]["ocr_source_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert ocr_call["metadata"]["ocr_artifact_name"] == ocr_call["source"].name
    assert ocr_call["metadata"]["metadata_preflight_text_source"] == "ocr_markdown"
    assert "/" not in ocr_call["metadata"]["ocr_artifact_name"]
    assert "OCR artifact filename=" + ocr_call["source"].name in ocr_call["context"]
    assert "ocr:complete" in ocr_call["tags"]
    assert source.read_bytes() == original_bytes
    assert queue.get_item(workspace, "doc-notice")["hindsight_status"] == "MEMORIZING"

    producer.reconcile(_snapshot(card, workspace))
    final = queue.get_item(workspace, "doc-notice")
    assert final["hindsight_status"] == "MEMORIZED"
    assert final["ocr_status"] == "DONE"
    assert source.read_bytes() == original_bytes


def test_ocr_and_hindsight_advance_independently_and_ocr_completion_wakes_coordinator(tmp_path: Path) -> None:
    module = _module()
    for name in ("one.pdf", "two.pdf", "scan.pdf"):
        (tmp_path / name).write_bytes(b"%PDF-" + name.encode())
    ocr_started, release_ocr, wake = threading.Event(), threading.Event(), threading.Event()

    class BlockingOcr:
        cache_dir = tmp_path / "ocr-cache"

        def process(self, source, *, expected_source_sha256, output_path):
            from document_ocr import OcrResult
            ocr_started.set()
            assert release_ocr.wait(5), "test did not release OCR"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("# Texte OCR\n" * 30)
            return OcrResult(output_path, "docling:test", expected_source_sha256, 1)

    class RetainedOnlyClient(FakeClient):
        def get_document(self, document_id):
            if not any(call["document_id"] == document_id for call in self.retains):
                raise RuntimeError("Hindsight HTTP 404: Document not found")
            return super().get_document(document_id)

    client = RetainedOnlyClient(["processing"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=tmp_path / "state.sqlite3",
        processing_queue_db=tmp_path / "queue.sqlite3", client=client,
        ocr_processor=BlockingOcr(),
    )
    cards = [_card("one.pdf", document_id="doc-one"), _card("two.pdf", document_id="doc-two")]
    snapshot = {"workspaces": [{"name": "Affaires", "available": True, "cards": cards, "errors": []}]}
    _first_queued_reconcile(producer, snapshot)
    queue = producer.processing_queue
    queue.upsert_candidate(
        workspace="Affaires", document_id="doc-scan", source_path="scan.pdf",
        source_sha256=hashlib.sha256((tmp_path / "scan.pdf").read_bytes()).hexdigest(),
        preflight_status="TO_PROCESS", hindsight_status="FAILED",
    )
    queue.set_status("Affaires", "doc-scan", error="No content extracted from PDF")
    _wait_preflight(producer, {"doc-scan"})
    assert queue.get_item("Affaires", "doc-scan")["error"] == "No content extracted from PDF"
    queue.request_ocr("Affaires", "doc-scan")
    cards.append(_card("scan.pdf", document_id="doc-scan"))
    producer.on_work_available = wake.set
    try:
        producer.reconcile(snapshot)
        assert ocr_started.wait(5)
        assert queue.get_item("Affaires", "doc-one")["hindsight_status"] == "MEMORIZING"
        assert queue.get_item("Affaires", "doc-scan")["ocr_status"] == "PROCESSING"
        client.statuses = ["completed"]
        producer.reconcile(snapshot)
        assert [call["source"].name for call in client.retains] == ["one.pdf", "two.pdf"]
        assert queue.get_item("Affaires", "doc-scan")["ocr_status"] == "PROCESSING"
        release_ocr.set()
        producer._ocr_futures[("Affaires", "doc-scan")].result(timeout=5)
        assert wake.wait(5)
        client.statuses = ["processing"]
        producer.reconcile(snapshot)
        assert len(client.retains) == 2
        assert queue.get_item("Affaires", "doc-scan")["ocr_status"] == "READY"
        assert queue.get_item("Affaires", "doc-scan")["hindsight_status"] == "OCR_READY"
        _wait_preflight(producer, {"doc-scan"})
        client.statuses = ["completed"]
        producer.reconcile(snapshot)
        assert len(client.retains) == 3
        assert client.retains[-1]["source"].suffix == ".md"
        assert (tmp_path / "scan.pdf").read_bytes() == b"%PDF-scan.pdf"
    finally:
        release_ocr.set()


def test_user_exclusion_stays_visible_and_prevents_any_hindsight_retain(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Perspective.pdf"
    source.write_bytes(b"%PDF-perspective-image")
    queue_db = tmp_path / "state" / "queue.sqlite3"
    queue = module.ProcessingQueue(queue_db)
    queue.upsert_candidate(
        workspace="Affaires", document_id="doc-perspective",
        source_path="Perspective.pdf", source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    queue.do_not_memorize("Affaires", "doc-perspective")
    client = FakeClient()
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state" / "index.sqlite3",
        processing_queue_db=queue_db,
        client=client,
    )

    producer.reconcile(_snapshot(_card("Perspective.pdf", document_id="doc-perspective")))

    assert client.retains == []
    visible = queue.list_items()["items"]
    assert len(visible) == 1
    assert visible[0]["hindsight_status"] == "NOT_MEMORIZED"
    assert visible[0]["user_decision"] == "DO_NOT_SEND"


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
    assert _row(tmp_path / "state.sqlite3")["status"] == "VERIFYING"

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
        processing_queue_db=db,
    )

    _first_queued_reconcile(producer, _snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    quarantined = producer.reconcile(_snapshot(None))

    assert quarantined["quarantined"] == 1
    assert quarantined["delete_missing"] == "complete-scan-quarantine-then-grace"
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

    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "UPDATE hindsight_sync SET updated_at='2020-01-01T00:00:00Z'"
        )
        connection.commit()
    finally:
        connection.close()
    archived = producer.reconcile(_snapshot(None))
    assert archived["archived"] == 1
    assert _row(db)["status"] == "ARCHIVED"
    assert _row(db)["missing_observations"] == 2
    assert client.deleted_documents == ["doc-notice:source"]
    queue = module.ProcessingQueue(db)
    assert queue.list_items()["items"] == []

    restored = _first_queued_reconcile(producer, _snapshot(_card()))
    assert restored["submitted"] == 1
    assert queue.list_items()["items"][0]["hindsight_status"] == "MEMORIZING"


def test_missing_document_is_not_deleted_during_quarantine_grace_period(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client
    )

    _first_queued_reconcile(producer, _snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(None))
    result = producer.reconcile(_snapshot(None))

    assert result["archived"] == 0
    assert _row(db)["status"] == "QUARANTINED"
    assert client.deleted_documents == []


def test_incomplete_scan_never_advances_missing_document_lifecycle(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    db = tmp_path / "state.sqlite3"
    client = FakeClient(["completed"])
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)], state_db=db, client=client
    )

    producer.reconcile(_snapshot(_card()))
    producer.reconcile(_snapshot(_card()))
    incomplete = _snapshot(None)
    incomplete["workspaces"][0]["complete"] = False
    incomplete["workspaces"][0]["errors"] = ["Dossier illisible"]
    producer.reconcile(incomplete)

    assert _row(db)["status"] == "COMPLETED"
    assert _row(db)["missing_observations"] == 0
    assert client.deleted_documents == []


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


def test_preflight_source_io_error_is_deferred_instead_of_failed(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-preflight-transient-error")
    queue_db = tmp_path / "queue.sqlite3"
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
        processing_queue_db=queue_db,
    )
    queue = module.ProcessingQueue(queue_db)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    queue.upsert_candidate(
        workspace="Affaires", document_id="doc-notice", source_path="Notice.pdf",
        source_sha256=source_sha256, preflight_status="TO_PROCESS", hindsight_status="QUEUED",
    )
    request = queue.preflight_requests()[0]
    monkeypatch.setattr(
        module, "_sha256",
        lambda _path: (_ for _ in ()).throw(PermissionError("temporary NAS read failure")),
    )

    producer._process_preflight_request(request, stability_checked=True)

    item = queue.list_items(include_memorized=True)["items"][0]
    assert item["preflight_status"] == "STABILIZING"
    assert item["hindsight_status"] == "MODIFIED"
    assert ("Affaires", "doc-notice") in producer._preflight_waiting_source


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
    source.write_bytes(b"%PDF-1.7\nEXACT-PDF-BYTES")
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
        candidate = {
            "value": "Atelier Exemple (atelier-exemple.fr)",
            "page": 1,
            "signal": "organization_name_and_domain",
            "evidence": "Atelier Exemple — contact@atelier-exemple.fr",
            "status": "candidate_unconfirmed",
        }
        operation_id = client.retain_file(
            source,
            document_id="doc-notice:source",
            context="AFFAIRES professional source document",
            tags=["workspace:affaires"],
            metadata={
                "pantheon_document_id": "doc-notice",
                "metadata_preflight_issuer_candidates": json.dumps(
                    [candidate], ensure_ascii=False, separators=(",", ":")
                ),
            },
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
    boundary = request.get_header("Content-type").split("boundary=", 1)[1]
    request_part = body.split(b"\r\n\r\n", 1)[1].split(
        f"\r\n--{boundary}".encode(), 1
    )[0]
    envelope = json.loads(request_part)
    sent_metadata = envelope["files_metadata"][0]["metadata"]
    sent_candidates = json.loads(sent_metadata["metadata_preflight_issuer_candidates"])
    assert sent_candidates == [candidate]
    assert "document_emetteur" not in sent_metadata


def test_http_client_lists_recent_file_retain_operations_for_recovery() -> None:
    module = _module()
    captured = {}
    expected = {
        "operations": [{
            "id": "op-123",
            "operation_type": "file_convert_retain",
            "document_id": "doc-notice:source",
        }]
    }

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response(expected)

    client = module.HindsightHTTPClient("http://127.0.0.1:8888", "PROJECTS")
    with patch.object(module, "urlopen", fake_urlopen):
        operations = client.list_file_retain_operations(limit=250)

    assert operations == expected["operations"]
    assert captured["request"].method == "GET"
    assert captured["request"].full_url.endswith(
        "/v1/default/banks/PROJECTS/operations?type=file_convert_retain&limit=100"
    )


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


def test_http_client_rechecks_source_hash_before_network_submission(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF-new-bytes")
    client = module.HindsightHTTPClient("http://127.0.0.1:8888", "affaires")

    with patch.object(module, "urlopen") as mocked:
        try:
            client.retain_file(
                source,
                document_id="doc-notice:source",
                context="AFFAIRES professional source document",
                tags=["workspace:affaires"],
                metadata={"pantheon_document_id": "doc-notice"},
                expected_source_sha256=hashlib.sha256(b"%PDF-old-bytes").hexdigest(),
            )
        except RuntimeError as exc:
            assert "Source changed before Hindsight upload" in str(exc)
        else:
            raise AssertionError("changed source bytes should block the upload")

    mocked.assert_not_called()


def test_http_client_enforces_upload_bound_if_source_grows_after_stat(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"0123456789abcdef")
    client = module.HindsightHTTPClient(
        "http://127.0.0.1:8888", "affaires", max_file_bytes=8
    )

    with patch.object(Path, "stat", return_value=SimpleNamespace(st_size=4)):
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
                raise AssertionError("the bounded read should reject a file that grew")

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


def test_manual_document_note_is_bound_to_stable_identity_after_path_move(tmp_path: Path) -> None:
    module = _module()
    old_path = tmp_path / "old" / "Notice.pdf"
    old_path.parent.mkdir()
    old_path.write_bytes(b"%PDF")
    producer = module.HindsightProducer(
        roots=[("Affaires", tmp_path)],
        state_db=tmp_path / "state.sqlite3",
        client=FakeClient(),
    )
    connection = sqlite3.connect(producer.state_db)
    try:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='workspace_document_metadata_overrides'"
        ).fetchone() == (1,)
        connection.execute(
            "INSERT INTO workspace_document_notes VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("Affaires", "old/Notice.pdf", "doc-1", "old-hash", "Vérifier la version signée.", "created", "updated"),
        )
        connection.commit()
    finally:
        connection.close()

    producer._bind_document_note("Affaires", "new/Notice.pdf", "new-hash", "doc-1")

    connection = sqlite3.connect(producer.state_db)
    try:
        row = connection.execute(
            "SELECT workspace, source_path, document_id, source_sha256, note FROM workspace_document_notes"
        ).fetchone()
    finally:
        connection.close()
    assert row == (
        "Affaires", "new/Notice.pdf", "doc-1", "new-hash", "Vérifier la version signée."
    )

@pytest.mark.parametrize('payload,name,wanted', [
    (b'%PDF-1.7\n', 'document.txt', ('document.pdf','application/pdf','pdf')),
    (b'<html><body>Bonjour</body></html>', 'document.pdf', ('document.html','text/html','html')),
    ('Texte français'.encode(), 'document.pdf', ('document.txt','text/plain','txt')),
    (b'a,b\n1,2', 'document.csv', ('document.csv','text/csv','csv')),
    (b'# Titre\nTexte', 'document.md', ('document.md','text/markdown','md')),
])
def test_upload_detects_content_and_preserves_declared_text_structure(payload, name, wanted):
    assert _module()._source_upload_format(payload, name) == wanted


@pytest.mark.parametrize('marker,expected', [
    ('word/document.xml','docx'), ('xl/workbook.xml','xlsx'),
    ('ppt/presentation.xml','pptx'), ('META-INF/container.xml','epub'),
])
def test_upload_detects_office_or_epub_without_extracting_members(marker, expected):
    import io, zipfile
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z: z.writestr(marker, '<root/>')
    name, mime, detected = _module()._source_upload_format(buf.getvalue(), 'wrong.pdf')
    assert name == 'wrong.'+expected
    assert detected == expected
    assert mime != 'application/pdf'


@pytest.mark.parametrize('data,reason', [
    (b'', 'empty file'), (b'\xff\x00\xfe\x81', 'not identified'),
    (b'PK\x03\x04partial', 'incomplete ZIP'),
    (b'\x89PNG\r\n\x1a\nimage', 'image content'),
    (b'{\\rtf1 document}', 'RTF content'),
])
def test_upload_unknown_or_unhandled_format_is_explicit_not_ocr(data, reason):
    with pytest.raises(RuntimeError, match=reason):
        _module()._source_upload_format(data, 'misleading.pdf')


def test_http_upload_mismatch_keeps_raw_file_and_original_locator(tmp_path):
    module=_module()
    source=tmp_path/'source.pdf'
    raw=b'<html><body>Source</body></html>'
    source.write_bytes(raw)
    captured={}
    def respond(request, timeout):
        captured['body']=request.data
        return _Response({'operation_ids':['op-format']})
    metadata={'source_path':'folder/source.pdf','title':'source.pdf'}
    with patch.object(module,'urlopen',respond):
        result=module.HindsightHTTPClient('http://127.0.0.1:8888','test').retain_file(
            source, document_id='doc:source', context='Source', tags=[], metadata=metadata,
            expected_source_sha256=hashlib.sha256(raw).hexdigest())
    assert result=='op-format'
    assert b'filename="source.html"' in captured['body']
    assert b'"source_path":"folder/source.pdf"' in captured['body']
    assert b'"source_detected_format":"html"' in captured['body']
    assert source.read_bytes()==raw
    assert not (tmp_path/'source.html').exists()
    assert metadata=={'source_path':'folder/source.pdf','title':'source.pdf'}


def test_unknown_binary_does_not_reach_hindsight(tmp_path):
    module=_module()
    source=tmp_path/'broken.pdf'
    source.write_bytes(b'\x89\xed\x7a\x7b\x43\x8a\xca\x68')
    with patch.object(module,'urlopen') as mocked:
        with pytest.raises(RuntimeError,match='Source format not identified'):
            module.HindsightHTTPClient('http://127.0.0.1:8888','test').retain_file(
                source, document_id='doc:source', context='', tags=[], metadata={})
    mocked.assert_not_called()


@pytest.mark.parametrize("message", [
    "Source format not identified: binary content or unsupported encoding; check original file",
    "Source format: empty file; nothing to extract",
    "Source format: image content; an image OCR/vision extraction route is required",
])
def test_format_rejection_is_a_known_local_failure_not_an_uncertain_submission(message):
    assert _module()._submission_outcome_uncertain(message) is False
