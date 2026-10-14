from __future__ import annotations

import threading
import uuid

import pytest

from mvp_vertical import (
    agency_claims,
    agency_data,
    execution_results,
    project_claim_candidates,
)


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


def _prepare_candidate(conn) -> tuple[str, str, str, str]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("F")[:24],
        display_name="Concurrent candidate Claim",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={},
    )
    information_id = _id("information")
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, summary, details,
            status, limits, type_tags, subject_tags, author, acted_at
        ) VALUES (
            %s, %s, %s, 'Cost synthesis', 'cost_synthesis',
            'native', 'Concurrency fixture', 'A01', 'Budget', 'Acted source.',
            'acted', '[]'::jsonb, '[]'::jsonb, '[]'::jsonb,
            'human:test', clock_timestamp()
        )
        """,
        (information_id, _id("series"), project["project_id"]),
    )
    conn.commit()

    execution_id = _id("execution")
    result_id = _id("result")
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract.project-claim",
            "project_ref": project["project_id"],
            "producer": {
                "capability": "extract_project_claim",
                "implementation": "hermes.skill.project-claim",
                "version": "1.0.0",
            },
            "produced_at": "2026-08-06T16:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "project_claim_candidate",
                    "schema_ref": "schemas/project_claim_candidate.schema.yaml",
                    "payload": {
                        "project_ref": project["project_id"],
                        "claim_type": "budget",
                        "proposed_value": 375000,
                        "unit": "EUR",
                        "certainty": "E2",
                        "observed_at": "2026-08-06T16:00:00+00:00",
                        "basis_refs": [
                            {
                                "entity_type": "information",
                                "entity_id": information_id,
                                "observed_revision": 1,
                                "observed_status": "acted",
                            }
                        ],
                        "rationale": "Budget extracted from an acted synthesis.",
                        "limitations": ["Market award not checked."],
                        "authority": {
                            "creates_project_claim": False,
                            "adopts_project_truth": False,
                            "admits_evidence": False,
                            "creates_decision": False,
                            "creates_work_issue": False,
                            "authorizes_effect": False,
                        },
                    },
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )
    execution_results.append_review_disposition(
        conn,
        result_ref=result_id,
        disposition="accepted_for_claim",
        reviewer="human:reviewer",
        reviewer_kind="human",
        note="Accepted for a separate Claim.",
        idempotency_key=_id("claim-review"),
    )
    return project["project_id"], execution_id, result_id, information_id


def _open_connections(count: int):
    connections = []
    try:
        for _ in range(count):
            connections.append(agency_data.connect())
    except Exception as exc:  # pragma: no cover - unit-only environment
        for conn in connections:
            conn.close()
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    for conn in connections:
        execution_results.ensure_schema(conn)
        conn.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
    return connections


def _truncate(setup) -> None:
    setup.execute(
        "TRUNCATE agency_project_claims, execution_result_review_dispositions, "
        "execution_clarification_requests, execution_result_items, execution_results, "
        "agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_information_cards, agency_projects "
        "RESTART IDENTITY CASCADE"
    )
    setup.commit()


def test_concurrent_creation_returns_one_append_only_claim(monkeypatch) -> None:
    connections = _open_connections(3)
    setup, first_conn, second_conn = connections
    try:
        _truncate(setup)
        project_id, execution_id, result_id, information_id = _prepare_candidate(setup)

        original_load = project_claim_candidates._load_candidate
        first_has_lock = threading.Event()
        release_first = threading.Event()
        second_started = threading.Event()
        second_finished = threading.Event()
        claims: list[dict] = []
        errors: list[BaseException] = []

        def delayed_load(conn, *, execution_id: str, result_id: str):
            loaded = original_load(conn, execution_id=execution_id, result_id=result_id)
            if threading.current_thread().name == "claim-first":
                first_has_lock.set()
                if not release_first.wait(5):
                    raise AssertionError("concurrency test did not release the first transaction")
            return loaded

        monkeypatch.setattr(project_claim_candidates, "_load_candidate", delayed_load)

        def create(conn, *, second: bool) -> None:
            try:
                if second:
                    second_started.set()
                claims.append(
                    project_claim_candidates.create_claim_from_candidate(
                        conn,
                        execution_id=execution_id,
                        result_id=result_id,
                        actor="human:ifan",
                        status="source_backed",
                        backing_ref={
                            "entity_type": "information",
                            "entity_id": information_id,
                        },
                    )
                )
            except BaseException as exc:  # captured for assertion in the parent thread
                errors.append(exc)
            finally:
                if second:
                    second_finished.set()

        first = threading.Thread(
            target=create,
            kwargs={"conn": first_conn, "second": False},
            name="claim-first",
        )
        second = threading.Thread(
            target=create,
            kwargs={"conn": second_conn, "second": True},
            name="claim-second",
        )

        first.start()
        assert first_has_lock.wait(5), "first creation never acquired the candidate row lock"
        second.start()
        assert second_started.wait(5)
        assert not second_finished.wait(0.2), "second creation bypassed the candidate row lock"
        release_first.set()

        first.join(5)
        second.join(5)
        assert not first.is_alive() and not second.is_alive()
        assert errors == []
        assert len(claims) == 2
        assert claims[0]["claim_id"] == claims[1]["claim_id"]
        assert len(agency_claims.list_project_claims(setup, project_id)) == 1
    finally:
        for conn in connections:
            conn.close()


def test_review_insertion_is_ordered_after_inflight_claim_creation(monkeypatch) -> None:
    connections = _open_connections(3)
    setup, claim_conn, review_conn = connections
    try:
        _truncate(setup)
        project_id, execution_id, result_id, information_id = _prepare_candidate(setup)

        original_load = project_claim_candidates._load_candidate
        claim_has_lock = threading.Event()
        release_claim = threading.Event()
        review_started = threading.Event()
        review_finished = threading.Event()
        claims: list[dict] = []
        reviews: list[dict] = []
        errors: list[BaseException] = []

        def delayed_load(conn, *, execution_id: str, result_id: str):
            loaded = original_load(conn, execution_id=execution_id, result_id=result_id)
            if threading.current_thread().name == "claim-create":
                claim_has_lock.set()
                if not release_claim.wait(5):
                    raise AssertionError("review-order test did not release the Claim transaction")
            return loaded

        monkeypatch.setattr(project_claim_candidates, "_load_candidate", delayed_load)

        def create_claim() -> None:
            try:
                claims.append(
                    project_claim_candidates.create_claim_from_candidate(
                        claim_conn,
                        execution_id=execution_id,
                        result_id=result_id,
                        actor="human:ifan",
                        status="source_backed",
                        backing_ref={
                            "entity_type": "information",
                            "entity_id": information_id,
                        },
                    )
                )
            except BaseException as exc:
                errors.append(exc)

        def reject_after_claim() -> None:
            try:
                review_started.set()
                reviews.append(
                    execution_results.append_review_disposition(
                        review_conn,
                        result_ref=result_id,
                        disposition="rejected",
                        reviewer="human:reviewer",
                        reviewer_kind="human",
                        note="Review committed after Claim creation.",
                        idempotency_key=_id("claim-rejection"),
                    )
                )
            except BaseException as exc:
                errors.append(exc)
            finally:
                review_finished.set()

        claim_thread = threading.Thread(target=create_claim, name="claim-create")
        review_thread = threading.Thread(target=reject_after_claim, name="claim-review")

        claim_thread.start()
        assert claim_has_lock.wait(5), "Claim creation never acquired the candidate row lock"
        review_thread.start()
        assert review_started.wait(5)
        assert not review_finished.wait(0.2), "review bypassed the candidate row lock"
        release_claim.set()

        claim_thread.join(5)
        review_thread.join(5)
        assert not claim_thread.is_alive() and not review_thread.is_alive()
        assert errors == []
        assert len(claims) == 1
        assert len(reviews) == 1
        assert len(agency_claims.list_project_claims(setup, project_id)) == 1

        history = execution_results.get_execution_result(setup, execution_id)[
            "review_dispositions"
        ]
        assert history[-1]["disposition"] == "rejected"
        assert claims[0]["provenance"]["candidate_ref"]["review_disposition_id"] == next(
            item["disposition_id"]
            for item in history
            if item["disposition"] == "accepted_for_claim"
        )
    finally:
        for conn in connections:
            conn.close()


def test_rejection_committed_before_claim_creation_blocks_adoption() -> None:
    connections = _open_connections(3)
    setup, review_conn, claim_conn = connections
    try:
        _truncate(setup)
        project_id, execution_id, result_id, information_id = _prepare_candidate(setup)

        review_has_lock = threading.Event()
        release_review = threading.Event()
        claim_started = threading.Event()
        claim_finished = threading.Event()
        errors: list[BaseException] = []

        disposition_id = _id("disposition")
        idempotency_key = _id("claim-rejection-before-adoption")

        def hold_rejection() -> None:
            try:
                with review_conn.transaction():
                    with review_conn.cursor() as cur:
                        cur.execute(
                            "SELECT execution_result_id FROM execution_result_items "
                            "WHERE result_id = %s FOR UPDATE",
                            (result_id,),
                        )
                        assert cur.fetchone() is not None
                        cur.execute(
                            """
                            INSERT INTO execution_result_review_dispositions (
                                disposition_id, result_ref, disposition, reviewer,
                                reviewer_kind, note, idempotency_key, payload_digest
                            ) VALUES (%s, %s, 'rejected', 'human:reviewer', 'human', %s, %s, %s)
                            """,
                            (
                                disposition_id,
                                result_id,
                                "Rejected before Claim creation.",
                                idempotency_key,
                                "0" * 64,
                            ),
                        )
                        review_has_lock.set()
                        if not release_review.wait(5):
                            raise AssertionError("claim-order test did not release the review")
            except BaseException as exc:
                errors.append(exc)

        def create_after_rejection() -> None:
            try:
                claim_started.set()
                project_claim_candidates.create_claim_from_candidate(
                    claim_conn,
                    execution_id=execution_id,
                    result_id=result_id,
                    actor="human:ifan",
                    status="source_backed",
                    backing_ref={
                        "entity_type": "information",
                        "entity_id": information_id,
                    },
                )
            except BaseException as exc:
                errors.append(exc)
            finally:
                claim_finished.set()

        review_thread = threading.Thread(target=hold_rejection, name="claim-review-first")
        claim_thread = threading.Thread(target=create_after_rejection, name="claim-create-second")

        review_thread.start()
        assert review_has_lock.wait(5), "rejection never acquired the candidate row lock"
        claim_thread.start()
        assert claim_started.wait(5)
        assert not claim_finished.wait(0.2), "Claim creation bypassed the review row lock"
        release_review.set()

        review_thread.join(5)
        claim_thread.join(5)
        assert not review_thread.is_alive() and not claim_thread.is_alive()

        claim_errors = [
            exc for exc in errors if isinstance(exc, project_claim_candidates.ProjectClaimCandidateError)
        ]
        unexpected = [exc for exc in errors if exc not in claim_errors]
        assert unexpected == []
        assert len(claim_errors) == 1
        assert "latest ProjectClaim candidate disposition is not accepted_for_claim" in str(
            claim_errors[0]
        )
        assert agency_claims.list_project_claims(setup, project_id) == []

        history = execution_results.get_execution_result(setup, execution_id)[
            "review_dispositions"
        ]
        assert history[-1]["disposition_id"] == disposition_id
        assert history[-1]["disposition"] == "rejected"
    finally:
        for conn in connections:
            conn.close()
