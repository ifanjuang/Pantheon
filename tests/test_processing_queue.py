from __future__ import annotations

import os
import sqlite3

import pytest

from implementation.workspace_cockpit.processing_queue import CoordinatorLock, ProcessingQueue


def test_queue_preserves_priority_and_marks_source_changes(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/a.pdf", source_sha256="sha1"
    )
    queue.upsert_candidate(
        workspace="Bibliotheque", document_id="d2", source_path="B/b.pdf", source_sha256="sha2"
    )
    queue.reorder([("Bibliotheque", "d2"), ("Affaires", "d1")])

    changed = queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/renamed.pdf", source_sha256="sha3"
    )
    assert changed["priority"] == queue.list_items()["items"][1]["priority"]
    assert changed["preflight_status"] == "STABILIZING"
    assert changed["hindsight_status"] == "MODIFIED"


def test_repeated_preflight_reads_close_sqlite_file_descriptors(tmp_path) -> None:
    fd_directory = "/proc/self/fd"
    if not os.path.isdir(fd_directory):
        pytest.skip("file descriptor count requires procfs")
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    before = len(os.listdir(fd_directory))

    for _ in range(25):
        assert queue.preflight_requests() == []

    after = len(os.listdir(fd_directory))
    assert after <= before + 1


def test_worker_health_reports_heartbeat_and_staleness(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.publish_worker_health("preflight", {
        "running": True,
        "last_success_at": "2026-10-30T10:00:00Z",
        "retry_waiting": 2,
    })

    health = queue.worker_health(stale_after_seconds=90)

    assert len(health) == 1
    assert health[0]["worker"] == "preflight"
    assert health[0]["running"] is True
    assert health[0]["retry_waiting"] == 2
    assert health[0]["heartbeat_at"]
    assert health[0]["stale"] is False

    with sqlite3.connect(queue.database) as connection:
        connection.execute(
            "UPDATE processing_worker_health SET updated_at='2000-01-01T00:00:00Z' WHERE worker_name='preflight'"
        )
    assert queue.worker_health(stale_after_seconds=90)[0]["stale"] is True


def test_pause_is_scoped_and_retry_only_moves_errors(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/a.pdf", source_sha256="sha1"
    )
    queue.upsert_candidate(
        workspace="Bibliotheque", document_id="d2", source_path="B/b.pdf", source_sha256="sha2"
    )
    assert not queue.is_paused("Affaires")
    queue.set_paused("vault:Affaires", True)
    assert queue.is_paused("Affaires")
    assert not queue.is_paused("Bibliotheque")
    queue.set_status("Affaires", "d1", hindsight_status="FAILED", error="API indisponible")
    queue.retry("Affaires", "d1")
    item = queue.list_items(workspace="Affaires")["items"][0]
    assert item["hindsight_status"] == "QUEUED"
    assert item["error"] is None


def test_lane_pause_targets_only_the_listed_items_and_resumes_independently(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="BLANC/a.pdf",
        source_sha256="sha1", preflight_status="TO_PROCESS",
    )
    queue.upsert_candidate(
        workspace="Affaires", document_id="d2", source_path="FLOQUET/b.pdf",
        source_sha256="sha2", preflight_status="TO_PROCESS",
    )

    queue.set_items_paused([("Affaires", "d1")], "preflight", True)
    assert queue.is_item_paused("Affaires", "d1", "preflight")
    assert not queue.is_item_paused("Affaires", "d1", "ocr")
    assert not queue.is_item_paused("Affaires", "d2", "preflight")
    assert not queue.claim_preflight("Affaires", "d1", "sha1")
    assert queue.claim_preflight("Affaires", "d2", "sha2")

    queue.set_items_paused([("Affaires", "d1")], "preflight", False)
    assert not queue.is_item_paused("Affaires", "d1", "preflight")
    assert queue.claim_preflight("Affaires", "d1", "sha1")
    items = {item["document_id"]: item for item in queue.list_items()["items"]}
    assert items["d1"]["paused_preflight"] == 0
    assert items["d2"]["paused_preflight"] == 0


def test_ocr_queue_persists_only_portable_markdown_filename(tmp_path) -> None:
    database = tmp_path / "queue.sqlite3"
    queue = ProcessingQueue(database)
    queue.upsert_candidate(
        workspace="Bibliotheque", document_id="d-ocr", source_path="guide.pdf", source_sha256="a" * 64
    )
    queue.set_ocr_status(
        "Bibliotheque", "d-ocr", status="READY",
        output_filename="a" * 64 + ".md", engine="docling",
    )
    item = queue.get_item("Bibliotheque", "d-ocr")
    assert item["ocr_filename"] == "a" * 64 + ".md"
    assert item["ocr_output_path"] is None
    with pytest.raises(ValueError, match="basename"):
        queue.set_ocr_status(
            "Bibliotheque", "d-ocr", status="READY",
            output_filename="../outside.md",
        )


def test_legacy_ocr_absolute_path_migrates_to_filename(tmp_path) -> None:
    database = tmp_path / "queue.sqlite3"
    queue = ProcessingQueue(database)
    queue.upsert_candidate(
        workspace="Affaires", document_id="d-legacy", source_path="scan.pdf", source_sha256="b" * 64
    )
    with queue._connection() as connection:
        connection.execute(
            "UPDATE processing_queue SET ocr_output_path=? WHERE workspace=? AND document_id=?",
            ("/var/lib/old/ocr-cache/derived.md", "Affaires", "d-legacy"),
        )
    migrated = ProcessingQueue(database).get_item("Affaires", "d-legacy")
    assert migrated["ocr_filename"] == "derived.md"
    assert migrated["ocr_output_path"] is None


def test_reorder_requires_complete_active_set_and_rejects_stale_revision(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/a.pdf", source_sha256="sha1"
    )
    queue.upsert_candidate(
        workspace="Bibliotheque", document_id="d2", source_path="B/b.pdf", source_sha256="sha2"
    )
    with pytest.raises(ValueError, match="every active queue item"):
        queue.reorder([("Affaires", "d1")])
    with pytest.raises(RuntimeError, match="queue_revision_conflict"):
        queue.reorder([("Affaires", "d1"), ("Bibliotheque", "d2")], expected_revision=99)


def test_reorder_keeps_failed_and_verification_items_in_shared_order(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    for workspace, document_id in (
        ("Affaires", "failed"), ("Bibliotheque", "queued"), ("Affaires", "verify")
    ):
        queue.upsert_candidate(
            workspace=workspace, document_id=document_id,
            source_path=f"{document_id}.pdf", source_sha256=document_id,
        )
    queue.set_status("Affaires", "failed", hindsight_status="FAILED", error="upload failed")
    queue.set_status("Affaires", "verify", hindsight_status="VERIFY", error="outcome unclear")

    items = queue.list_items()["items"]
    revision = queue.list_items()["revision"]
    queue.reorder(
        [("Affaires", "verify"), ("Affaires", "failed"), ("Bibliotheque", "queued")],
        expected_revision=revision,
    )

    ordered = queue.list_items()["items"]
    assert [(item["workspace"], item["document_id"]) for item in ordered] == [
        ("Affaires", "verify"), ("Affaires", "failed"), ("Bibliotheque", "queued")
    ]
    assert {item["hindsight_status"] for item in ordered} == {"VERIFY", "FAILED", "NOT_SENT"}


def test_move_reorders_single_item_including_errors_without_full_payload(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    for document_id in ("one", "two", "three"):
        queue.upsert_candidate(
            workspace="Affaires", document_id=document_id,
            source_path=f"{document_id}.pdf", source_sha256=document_id,
        )
    queue.set_status("Affaires", "two", hindsight_status="FAILED", error="upload failed")
    revision = queue.list_items()["revision"]

    result = queue.move(("Affaires", "two"), 0, expected_revision=revision)

    assert [item["document_id"] for item in result["items"]] == ["two", "one", "three"]
    assert result["items"][0]["hindsight_status"] == "FAILED"
    with pytest.raises(RuntimeError, match="queue_revision_conflict"):
        queue.move(("Affaires", "three"), 0, expected_revision=revision)
    with pytest.raises(ValueError, match="position_out_of_range"):
        queue.move(("Affaires", "three"), 3)


def test_global_pause_applies_to_every_vault(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.set_paused("global", True)
    assert queue.is_paused("Affaires")
    assert queue.is_paused("Bibliotheque")


def test_verification_request_is_durable_optimistic_and_never_a_retry(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/a.pdf", source_sha256="sha1"
    )
    queue.set_status("Affaires", "d1", hindsight_status="VERIFY", error="outcome unclear")

    first_request = queue.request_verification("Affaires", "d1")
    assert queue.verification_requests() == [{
        "workspace": "Affaires", "document_id": "d1",
        "verification_requested_at": first_request,
    }]
    with pytest.raises(RuntimeError, match="remote_outcome_requires_verification"):
        queue.retry("Affaires", "d1")

    # A second click during a worker check must survive clearing the old request.
    second_request = queue.request_verification("Affaires", "d1")
    assert not queue.clear_verification_request("Affaires", "d1", first_request)
    assert queue.clear_verification_request("Affaires", "d1", second_request)
    assert queue.verification_requests() == []

    queue.set_status("Affaires", "d1", hindsight_status="MEMORIZING")
    with pytest.raises(RuntimeError, match="not_awaiting_verification"):
        queue.request_verification("Affaires", "d1")


def test_queue_adds_verification_request_column_to_existing_database(tmp_path) -> None:
    import sqlite3

    database = tmp_path / "old-queue.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("""CREATE TABLE processing_queue (
            workspace TEXT NOT NULL, document_id TEXT NOT NULL, source_path TEXT NOT NULL,
            source_sha256 TEXT NOT NULL, priority INTEGER NOT NULL,
            preflight_status TEXT NOT NULL DEFAULT 'TO_PROCESS',
            hindsight_status TEXT NOT NULL DEFAULT 'NOT_SENT', operation_id TEXT, error TEXT,
            revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL,
            PRIMARY KEY(workspace, document_id))""")
    ProcessingQueue(database)
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(processing_queue)")}
    assert "verification_requested_at" in columns


def test_archived_items_leave_active_and_error_views_and_reappear_in_place(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/a.pdf", source_sha256="sha1"
    )
    queue.upsert_candidate(
        workspace="Bibliotheque", document_id="d2", source_path="B/b.pdf", source_sha256="sha2"
    )
    original = queue.list_items()["items"][0]
    queue.set_status("Affaires", "d1", hindsight_status="ARCHIVED")

    visible = queue.list_items()
    assert [item["document_id"] for item in visible["items"]] == ["d2"]
    with pytest.raises(ValueError, match="every active queue item"):
        queue.reorder([("Bibliotheque", "d2"), ("Affaires", "d1")])

    restored = queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="A/a.pdf", source_sha256="sha1"
    )
    assert restored["priority"] == original["priority"]
    assert restored["hindsight_status"] == "MODIFIED"
    assert restored["preflight_status"] == "STABILIZING"


def test_manual_ocr_request_is_limited_to_pdf_extraction_failures(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="scan", source_path="scan.pdf", source_sha256="h1"
    )
    queue.set_status("Affaires", "scan", hindsight_status="FAILED", error="No content extracted")
    request_time = queue.request_ocr("Affaires", "scan")
    row = queue.get_item("Affaires", "scan")
    assert row["ocr_status"] == "QUEUED"
    assert row["hindsight_status"] == "OCR_QUEUED"
    assert row["ocr_requested_at"] == request_time
    assert queue.ocr_requests()[0]["document_id"] == "scan"

    queue.upsert_candidate(
        workspace="Affaires", document_id="other", source_path="other.pdf", source_sha256="h2"
    )
    queue.set_status("Affaires", "other", hindsight_status="FAILED", error="Connection refused")
    with pytest.raises(RuntimeError, match="not_ocr_retryable"):
        queue.request_ocr("Affaires", "other")


def test_exclusion_is_visible_reversible_and_source_change_clears_it(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="drawing.pdf", source_sha256="h1"
    )
    queue.do_not_memorize("Affaires", "d1")
    row = queue.list_items()["items"][0]
    assert row["hindsight_status"] == "NOT_MEMORIZED"
    assert row["user_decision"] == "DO_NOT_SEND"

    queue.reinclude("Affaires", "d1")
    row = queue.get_item("Affaires", "d1")
    assert row["hindsight_status"] == "NOT_SENT"
    assert row["user_decision"] == "AUTO"

    queue.do_not_memorize("Affaires", "d1")
    changed = queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="drawing.pdf", source_sha256="h2"
    )
    assert changed["user_decision"] == "AUTO"
    assert changed["hindsight_status"] == "MODIFIED"


def test_exclusion_cannot_interrupt_running_ocr(tmp_path) -> None:
    queue = ProcessingQueue(tmp_path / "queue.sqlite3")
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="scan.pdf", source_sha256="h1"
    )
    queue.set_status("Affaires", "d1", hindsight_status="FAILED", error="No content extracted")
    queue.request_ocr("Affaires", "d1")
    queue.set_ocr_status("Affaires", "d1", status="PROCESSING", queue_status="OCR_PROCESSING")
    with pytest.raises(RuntimeError, match="not_excludable"):
        queue.do_not_memorize("Affaires", "d1")


def test_interrupted_ocr_is_requeued_after_restart(tmp_path) -> None:
    database = tmp_path / "queue.sqlite3"
    queue = ProcessingQueue(database)
    queue.upsert_candidate(
        workspace="Affaires", document_id="d1", source_path="scan.pdf", source_sha256="h1"
    )
    queue.set_status("Affaires", "d1", hindsight_status="FAILED", error="No content extracted")
    queue.request_ocr("Affaires", "d1")
    queue.set_ocr_status("Affaires", "d1", status="PROCESSING", queue_status="OCR_PROCESSING")

    restarted = ProcessingQueue(database)
    restarted.recover_interrupted_ocr()

    row = restarted.get_item("Affaires", "d1")
    assert row["ocr_status"] == "QUEUED"
    assert row["hindsight_status"] == "OCR_QUEUED"
    assert restarted.ocr_requests()[0]["document_id"] == "d1"


def test_coordinator_lock_allows_only_one_owner(tmp_path) -> None:
    path = tmp_path / "queue.coordinator.lock"
    first = CoordinatorLock(path)
    second = CoordinatorLock(path)
    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="another producer coordinator"):
            second.acquire()
    finally:
        first.release()
    second.acquire()
    second.release()
