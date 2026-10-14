"""The chokepoint on the Knowledge writes that needed it, and the local fix
for the one that did not.

Three findings, three different repairs:

- `publish_knowledge` lets a caller assert `review_status="reviewed"` with
  nothing behind the claim. Gated, but only for that one claim — candidate
  publication makes no professional claim and needs no decision point.
- `complete_edit_request` had no status guard at all, so a request a human
  had rejected could be silently returned to `proposed` by Hermes filling in
  a new proposal. That is a missing local check, not a missing decision
  point, and is fixed as one.
- `apply_edit_request` is where the Knowledge Markdown actually changes.
  Gated unconditionally: nothing upstream of it has to decide anything for a
  request to arrive `proposed`.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from mvp_vertical import execution_results, knowledge, knowledge_edit_variants, store
from mvp_vertical.contract import TaskContract
from mvp_vertical.policy_gate import StandInPolicyClient


class _UnreachablePolicyClient:
    def preflight(self, candidate):
        raise RuntimeError("decision point unreachable")

    def validate_decision(self, payload):  # pragma: no cover - never reached
        raise AssertionError("validation must not be attempted after a failed preflight")


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only lane
        pytest.skip(f"PostgreSQL/pgvector unreachable: {exc}")
    # The rejected-request test below calls knowledge_edit_variants.reject_request
    # directly, which is the only path in this module that touches its tables;
    # nothing else in this file provisions them.
    execution_results.ensure_schema(connection)
    knowledge_edit_variants.ensure_schema(connection)
    yield connection
    connection.close()


def _source(conn, tmp_path: Path) -> tuple[str, list[str]]:
    suffix = uuid.uuid4().hex
    dossier = f"gate-{suffix}"
    source_ref = f"Projects/GATE-A/30_DCE/GATE-A_A1_DCE_ARC_CCTP_LOT-06-{suffix}_2026-09-02.md"
    path = tmp_path / source_ref
    path.parent.mkdir(parents=True)
    path.write_text("# Façades\n\nLes reprises concernent le support existant.", encoding="utf-8")
    raw = {
        "object_type": "task_contract",
        "object_id": f"tc.{suffix}",
        "contract_id": f"tc.{suffix}",
        "scope": {
            "dossier": dossier,
            "parent_project_id": "project-gate-a",
            "declared_sources": [{"source_ref": source_ref}],
        },
    }
    contract = TaskContract(
        raw=raw, path=tmp_path / "task_contract.yaml", dossier=dossier, sources=(source_ref,)
    )
    assert store.ingest(conn, contract, tmp_path, ingestion_id=f"ingest-{suffix}") == 1
    card = store.get_document_card(conn, dossier, source_ref)
    compilation_id = card["structured_extraction"]["compilation_id"]
    return card["document_id"], [f"chunk.{compilation_id}.0000"]


def _publish(conn, tmp_path: Path, **overrides) -> dict:
    document_id, refs = _source(conn, tmp_path)
    knowledge_id = f"knowledge.techniques.{uuid.uuid4().hex}"
    kwargs = dict(
        knowledge_id=knowledge_id,
        document_id=document_id,
        title="Reprise des façades existantes",
        family="techniques",
        markdown="# Reprise des façades\n\nPréparer le support existant.",
        source_chunk_refs=refs,
        created_by="hermes-test",
        actor_kind="hermes",
        idempotency_key=f"publish-{uuid.uuid4().hex}",
    )
    kwargs.update(overrides)
    return knowledge.publish_knowledge(conn, **kwargs)


def _edit_request(conn, knowledge_id: str) -> dict:
    markdown = knowledge.get_knowledge_markdown(conn, knowledge_id)
    selected = "Préparer le support existant."
    start = markdown.index(selected)
    return knowledge.create_edit_request(
        conn,
        request_id=f"edit-{uuid.uuid4().hex}",
        knowledge_id=knowledge_id,
        instruction_kind="expand",
        instruction="Détailler la préparation du support.",
        base_version=1,
        selection_start=start,
        selection_end=start + len(selected),
        selected_text=selected,
        requested_by="mobile-user",
        idempotency_key=f"request-{uuid.uuid4().hex}",
    )


def _canonical_decision(
    *,
    decision_id: str,
    decided_by: str,
    scope: dict[str, str],
    object_identity: str,
    content_digest: str,
    approval_level: str = "C2",
) -> dict:
    return {
        "decision": {
            "decision_id": decision_id,
            "decided_by": decided_by,
            "approval_level": approval_level,
            "scope": scope,
            "object_identity": object_identity,
            "content_digest": content_digest,
            "expires_at": "2099-01-01T00:00:00Z",
            "signature": "signed-canonical-decision",
        }
    }


def _reviewed_publication_decision(
    *,
    decision_id: str,
    knowledge_id: str,
    document_id: str,
    title: str,
    markdown: str,
    source_chunk_refs: list[str],
    created_by: str = "human:architect",
    actor_kind: str = "human",
) -> dict:
    payload_digest = knowledge._payload_digest(
        {
            "knowledge_id": knowledge_id,
            "document_id": document_id,
            "title": title,
            "family": "techniques",
            "markdown": markdown,
            "source_chunk_refs": source_chunk_refs,
            "created_by": created_by,
            "actor_kind": actor_kind,
            "review_status": "reviewed",
            "expected_version": 0,
        }
    )
    return _canonical_decision(
        decision_id=decision_id,
        decided_by=created_by,
        scope={"scope_type": "project", "scope_id": "project-gate-a"},
        object_identity=f"knowledge_item:{knowledge_id}",
        content_digest=payload_digest,
    )


def _apply_decision(conn, *, request_id: str, decision_id: str, actor: str = "human:architect") -> dict:
    request = knowledge.get_edit_request(conn, request_id)
    apply_digest = knowledge._payload_digest(
        {
            "request_id": request_id,
            "knowledge_id": request["knowledge_id"],
            "base_version": request["base_version"],
            "selected_text_digest": request["selected_text_digest"],
            "replacement_markdown": request["replacement_markdown"],
        }
    )
    return _canonical_decision(
        decision_id=decision_id,
        decided_by=actor,
        scope={"scope_type": "project", "scope_id": "project-gate-a"},
        object_identity=f"knowledge_edit_request:{request_id}",
        content_digest=apply_digest,
    )


# --- publish_knowledge --------------------------------------------------------


def test_candidate_publication_needs_no_decision_point(conn, tmp_path) -> None:
    """generated_unreviewed, needs_review and superseded assert nothing to gate."""
    card = _publish(conn, tmp_path, review_status="needs_review")
    assert card["review_status"] == "needs_review"


def test_publishing_as_reviewed_is_refused_without_a_decision_point(conn, tmp_path) -> None:
    document_id, refs = _source(conn, tmp_path)
    with pytest.raises(knowledge.KnowledgeGateRefused, match="decision_payload.decision"):
        knowledge.publish_knowledge(
            conn,
            knowledge_id=f"knowledge.techniques.{uuid.uuid4().hex}",
            document_id=document_id,
            title="Reprise des façades existantes",
            family="techniques",
            markdown="# Reprise\n\nContenu.",
            source_chunk_refs=refs,
            created_by="human:architect",
            actor_kind="human",
            idempotency_key=f"publish-{uuid.uuid4().hex}",
            review_status="reviewed",
            policy_client=StandInPolicyClient(),
            # no decision_payload: nothing to bind the claim to
        )


def test_publishing_as_reviewed_carries_the_publication_digest_to_the_decision_point(
    conn, tmp_path
) -> None:
    document_id, refs = _source(conn, tmp_path)
    knowledge_id = f"knowledge.techniques.{uuid.uuid4().hex}"
    client = StandInPolicyClient()

    card = knowledge.publish_knowledge(
        conn,
        knowledge_id=knowledge_id,
        document_id=document_id,
        title="Reprise des façades existantes",
        family="techniques",
        markdown="# Reprise\n\nContenu.",
        source_chunk_refs=refs,
        created_by="human:architect",
        actor_kind="human",
        idempotency_key=f"publish-{uuid.uuid4().hex}",
        review_status="reviewed",
        policy_client=client,
        decision_payload=_reviewed_publication_decision(
            decision_id="decision-1",
            knowledge_id=knowledge_id,
            document_id=document_id,
            title="Reprise des façades existantes",
            markdown="# Reprise\n\nContenu.",
            source_chunk_refs=refs,
        ),
    )
    assert card["review_status"] == "reviewed"

    expectation = client.last_decision["expectation"]
    assert expectation["object_identity"] == f"knowledge_item:{knowledge_id}"
    assert expectation["required_scope"] == {
        "scope_type": "project",
        "scope_id": "project-gate-a",
    }
    request = client.last_preflight["request"]
    assert request["external_effect"] is False
    assert request["writes_state"] is True


def test_a_refused_reviewed_publication_writes_no_knowledge_item(conn, tmp_path) -> None:
    document_id, refs = _source(conn, tmp_path)
    knowledge_id = f"knowledge.techniques.{uuid.uuid4().hex}"
    client = StandInPolicyClient(disposition="blocked_missing_task_contract")

    with pytest.raises(knowledge.KnowledgeGateRefused):
        knowledge.publish_knowledge(
            conn,
            knowledge_id=knowledge_id,
            document_id=document_id,
            title="Reprise",
            family="techniques",
            markdown="# Reprise\n\nContenu.",
            source_chunk_refs=refs,
            created_by="human:architect",
            actor_kind="human",
            idempotency_key=f"publish-{uuid.uuid4().hex}",
            review_status="reviewed",
            policy_client=client,
            decision_payload=_reviewed_publication_decision(
                decision_id="decision-2",
                knowledge_id=knowledge_id,
                document_id=document_id,
                title="Reprise",
                markdown="# Reprise\\n\\nContenu.",
                source_chunk_refs=refs,
            ),
        )
    with pytest.raises(knowledge.KnowledgeNotFound):
        knowledge.get_knowledge_card(conn, knowledge_id)


# --- complete_edit_request: local fix, no chokepoint involved ----------------


def test_a_rejected_request_cannot_be_un_rejected_through_complete(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    knowledge_edit_variants.reject_request(
        conn,
        request_id=request["request_id"],
        actor="human:reviewer",
        reason="Non retenue.",
        idempotency_key=f"reject-{uuid.uuid4().hex}",
    )
    rejected = knowledge.get_edit_request(conn, request["request_id"])
    assert rejected["status"] == "rejected"

    with pytest.raises(knowledge.KnowledgeError, match="not awaiting a Hermes proposal"):
        knowledge.complete_edit_request(
            conn,
            request_id=request["request_id"],
            replacement_markdown="Un remplacement qui ne devrait jamais être accepté.",
        )
    still_rejected = knowledge.get_edit_request(conn, request["request_id"])
    assert still_rejected["status"] == "rejected", "the rejection must survive the retry"


def test_completing_a_queued_request_still_works(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    proposal = knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    assert proposal["status"] == "proposed"


def test_completing_the_same_proposal_twice_is_idempotent(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    first = knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    second = knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    assert first == second


# --- apply_edit_request -------------------------------------------------------


def test_apply_is_refused_without_a_decision_point(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    with pytest.raises(knowledge.KnowledgeGateRefused, match="decision_payload.decision"):
        knowledge.apply_edit_request(
            conn,
            request_id=request["request_id"],
            actor="human:architect",
            actor_kind="human",
            idempotency_key=f"apply-{uuid.uuid4().hex}",
            policy_client=StandInPolicyClient(),
        )


def test_an_allowed_apply_carries_the_replacement_digest_to_the_decision_point(
    conn, tmp_path
) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    client = StandInPolicyClient()

    applied = knowledge.apply_edit_request(
        conn,
        request_id=request["request_id"],
        actor="human:architect",
        actor_kind="human",
        idempotency_key=f"apply-{uuid.uuid4().hex}",
        policy_client=client,
        decision_payload=_apply_decision(
            conn, request_id=request["request_id"], decision_id="decision-3"
        ),
    )
    assert applied["knowledge"]["version"] == 2

    expectation = client.last_decision["expectation"]
    assert expectation["object_identity"] == f"knowledge_edit_request:{request['request_id']}"
    assert expectation["required_scope"] == {
        "scope_type": "project",
        "scope_id": "project-gate-a",
    }


def test_a_refused_apply_leaves_the_request_proposed_and_retryable(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    client = StandInPolicyClient(disposition="blocked_missing_task_contract")

    with pytest.raises(knowledge.KnowledgeGateRefused):
        knowledge.apply_edit_request(
            conn,
            request_id=request["request_id"],
            actor="human:architect",
            actor_kind="human",
            idempotency_key=f"apply-{uuid.uuid4().hex}",
            policy_client=client,
            decision_payload=_apply_decision(
            conn, request_id=request["request_id"], decision_id="decision-4"
        ),
        )
    still_proposed = knowledge.get_edit_request(conn, request["request_id"])
    assert still_proposed["status"] == "proposed", (
        "a refusal is not the same as staleness; the request must remain "
        "retryable once a real decision exists"
    )
    unchanged = knowledge.get_knowledge_card(conn, card["knowledge_id"])
    assert unchanged["version"] == 1


def test_an_unreachable_decision_point_fails_closed(conn, tmp_path) -> None:
    card = _publish(conn, tmp_path)
    request = _edit_request(conn, card["knowledge_id"])
    knowledge.complete_edit_request(
        conn, request_id=request["request_id"], replacement_markdown="Remplacement."
    )
    with pytest.raises(knowledge.KnowledgeGatePolicyUnavailable):
        knowledge.apply_edit_request(
            conn,
            request_id=request["request_id"],
            actor="human:architect",
            actor_kind="human",
            idempotency_key=f"apply-{uuid.uuid4().hex}",
            policy_client=_UnreachablePolicyClient(),
            decision_payload=_apply_decision(
            conn, request_id=request["request_id"], decision_id="decision-5"
        ),
        )
    unchanged = knowledge.get_knowledge_card(conn, card["knowledge_id"])
    assert unchanged["version"] == 1


# --- _gate_knowledge_write in isolation: no database needed ------------------


def test_gate_knowledge_write_requires_a_decision_id() -> None:
    with pytest.raises(knowledge.KnowledgeGateRefused, match="decision_payload.decision"):
        knowledge._gate_knowledge_write(
            StandInPolicyClient(),
            intent="publish_knowledge_reviewed",
            scope={"scope_type": "project", "scope_id": "p-1"},
            object_ref="knowledge_item:k-1",
            expected_digest="digest-1",
            decision_payload=None,
            actor="human:architect",
            required_ceiling="C2",
        )


def test_gate_knowledge_write_allows_a_bound_decision() -> None:
    client = StandInPolicyClient()
    knowledge._gate_knowledge_write(
        client,
        intent="publish_knowledge_reviewed",
        scope={"scope_type": "project", "scope_id": "p-1"},
        object_ref="knowledge_item:k-1",
        expected_digest="digest-1",
        decision_payload=_canonical_decision(
            decision_id="decision-1",
            decided_by="human:architect",
            scope={"scope_type": "project", "scope_id": "p-1"},
            object_identity="knowledge_item:k-1",
            content_digest="digest-1",
        ),
        actor="human:architect",
        required_ceiling="C2",
    )
    assert client.last_decision["expectation"]["expected_digest"] == "digest-1"
    assert client.last_decision["expectation"]["object_identity"] == "knowledge_item:k-1"


def test_gate_knowledge_write_refuses_a_non_human_decider() -> None:
    with pytest.raises(knowledge.KnowledgeGateRefused):
        knowledge._gate_knowledge_write(
            StandInPolicyClient(),
            intent="publish_knowledge_reviewed",
            scope={"scope_type": "project", "scope_id": "p-1"},
            object_ref="knowledge_item:k-1",
            expected_digest="digest-1",
            decision_payload=_canonical_decision(
            decision_id="decision-1",
            decided_by="hermes:profile",
            scope={"scope_type": "project", "scope_id": "p-1"},
            object_identity="knowledge_item:k-1",
            content_digest="digest-1",
        ),
            actor="hermes:profile",
            required_ceiling="C2",
        )
