from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from mvp_vertical import knowledge, retrieval, store
from mvp_vertical.contract import TaskContract
from mvp_vertical.documents import file_digest


def _contract(dossier: str, source_ref: str) -> TaskContract:
    contract_id = f"task-{dossier}"
    return TaskContract(
        raw={
            "object_type": "task_contract",
            "object_id": contract_id,
            "contract_id": contract_id,
            "scope": {
                "dossier": dossier,
                "declared_sources": [{"source_ref": source_ref}],
            },
        },
        path=Path("task.yaml"),
        dossier=dossier,
        sources=(source_ref,),
        forbidden=(),
    )


def _connect_or_skip():
    try:
        return store.connect()
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL/pgvector unreachable: {exc}")


def test_store_schema_versions_retrieval_identity_by_digest() -> None:
    conn = _connect_or_skip()
    try:
        constraint = conn.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname = 'chunks_retrieval_identity_key'"
        ).fetchone()
        assert constraint is not None
        assert "source_digest" in constraint[0]

        projection = conn.execute(
            """
            SELECT is_nullable
              FROM information_schema.columns
             WHERE table_name = 'retrieval_chunk_projections'
               AND column_name = 'source_digest'
            """
        ).fetchone()
        units = conn.execute(
            """
            SELECT is_nullable
              FROM information_schema.columns
             WHERE table_name = 'retrieval_chunk_units'
               AND column_name = 'source_digest'
            """
        ).fetchone()
        assert projection == ("NO",)
        assert units == ("NO",)
    finally:
        conn.close()


def test_legacy_schema_upgrade_is_serialized_without_penalizing_normal_startup() -> None:
    migration = store.VERSIONED_RETRIEVAL_DDL
    assert "pg_advisory_xact_lock" in migration
    # Outer check keeps already-migrated startup lock-light; inner check makes
    # a second first-start worker re-read after waiting for the one-time lock.
    assert migration.count("chunks_retrieval_identity_key") >= 3
    assert migration.index("IF NOT EXISTS") < migration.index("pg_advisory_xact_lock")


def test_reingest_keeps_old_digest_but_legacy_retrieval_stays_current(tmp_path) -> None:
    conn = _connect_or_skip()
    dossier = f"versioned-retrieval-{uuid.uuid4().hex}"
    source_ref = "sources/reference.md"
    contract = _contract(dossier, source_ref)
    source = tmp_path / source_ref
    source.parent.mkdir(parents=True)

    try:
        source.write_text("# Reference\n\nlegacytoken belongs only to the older revision.", encoding="utf-8")
        old_digest = file_digest(source)
        store.ingest(conn, contract, tmp_path, ingestion_id="old-revision")

        source.write_text("# Reference\n\ncurrenttoken belongs only to the newer revision.", encoding="utf-8")
        new_digest = file_digest(source)
        assert new_digest != old_digest
        store.ingest(conn, contract, tmp_path, ingestion_id="new-revision")

        digests = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source_digest FROM chunks "
                "WHERE dossier = %s AND source_ref = %s",
                (dossier, source_ref),
            ).fetchall()
        }
        assert digests == {old_digest, new_digest}

        current_semantic = store.retrieve_scoped(conn, contract, "legacytoken", top_k=10)
        assert current_semantic
        assert {hit.source_digest for hit in current_semantic} == {new_digest}

        current_lexical = retrieval.retrieve_lexical_scoped(
            conn, contract, "legacytoken", top_k=10
        )
        assert current_lexical == []

        exact_old_semantic = store.retrieve_exact_scoped(
            conn,
            contract,
            "legacytoken",
            sources=((source_ref, old_digest),),
            top_k=10,
        )
        assert exact_old_semantic
        assert {hit.source_digest for hit in exact_old_semantic} == {old_digest}
        assert any("legacytoken" in hit.body for hit in exact_old_semantic)

        exact_old_lexical = retrieval.retrieve_lexical_exact_scoped(
            conn,
            contract,
            "legacytoken",
            sources=((source_ref, old_digest),),
            top_k=10,
        )
        assert exact_old_lexical
        assert {hit.source_digest for hit in exact_old_lexical} == {old_digest}

        exact_new_lexical = retrieval.retrieve_lexical_exact_scoped(
            conn,
            contract,
            "currenttoken",
            sources=((source_ref, new_digest),),
            top_k=10,
        )
        assert exact_new_lexical
        assert {hit.source_digest for hit in exact_new_lexical} == {new_digest}

        missing = "0" * 64
        assert store.retrieve_exact_scoped(
            conn,
            contract,
            "legacytoken",
            sources=((source_ref, missing),),
            top_k=10,
        ) == []
        assert retrieval.retrieve_lexical_exact_scoped(
            conn,
            contract,
            "legacytoken",
            sources=((source_ref, missing),),
            top_k=10,
        ) == []
    finally:
        conn.close()


def test_knowledge_publication_binds_current_body_and_locator_after_reingest(tmp_path) -> None:
    conn = _connect_or_skip()
    dossier = f"knowledge-versioned-retrieval-{uuid.uuid4().hex}"
    source_ref = "sources/reference.md"
    contract = _contract(dossier, source_ref)
    source = tmp_path / source_ref
    source.parent.mkdir(parents=True)

    try:
        source.write_text("# Reference\n\nold body for immutable provenance.", encoding="utf-8")
        old_digest = file_digest(source)
        store.ingest(conn, contract, tmp_path, ingestion_id="knowledge-old")

        source.write_text("# Reference\n\ncurrent body for immutable provenance.", encoding="utf-8")
        new_digest = file_digest(source)
        store.ingest(conn, contract, tmp_path, ingestion_id="knowledge-current")
        assert new_digest != old_digest

        card = store.get_document_card(conn, dossier, source_ref)
        current_ref = card["extraction"]["chunk_refs"][0]
        current_body = conn.execute(
            """
            SELECT body FROM chunks
             WHERE dossier = %s AND source_ref = %s AND source_digest = %s AND chunk_no = 0
            """,
            (dossier, source_ref, new_digest),
        ).fetchone()[0]

        knowledge_id = f"knowledge-{uuid.uuid4().hex}"
        knowledge.publish_knowledge(
            conn,
            knowledge_id=knowledge_id,
            document_id=card["document_id"],
            title="Current provenance",
            family="techniques",
            markdown="# Current provenance\n\nDerived editorial note.",
            source_chunk_refs=[current_ref],
            created_by="reviewer",
            actor_kind="human",
            idempotency_key=f"publish-{uuid.uuid4().hex}",
        )

        persisted = conn.execute(
            """
            SELECT source_digest, text_digest, structural_locator
              FROM knowledge_source_chunks
             WHERE knowledge_id = %s
            """,
            (knowledge_id,),
        ).fetchone()
        assert persisted is not None
        assert persisted[0] == new_digest
        assert persisted[1] == hashlib.sha256(current_body.encode("utf-8")).hexdigest()
        assert persisted[2]
    finally:
        conn.close()


def test_rrf_does_not_collapse_two_digests_at_same_path_and_chunk() -> None:
    old = store.RetrievedChunk(
        source_ref="sources/reference.md",
        chunk_no=0,
        body="old",
        distance=0.1,
        source_digest="old-digest",
    )
    new = store.RetrievedChunk(
        source_ref="sources/reference.md",
        chunk_no=0,
        body="new",
        distance=0.2,
        source_digest="new-digest",
    )

    fused = retrieval.reciprocal_rank_fusion(
        [old, new],
        [new, old],
        top_k=2,
        candidate_k=2,
    )

    assert len(fused) == 2
    assert {hit.chunk.source_digest for hit in fused} == {"old-digest", "new-digest"}
