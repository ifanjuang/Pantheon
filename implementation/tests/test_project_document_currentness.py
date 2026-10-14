"""PostgreSQL acceptance for A4b bounded document currentness."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import psycopg
import pytest
import yaml

from mvp_vertical import pantheon_contracts, project_document_currentness, project_documents



@pytest.fixture
def conn():
    try:
        connection = project_document_currentness.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_version_effect_events, doc_document_version_sources, "
        "doc_document_events, doc_document_versions, doc_documents, "
        "document_versions, source_documents RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _logical_document(conn) -> dict:
    document = project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id="project-alpha",
        document_type="PLAN",
        title="Plan architectural",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("document-create"),
    )
    conn.commit()
    return document


def _revision(
    conn,
    *,
    document: dict,
    label: str,
    digest_char: str,
    supersedes: str | None = None,
) -> dict:
    technical_id = _id("source-document")
    digest = digest_char * 64
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, 'project-alpha', 'project-alpha', %s, %s,
                  'application/pdf', 1234, 'ready')
        """,
        (technical_id, f"plans/plan_{label}.pdf", digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (technical_id, f"plans/plan_{label}.pdf", digest),
    )
    conn.commit()
    revision = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=technical_id,
        source_version=1,
        revision_label=label,
        supersedes_version_id=supersedes,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("revision-link"),
    )
    conn.commit()
    return revision


def _event(
    conn,
    *,
    revision: dict,
    effect: str,
    authority: str = "internal_working_authority",
    status: str = "issued",
    event_type: str = "issued",
    actor_kind: str = "human",
) -> dict:
    result = project_document_currentness.record_version_event(
        conn,
        document_version_id=revision["version_id"],
        event_type=event_type,
        new_status=status,
        new_effect_class=effect,
        new_authority_status=authority,
        actor="reviewer" if actor_kind == "human" else actor_kind,
        actor_kind=actor_kind,
        idempotency_key=_id("version-event"),
        reason="bounded test posture",
        basis_refs=["review:test"],
    )
    conn.commit()
    return result


def test_currentness_vocabularies_use_canonical_contracts() -> None:
    version_source = pantheon_contracts.provenance("document_version_event")
    currentness_source = pantheon_contracts.provenance("document_currentness_projection")
    assert version_source["source_repository"] == "ifanjuang/Pantheon"
    assert version_source["source_path"] == "schemas/architecture-proof-register/version_event.schema.yaml"
    assert currentness_source["source_path"] == "schemas/architecture-proof-register/document_currentness_projection.schema.yaml"
    assert version_source["posture"] == "canonical-repository"
    assert currentness_source["posture"] == "canonical-repository"
    assert version_source["authority_transfer"] is False
    assert currentness_source["authority_transfer"] is False

    event_schema = pantheon_contracts.load_schema("document_version_event")
    currentness_schema = pantheon_contracts.load_schema("document_currentness_projection")
    assert set(event_schema["properties"]["event_type"]["enum"]) == project_document_currentness.EVENT_TYPES
    assert set(event_schema["$defs"]["effect_class"]["enum"]) == project_document_currentness.EFFECT_CLASSES
    assert set(event_schema["$defs"]["authority_status"]["enum"]) == project_document_currentness.AUTHORITY_STATUSES
    assert set(currentness_schema["properties"]["purpose"]["enum"]) == project_document_currentness.PURPOSES


def test_event_history_is_ordered_idempotent_and_append_only(conn) -> None:
    document = _logical_document(conn)
    revision = _revision(conn, document=document, label="A", digest_char="a")
    key = _id("event")
    first = project_document_currentness.record_version_event(
        conn,
        document_version_id=revision["version_id"],
        event_type="created",
        new_status="draft",
        new_effect_class="working_revision",
        new_authority_status="internal_working_authority",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=key,
        reason="first reviewed working posture",
    )
    replay = project_document_currentness.record_version_event(
        conn,
        document_version_id=revision["version_id"],
        event_type="created",
        new_status="draft",
        new_effect_class="working_revision",
        new_authority_status="internal_working_authority",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=key,
        reason="first reviewed working posture",
    )
    assert replay == first
    second = project_document_currentness.record_version_event(
        conn,
        document_version_id=revision["version_id"],
        event_type="issued",
        new_status="issued",
        new_effect_class="coordination_update",
        new_authority_status="internal_review_authority",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("event-2"),
        reason="coordination issue",
    )
    conn.commit()

    assert first["event_seq"] == 1
    assert second["event_seq"] == 2
    assert second["previous_status"] == "draft"
    assert second["previous_effect_class"] == "working_revision"
    assert second["previous_authority_status"] == "internal_working_authority"
    assert [row["event_seq"] for row in project_document_currentness.list_version_events(conn, revision["version_id"])] == [1, 2]

    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            "UPDATE doc_document_version_effect_events SET reason = 'rewritten' WHERE event_id = %s",
            (first["event_id"],),
        )
    conn.rollback()
    assert len(project_document_currentness.list_version_events(conn, revision["version_id"])) == 2


def test_idempotency_conflict_and_unknown_vocab_fail_closed(conn) -> None:
    document = _logical_document(conn)
    revision = _revision(conn, document=document, label="A", digest_char="b")
    key = _id("event")
    project_document_currentness.record_version_event(
        conn,
        document_version_id=revision["version_id"],
        event_type="created",
        new_status="draft",
        new_effect_class="working_revision",
        new_authority_status="internal_working_authority",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=key,
    )
    with pytest.raises(project_document_currentness.IdempotencyConflict):
        project_document_currentness.record_version_event(
            conn,
            document_version_id=revision["version_id"],
            event_type="created",
            new_status="issued",
            new_effect_class="working_revision",
            new_authority_status="internal_working_authority",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=key,
        )
    with pytest.raises(project_document_currentness.VocabularyError):
        project_document_currentness.record_version_event(
            conn,
            document_version_id=revision["version_id"],
            event_type="created",
            new_status="draft",
            new_effect_class="made_up_effect",
            new_authority_status="not_authoritative",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("bad-vocab"),
        )


def test_hermes_system_authority_and_consequential_authority_are_refused(conn) -> None:
    document = _logical_document(conn)
    revision = _revision(conn, document=document, label="A", digest_char="c")
    with pytest.raises(project_document_currentness.GovernanceGateRequired, match="Hermes"):
        project_document_currentness.record_version_event(
            conn,
            document_version_id=revision["version_id"],
            event_type="created",
            new_status="draft",
            new_effect_class="working_revision",
            new_authority_status="not_authoritative",
            actor="hermes",
            actor_kind="hermes",
            idempotency_key=_id("hermes"),
        )
    with pytest.raises(project_document_currentness.GovernanceGateRequired, match="system events"):
        project_document_currentness.record_version_event(
            conn,
            document_version_id=revision["version_id"],
            event_type="created",
            new_status="draft",
            new_effect_class="working_revision",
            new_authority_status="internal_working_authority",
            actor="system",
            actor_kind="system",
            idempotency_key=_id("system"),
        )
    with pytest.raises(project_document_currentness.GovernanceGateRequired, match="consequential"):
        project_document_currentness.record_version_event(
            conn,
            document_version_id=revision["version_id"],
            event_type="signed",
            new_status="signed",
            new_effect_class="signed_contractual_version",
            new_authority_status="contractual_authority",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("contract"),
            basis_refs=["decision:not-enough"],
        )


def test_database_also_refuses_consequential_authority_bypass(conn) -> None:
    document = _logical_document(conn)
    revision = _revision(conn, document=document, label="A", digest_char="d")
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            """
            INSERT INTO doc_document_version_effect_events (
                event_id, document_version_id, event_seq, event_type,
                new_status, new_effect_class, new_authority_status,
                actor, actor_kind, idempotency_key, payload_digest, result_snapshot
            ) VALUES (%s, %s, 1, 'signed', 'signed', 'signed_contractual_version',
                      'contractual_authority', 'bypass', 'human', %s, %s, '{}'::jsonb)
            """,
            (_id("event"), revision["version_id"], _id("key"), "e" * 64),
        )
    conn.rollback()
    assert project_document_currentness.list_version_events(conn, revision["version_id"]) == []


def test_latest_received_and_coordination_are_independent(conn) -> None:
    document = _logical_document(conn)
    revision_b = _revision(conn, document=document, label="B", digest_char="f")
    event_b = _event(conn, revision=revision_b, effect="coordination_update")

    current_before = project_document_currentness.resolve_currentness(
        conn, document_id=document["document_id"], purpose="current_for_coordination"
    )
    assert current_before["resolution_status"] == "resolved"
    assert current_before["document_version_id"] == revision_b["version_id"]
    assert current_before["basis"]["basis_refs"][0] == f"version-event:{event_b['event_id']}"

    revision_c = _revision(
        conn,
        document=document,
        label="C",
        digest_char="1",
        supersedes=revision_b["version_id"],
    )
    latest = project_document_currentness.resolve_currentness(
        conn, document_id=document["document_id"], purpose="latest_received"
    )
    coordination = project_document_currentness.resolve_currentness(
        conn, document_id=document["document_id"], purpose="current_for_coordination"
    )
    assert latest["document_version_id"] == revision_c["version_id"]
    assert latest["authority_status"] is None
    assert latest["authority"]["is_contractual_authority"] is False
    assert coordination["document_version_id"] == revision_b["version_id"]


def test_two_active_coordination_postures_conflict_until_old_one_is_explicitly_retired(conn) -> None:
    document = _logical_document(conn)
    revision_b = _revision(conn, document=document, label="B", digest_char="2")
    _event(conn, revision=revision_b, effect="coordination_update")
    revision_c = _revision(
        conn,
        document=document,
        label="C",
        digest_char="3",
        supersedes=revision_b["version_id"],
    )
    event_c = _event(conn, revision=revision_c, effect="coordination_update")

    conflict = project_document_currentness.resolve_currentness(
        conn, document_id=document["document_id"], purpose="current_for_coordination"
    )
    assert conflict["resolution_status"] == "conflicting"
    assert conflict["document_version_id"] is None
    assert len(conflict["basis"]["conflict_refs"]) == 2

    project_document_currentness.record_version_event(
        conn,
        document_version_id=revision_b["version_id"],
        event_type="superseded",
        new_status="superseded",
        new_effect_class="obsolete_superseded",
        new_authority_status="historical_evidence_only",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("retire-b"),
        reason="C explicitly replaces B for future coordination",
        basis_refs=[f"version-event:{event_c['event_id']}"],
    )
    conn.commit()
    resolved = project_document_currentness.resolve_currentness(
        conn, document_id=document["document_id"], purpose="current_for_coordination"
    )
    assert resolved["resolution_status"] == "resolved"
    assert resolved["document_version_id"] == revision_c["version_id"]


def test_current_working_uses_only_internal_reviewed_posture(conn) -> None:
    document = _logical_document(conn)
    revision = _revision(conn, document=document, label="A", digest_char="4")
    _event(
        conn,
        revision=revision,
        effect="working_revision",
        authority="internal_review_authority",
        status="under_review",
        event_type="created",
    )
    result = project_document_currentness.resolve_currentness(
        conn, document_id=document["document_id"], purpose="current_working"
    )
    assert result["resolution_status"] == "resolved"
    assert result["document_version_id"] == revision["version_id"]
    assert result["authority_status"] == "internal_review_authority"
    assert result["authority"]["is_approval"] is False


def test_consequential_and_unimplemented_purposes_are_explicitly_unresolved(conn) -> None:
    document = _logical_document(conn)
    revision = _revision(conn, document=document, label="A", digest_char="5")
    _event(conn, revision=revision, effect="coordination_update")

    expected = {
        "latest_reviewed": "reviewed-version",
        "current_for_consultation": "consultation",
        "current_contractual": "contractual",
        "current_for_execution": "execution",
        "current_for_site": "site",
        "latest_as_built_candidate": "as-built",
    }
    for purpose, marker in expected.items():
        result = project_document_currentness.resolve_currentness(
            conn, document_id=document["document_id"], purpose=purpose
        )
        assert result["resolution_status"] == "unresolved"
        assert result["document_version_id"] is None
        assert result["basis"]["basis_type"] == "insufficient_inputs"
        assert marker in " ".join(result["basis"]["missing_requirements"])
        assert result["authority"]["is_proof"] is False
