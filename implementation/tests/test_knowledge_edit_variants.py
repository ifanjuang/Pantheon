from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import pytest

from mvp_vertical import execution_results, knowledge, knowledge_edit_variants, store
from mvp_vertical.contract import TaskContract


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _sha256(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL/pgvector unreachable: {exc}")
    execution_results.ensure_schema(connection)
    knowledge_edit_variants.ensure_schema(connection)
    yield connection
    connection.close()


def _publish(conn, tmp_path: Path) -> dict:
    suffix = uuid.uuid4().hex
    dossier = f"variant-{suffix}"
    source_ref = (
        "Projects/MAISON-A/30_DCE/"
        f"MAISON-A_A1_DCE_ARC_CCTP_LOT-06-{suffix}_2026-08-05.md"
    )
    path = tmp_path / source_ref
    path.parent.mkdir(parents=True)
    path.write_text("# Façades\n\nPréparer le support existant.", encoding="utf-8")
    raw = {
        "object_type": "task_contract",
        "object_id": f"tc.{suffix}",
        "contract_id": f"tc.{suffix}",
        "scope": {
            "dossier": dossier,
            "parent_project_id": "project-maison-a",
            "declared_sources": [{"source_ref": source_ref}],
        },
    }
    contract = TaskContract(
        raw=raw,
        path=tmp_path / "task_contract.yaml",
        dossier=dossier,
        sources=(source_ref,),
    )
    assert store.ingest(conn, contract, tmp_path, ingestion_id=f"ingest-{suffix}") == 1
    document = store.get_document_card(conn, dossier, source_ref)
    compilation_id = document["structured_extraction"]["compilation_id"]
    # Document-card lookup and Knowledge publication are separate requests in
    # production; end the read transaction before the write owner begins.
    conn.rollback()
    return knowledge.publish_knowledge(
        conn,
        knowledge_id=f"knowledge.techniques.{suffix}",
        document_id=document["document_id"],
        title="Reprise des façades",
        family="techniques",
        markdown="# Reprise des façades\n\nPréparer le support existant.",
        source_chunk_refs=[f"chunk.{compilation_id}.0000"],
        created_by="hermes-test",
        actor_kind="hermes",
        idempotency_key=_id("publish"),
    )


def _request(conn, card: dict, *, count: int = 2) -> dict:
    markdown = knowledge.get_knowledge_markdown(conn, card["knowledge_id"])
    selected = "Préparer le support existant."
    start = markdown.index(selected)
    # The editor request starts on a fresh API connection in production.
    conn.rollback()
    return knowledge_edit_variants.create_variant_request(
        conn,
        request_id=_id("edit"),
        knowledge_id=card["knowledge_id"],
        instruction_kind="rewrite",
        instruction="Proposer des formulations alternatives.",
        base_version=card["version"],
        selection_start=start,
        selection_end=start + len(selected),
        selected_text=selected,
        requested_by="architecte",
        requested_variant_count=count,
        idempotency_key=_id("request"),
    )


def _store_variant_result(
    conn,
    review: dict,
    *,
    label: str,
    replacement: str,
    scope_digest: str | None = None,
    authority: dict | None = None,
    extra_payload: dict | None = None,
) -> tuple[str, str]:
    request = review["edit_request"]
    execution_result_id = _id("execution-result")
    result_ref = _id("knowledge-variant")
    payload = {
        "candidate_kind": "knowledge_edit_variant",
        "request_ref": request["request_id"],
        "request_scope_digest": scope_digest or request["request_scope_digest"],
        "knowledge_ref": request["knowledge_id"],
        "base_version": request["base_version"],
        "selection_start": request["selection_start"],
        "selection_end": request["selection_end"],
        "selected_text_digest": f"sha256:{request['selected_text_digest']}",
        "variant_label": label,
        "replacement_markdown": replacement,
        "replacement_digest": _sha256(replacement),
        "rationale": f"Alternative {label}",
        "source_refs": ["source-email-2026-08-05"],
        "limitations": ["Candidate non validé professionnellement."],
        "authority": authority or dict(knowledge_edit_variants.CANDIDATE_AUTHORITY),
    }
    payload.update(extra_payload or {})
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_result_id,
            "task_contract_ref": "task-contract-knowledge-edit",
            "project_ref": "project-maison-a",
            "producer": {
                "capability": "knowledge_edit",
                "implementation": "hermes-agent",
                "version": "0.20.0",
            },
            "produced_at": datetime.now(timezone.utc).isoformat(),
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_ref,
                    "result_kind": "knowledge_edit_variant",
                    "schema_ref": knowledge_edit_variants.VARIANT_SCHEMA_REF,
                    "payload": payload,
                    "authority": dict(execution_results.AUTHORITY),
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("store-result"),
    )
    return execution_result_id, result_ref


def _project(conn, execution_result_id: str, result_ref: str, key: str | None = None) -> dict:
    return knowledge_edit_variants.project_execution_result_variant(
        conn,
        execution_result_id=execution_result_id,
        result_ref=result_ref,
        idempotency_key=key or _id("project-variant"),
    )


def test_ab_variants_share_one_scope_and_selection_does_not_apply(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=2)
    request_id = review["edit_request"]["request_id"]
    original = knowledge.get_knowledge_markdown(conn, card["knowledge_id"])
    # Production review actions use separate API connections. End the read-only
    # snapshot before the first projection so subsequent mutation owners open
    # genuine top-level transactions rather than savepoints.
    conn.rollback()

    execution_a, result_a = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Nettoyer et préparer le support existant.",
    )
    first_key = _id("project-a")
    first = _project(conn, execution_a, result_a, first_key)
    assert first["edit_request"]["status"] == "queued_for_hermes"
    assert len(first["variants"]) == 1
    assert _project(conn, execution_a, result_a, first_key)["variants"][0]["variant_label"] == "A"

    execution_b, result_b = _store_variant_result(
        conn,
        review,
        label="B",
        replacement="Purger les parties non adhérentes, dépoussiérer puis appliquer le primaire.",
    )
    proposed = _project(conn, execution_b, result_b)
    assert proposed["edit_request"]["status"] == "proposed"
    assert proposed["edit_request"]["requested_variant_count"] == 2
    assert [variant["variant_label"] for variant in proposed["variants"]] == ["A", "B"]
    assert all(variant["diff"] for variant in proposed["variants"])
    assert {variant["request_id"] for variant in proposed["variants"]} == {request_id}
    assert all(variant["source_execution_result_id"] for variant in proposed["variants"])

    variant_b = next(variant for variant in proposed["variants"] if variant["variant_label"] == "B")
    selected = knowledge_edit_variants.select_variant(
        conn,
        request_id=request_id,
        variant_id=variant_b["variant_id"],
        actor="architecte",
        idempotency_key=_id("select"),
    )
    assert selected["edit_request"]["selected_variant_id"] == variant_b["variant_id"]
    assert selected["variant_selected_is_edit_applied"] is False
    assert knowledge.get_knowledge_markdown(conn, card["knowledge_id"]) == original
    assert knowledge.get_knowledge_card(conn, card["knowledge_id"])["version"] == 1
    # Selection/review and apply are separate API requests.
    conn.rollback()

    applied = knowledge_edit_variants.apply_selected_variant(
        conn,
        request_id=request_id,
        actor="architecte",
        idempotency_key=_id("apply"),
    )
    assert applied["knowledge"]["version"] == 2
    assert applied["review"]["edit_request"]["status"] == "applied"
    assert "Purger les parties" in knowledge.get_knowledge_markdown(conn, card["knowledge_id"])

    # The review projection above starts a read transaction after the apply.
    # Rolling it back must not erase the accepted Knowledge revision or audit.
    conn.rollback()
    assert knowledge.get_knowledge_card(conn, card["knowledge_id"])["version"] == 2
    persisted_review = knowledge_edit_variants.get_variant_review(conn, request_id)
    assert persisted_review["edit_request"]["status"] == "applied"

    event_types = [event["event_type"] for event in persisted_review["review_events"]]
    assert event_types == [
        "variant_projected",
        "variant_projected",
        "variant_selected",
        "variant_applied",
    ]


def test_projection_rejects_wrong_scope_and_forbidden_authority(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=1)

    execution_id, result_ref = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Préparer méthodiquement le support.",
        scope_digest="sha256:" + "0" * 64,
    )
    with pytest.raises(knowledge_edit_variants.KnowledgeEditVariantConflict):
        _project(conn, execution_id, result_ref)

    authority = dict(knowledge_edit_variants.CANDIDATE_AUTHORITY)
    authority["applies_edit"] = True
    execution_id, result_ref = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Préparer soigneusement le support.",
        authority=authority,
    )
    with pytest.raises(knowledge_edit_variants.KnowledgeEditVariantError):
        _project(conn, execution_id, result_ref)


def test_rejection_is_non_mutating_and_records_append_only_history(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=1)
    request_id = review["edit_request"]["request_id"]
    original = knowledge.get_knowledge_markdown(conn, card["knowledge_id"])
    execution_id, result_ref = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Préparer soigneusement le support existant.",
    )
    proposed = _project(conn, execution_id, result_ref)
    rejected = knowledge_edit_variants.reject_request(
        conn,
        request_id=request_id,
        actor="architecte",
        reason="Formulation non retenue.",
        idempotency_key=_id("reject"),
    )
    assert rejected["edit_request"]["status"] == "rejected"
    assert knowledge.get_knowledge_markdown(conn, card["knowledge_id"]) == original

    event_id = proposed["review_events"][0]["event_id"]
    variant_id = proposed["variants"][0]["variant_id"]
    conn.commit()
    with pytest.raises(Exception, match="append-only"):
        conn.execute(
            "UPDATE knowledge_edit_review_events SET actor = 'x' WHERE event_id = %s",
            (event_id,),
        )
    conn.rollback()
    with pytest.raises(Exception, match="immutable candidate snapshots"):
        conn.execute(
            "UPDATE knowledge_edit_variants SET proposed_by = 'x' WHERE variant_id = %s",
            (variant_id,),
        )
    conn.rollback()


def test_selected_variant_lock_is_held_through_apply_owner(
    conn, tmp_path, monkeypatch
) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=2)
    request_id = review["edit_request"]["request_id"]

    execution_a, result_a = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Nettoyer et préparer le support existant.",
    )
    _project(conn, execution_a, result_a)
    execution_b, result_b = _store_variant_result(
        conn,
        review,
        label="B",
        replacement="Purger, dépoussiérer puis appliquer le primaire.",
    )
    proposed = _project(conn, execution_b, result_b)
    variant_b = next(
        variant for variant in proposed["variants"] if variant["variant_label"] == "B"
    )
    knowledge_edit_variants.select_variant(
        conn,
        request_id=request_id,
        variant_id=variant_b["variant_id"],
        actor="human@agency",
        idempotency_key=_id("select"),
    )

    class ApplyObserved(RuntimeError):
        pass

    def inspect_locked_apply(active, **values):
        with active.cursor() as cur:
            cur.execute(
                "SELECT selected_variant_id, replacement_markdown "
                "FROM knowledge_edit_requests WHERE request_id = %s",
                (request_id,),
            )
            selected_variant_id, replacement_markdown = cur.fetchone()
        assert selected_variant_id == variant_b["variant_id"]
        assert replacement_markdown == variant_b["replacement_markdown"]

        contender = psycopg.connect(store.dsn_from_env())
        try:
            with pytest.raises(psycopg.errors.LockNotAvailable):
                with contender.transaction():
                    contender.execute(
                        "SELECT 1 FROM knowledge_edit_requests "
                        "WHERE request_id = %s FOR UPDATE NOWAIT",
                        (request_id,),
                    )
        finally:
            contender.close()
        raise ApplyObserved

    monkeypatch.setattr(knowledge, "apply_edit_request", inspect_locked_apply)
    with pytest.raises(ApplyObserved):
        knowledge_edit_variants.apply_selected_variant(
            conn,
            request_id=request_id,
            actor="human@agency",
            idempotency_key=_id("apply"),
        )

    # The sentinel unwinds the enclosing transaction, so preparation alone
    # cannot leak a replacement into the durable request.
    stored = knowledge.get_edit_request(conn, request_id)
    assert stored["selected_variant_id"] == variant_b["variant_id"]
    assert stored["replacement_markdown"] is None


def test_apply_and_its_audit_commit_together(conn, tmp_path, monkeypatch) -> None:
    """The applied revision and its variant_applied audit are one effect.

    A failing audit write must leave the Knowledge item, the request status and
    the event log all unchanged -- not a revised item whose review history has
    no record of which variant produced it. The audit used to run in its own
    transaction after the apply had already committed, so a failure there left
    exactly that.
    """
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=1)
    request_id = review["edit_request"]["request_id"]

    execution, result = _store_variant_result(
        conn, review, label="A", replacement="Nettoyer puis préparer le support."
    )
    proposed = _project(conn, execution, result)
    knowledge_edit_variants.select_variant(
        conn,
        request_id=request_id,
        variant_id=proposed["variants"][0]["variant_id"],
        actor="human@agency",
        idempotency_key=_id("select"),
    )

    before_version = knowledge.get_knowledge_card(conn, card["knowledge_id"])["version"]
    before = knowledge_edit_variants.get_variant_review(conn, request_id)
    # Review is a separate request from apply.
    conn.rollback()

    real_insert = knowledge_edit_variants._insert_event

    def failing_insert(*args, **kwargs):
        if kwargs.get("event_type") == "variant_applied":
            raise RuntimeError("audit write failed")
        return real_insert(*args, **kwargs)

    monkeypatch.setattr(knowledge_edit_variants, "_insert_event", failing_insert)

    with pytest.raises(RuntimeError):
        knowledge_edit_variants.apply_selected_variant(
            conn,
            request_id=request_id,
            actor="human@agency",
            idempotency_key=_id("apply"),
        )

    after = knowledge_edit_variants.get_variant_review(conn, request_id)
    assert knowledge.get_knowledge_card(conn, card["knowledge_id"])["version"] == before_version
    assert after["edit_request"]["status"] == before["edit_request"]["status"]
    assert len(after["review_events"]) == len(before["review_events"])
    conn.rollback()

    monkeypatch.setattr(knowledge_edit_variants, "_insert_event", real_insert)
    applied = knowledge_edit_variants.apply_selected_variant(
        conn,
        request_id=request_id,
        actor="human@agency",
        idempotency_key=_id("apply"),
    )
    assert applied["knowledge"]["version"] == before_version + 1
    assert "variant_applied" in [e["event_type"] for e in applied["review"]["review_events"]]



def test_variant_apply_conflict_status_survives_enclosing_transaction(
    conn, tmp_path
) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=1)
    request_id = review["edit_request"]["request_id"]

    execution_id, result_ref = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Préparer soigneusement le support.",
    )
    proposed = _project(conn, execution_id, result_ref)
    knowledge_edit_variants.select_variant(
        conn,
        request_id=request_id,
        variant_id=proposed["variants"][0]["variant_id"],
        actor="human@agency",
        idempotency_key=_id("select"),
    )

    markdown = knowledge.get_knowledge_markdown(conn, card["knowledge_id"])
    conn.rollback()
    knowledge.revise_knowledge(
        conn,
        knowledge_id=card["knowledge_id"],
        markdown=markdown + "\n\nRévision concurrente.",
        expected_version=card["version"],
        actor="architecte",
        actor_kind="human",
        idempotency_key=_id("concurrent-revision"),
    )

    with pytest.raises(
        knowledge.StaleKnowledgeWrite,
        match="Knowledge changed after the intelligent edit was proposed",
    ):
        knowledge_edit_variants.apply_selected_variant(
            conn,
            request_id=request_id,
            actor="human@agency",
            idempotency_key=_id("apply"),
        )

    stored = knowledge_edit_variants.get_variant_review(conn, request_id)
    assert stored["edit_request"]["status"] == "conflict"
    assert knowledge.get_knowledge_card(conn, card["knowledge_id"])["version"] == 2


def test_projection_conflict_status_survives_inner_rollback(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=1)
    execution_id, result_ref = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Préparer soigneusement le support.",
    )
    markdown = knowledge.get_knowledge_markdown(conn, card["knowledge_id"])
    knowledge.revise_knowledge(
        conn,
        knowledge_id=card["knowledge_id"],
        markdown=markdown + "\n\nMise à jour concurrente.",
        expected_version=card["version"],
        actor="architecte",
        actor_kind="human",
        idempotency_key=_id("concurrent-revision"),
    )

    with pytest.raises(knowledge_edit_variants.KnowledgeEditVariantConflict):
        _project(conn, execution_id, result_ref)

    stored = knowledge_edit_variants.get_variant_review(
        conn, review["edit_request"]["request_id"]
    )
    assert stored["edit_request"]["status"] == "conflict"


def test_projection_rejects_unknown_candidate_fields(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    review = _request(conn, card, count=1)
    execution_id, result_ref = _store_variant_result(
        conn,
        review,
        label="A",
        replacement="Préparer soigneusement le support.",
        extra_payload={"review_status": "approved"},
    )
    with pytest.raises(
        knowledge_edit_variants.KnowledgeEditVariantError,
        match="unsupported fields",
    ):
        _project(conn, execution_id, result_ref)
