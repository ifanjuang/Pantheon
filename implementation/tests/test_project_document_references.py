"""PostgreSQL acceptance tests for A6 issuer document references."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import project_documents


@pytest.fixture
def conn():
    try:
        connection = project_documents.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_version_reference_observations, "
        "doc_document_events, doc_document_versions, doc_documents, "
        "source_documents RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _revision(conn, *, project_id: str = "project-alpha", label: str = "B") -> dict:
    document = project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id=project_id,
        document_type="ETUDE",
        title="Étude structure",
        discipline_code="STRUCTURE",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("create-document"),
    )
    source_document_id = _id("source-document")
    digest = uuid.uuid4().hex * 2
    source_ref = f"BET/{source_document_id}.pdf"
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 1234, 'ready')
        """,
        (source_document_id, project_id, project_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (source_document_id, source_ref, digest),
    )
    conn.commit()
    return project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_document_id,
        source_version=1,
        revision_label=label,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-revision"),
    )


def _record(conn, version_id: str, value: str, *, basis: str = "human_declared") -> dict:
    return project_documents.record_issuer_reference(
        conn,
        document_version_id=version_id,
        reference_value=value,
        basis_kind=basis,
        basis_ref=_id("basis"),
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("reference"),
    )


@pytest.mark.parametrize(
    "value",
    ["123", "A", "A17", "ST-204/EXE-03", "NDC-26-042", "001"],
)
def test_reference_formats_are_preserved_exactly(conn, value: str) -> None:
    revision = _revision(conn)
    observed = _record(conn, revision["version_id"], value)
    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )

    assert observed["reference_value"] == value
    assert resolved["resolution_status"] == "resolved"
    assert resolved["issuer_document_reference"] == value
    assert resolved["authority"]["changes_revision_order"] is False


def test_reference_is_distinct_from_revision_label(conn) -> None:
    revision = _revision(conn, label="B2")
    _record(conn, revision["version_id"], "ST-204")
    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )

    assert revision["revision_label"] == "B2"
    assert resolved["issuer_document_reference"] == "ST-204"


def test_non_string_reference_is_refused_without_coercion(conn) -> None:
    revision = _revision(conn)
    with pytest.raises(project_documents.ProjectDocumentError, match="must be a string"):
        project_documents.record_issuer_reference(
            conn,
            document_version_id=revision["version_id"],
            reference_value=123,  # type: ignore[arg-type]
            basis_kind="human_declared",
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("numeric"),
        )


def test_leading_zero_and_case_punctuation_remain_significant(conn) -> None:
    revision = _revision(conn)
    _record(conn, revision["version_id"], "001")
    _record(conn, revision["version_id"], "1", basis="source_observed")
    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )

    assert resolved["resolution_status"] == "conflicting"
    assert resolved["issuer_document_reference"] is None
    assert resolved["observed_values"] == ["001", "1"]


def test_same_exact_value_from_distinct_provenance_resolves_without_losing_history(conn) -> None:
    revision = _revision(conn)
    _record(conn, revision["version_id"], "A-01", basis="human_declared")
    _record(conn, revision["version_id"], "A-01", basis="source_observed")

    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )
    assert resolved["resolution_status"] == "resolved"
    assert resolved["issuer_document_reference"] == "A-01"
    assert resolved["observation_count"] == 2
    assert len(resolved["observations"]) == 2


def test_distinct_reference_observations_fail_closed_as_conflicting(conn) -> None:
    revision = _revision(conn)
    _record(conn, revision["version_id"], "ST-204-A")
    _record(conn, revision["version_id"], "ST-204A", basis="source_observed")

    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )
    assert resolved["resolution_status"] == "conflicting"
    assert resolved["issuer_document_reference"] is None
    assert resolved["observed_values"] == ["ST-204-A", "ST-204A"]


def test_no_observation_is_explicitly_unresolved(conn) -> None:
    revision = _revision(conn)
    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )
    assert resolved["resolution_status"] == "unresolved"
    assert resolved["issuer_document_reference"] is None


def test_idempotent_replay_is_exact_and_conflicting_key_reuse_is_refused(conn) -> None:
    revision = _revision(conn)
    key = _id("idem")
    kwargs = dict(
        document_version_id=revision["version_id"],
        reference_value="BET-42",
        basis_kind="human_declared",
        basis_ref="cartouche:page-1",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=key,
    )
    first = project_documents.record_issuer_reference(conn, **kwargs)
    replay = project_documents.record_issuer_reference(conn, **kwargs)
    assert replay == first

    with pytest.raises(project_documents.ReferenceIdempotencyConflict):
        project_documents.record_issuer_reference(
            conn,
            **{**kwargs, "reference_value": "BET-43"},
        )


def test_reference_history_is_append_only(conn) -> None:
    revision = _revision(conn)
    observed = _record(conn, revision["version_id"], "BET-42")
    conn.commit()

    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            """
            UPDATE doc_document_version_reference_observations
               SET reference_value = 'BET-43'
             WHERE observation_id = %s
            """,
            (observed["observation_id"],),
        )
    conn.rollback()

    resolved = project_documents.resolve_issuer_document_reference(
        conn, revision["version_id"]
    )
    assert resolved["issuer_document_reference"] == "BET-42"


def test_hermes_direct_reference_observation_is_refused(conn) -> None:
    revision = _revision(conn)
    with pytest.raises(project_documents.GovernanceGateRequired):
        project_documents.record_issuer_reference(
            conn,
            document_version_id=revision["version_id"],
            reference_value="A17",
            basis_kind="source_observed",
            actor="hermes",
            actor_kind="hermes",
            idempotency_key=_id("hermes"),
        )


def test_reference_observations_do_not_change_revision_order_or_currentness(conn) -> None:
    revision = _revision(conn, label="Z")
    before = project_documents.resolve_latest_received(conn, revision["document_id"])
    assert before is not None

    _record(conn, revision["version_id"], "0001")
    after = project_documents.resolve_latest_received(conn, revision["document_id"])

    assert after == before
    assert project_documents.get_revision(conn, revision["version_id"])["version_seq"] == 1
