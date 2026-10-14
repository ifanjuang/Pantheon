"""pgvector store: bounded ingestion and scope-first retrieval.

The two rules that matter live here:

1. Ingestion reads ONLY the contract's declared sources — anything else
   raises before touching the database.
2. Retrieval filters on the declared perimeter in SQL *before* vector
   ranking. A query cannot see outside the contract by construction.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import psycopg

from .contract import TaskContract, assert_source_in_scope, resolve_source_within
from .documents import (
    ConvertedDocument,
    DocumentConversionError,
    DocumentConverter,
    converter_for,
    file_digest,
)
from .embedder import DIM, embed, to_pgvector
from .naming import DocumentName, parse_document_name
from .structured_extraction import (
    CompilationResult,
    chunk_ref,
    compilation_id,
    compile_document,
    unit_id,
)

STRUCTURED_EXTRACTION_DDL = (
    Path(__file__).resolve().parent / "sql" / "008_structured_extraction.sql"
).read_text(encoding="utf-8")
VERSIONED_RETRIEVAL_DDL = (
    Path(__file__).resolve().parent / "sql" / "035_versioned_retrieval_chunks.sql"
).read_text(encoding="utf-8")

# Audit identity (external review, finding #6): every chunk carries enough to
# prove, at retrieval time, exactly what produced it — which contract version
# (contract_id + contract_digest), which ingestion run (ingestion_id, an
# injectable nonce, finding #8), and which source version (source_digest).
#
# DDL runs on EVERY connect(), so fresh-table definitions stay lock-light and
# pre-existing schema evolution is isolated in a catalog-guarded migration.
DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks (
    id        BIGSERIAL PRIMARY KEY,
    dossier   TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    chunk_no  INT  NOT NULL,
    body      TEXT NOT NULL,
    embedding vector({DIM}) NOT NULL,
    contract_id     TEXT NOT NULL DEFAULT '',
    contract_digest TEXT NOT NULL DEFAULT '',
    ingestion_id    TEXT NOT NULL DEFAULT '',
    source_digest   TEXT NOT NULL DEFAULT '',
    CONSTRAINT chunks_retrieval_identity_key
        UNIQUE (dossier, source_ref, source_digest, chunk_no)
);
CREATE TABLE IF NOT EXISTS source_documents (
    document_id TEXT PRIMARY KEY,
    dossier TEXT NOT NULL,
    parent_project_id TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    media_type TEXT NOT NULL,
    byte_size BIGINT NOT NULL,
    analysis_status TEXT NOT NULL,
    current_extraction_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dossier, source_ref)
);
CREATE TABLE IF NOT EXISTS document_naming (
    document_id TEXT PRIMARY KEY REFERENCES source_documents(document_id) ON DELETE CASCADE,
    project_code TEXT NOT NULL,
    revision_index TEXT NOT NULL,
    phase_code TEXT NOT NULL,
    phase_folder TEXT NOT NULL,
    distributor TEXT NOT NULL,
    document_type TEXT NOT NULL,
    object_name TEXT NOT NULL,
    document_date DATE NOT NULL,
    extension TEXT NOT NULL,
    filename TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS extraction_runs (
    extraction_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON DELETE CASCADE,
    contract_id TEXT NOT NULL,
    contract_digest TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    converter TEXT NOT NULL,
    converter_version TEXT NOT NULL,
    config_digest TEXT NOT NULL,
    status TEXT NOT NULL,
    markdown_content TEXT,
    document_json JSONB,
    chunk_count INT NOT NULL DEFAULT 0,
    processing_time DOUBLE PRECISION,
    quality_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS extraction_cache_lookup
    ON extraction_runs (document_id, source_digest, converter, converter_version, config_digest);
CREATE TABLE IF NOT EXISTS document_versions (
    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON DELETE CASCADE,
    version INT NOT NULL CHECK (version > 0),
    source_ref TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    media_type TEXT NOT NULL,
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, version),
    UNIQUE (document_id, source_digest)
);
CREATE TABLE IF NOT EXISTS extraction_observations (
    extraction_id TEXT PRIMARY KEY REFERENCES extraction_runs(extraction_id) ON DELETE CASCADE,
    observation_kind TEXT NOT NULL CHECK (
        observation_kind IN ('direct_text', 'fixture', 'live_parser')
    )
);
CREATE TABLE IF NOT EXISTS document_extraction_bindings (
    document_id TEXT PRIMARY KEY REFERENCES source_documents(document_id) ON DELETE CASCADE,
    extraction_id TEXT NOT NULL REFERENCES extraction_runs(extraction_id) ON DELETE RESTRICT,
    ingestion_id TEXT NOT NULL,
    cache_reused BOOLEAN NOT NULL DEFAULT FALSE,
    bound_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS knowledge_items (
    knowledge_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON DELETE RESTRICT,
    source_version INT NOT NULL CHECK (source_version > 0),
    source_digest TEXT NOT NULL,
    extraction_id TEXT NOT NULL REFERENCES extraction_runs(extraction_id) ON DELETE RESTRICT,
    title TEXT NOT NULL CHECK (length(title) > 0),
    family TEXT NOT NULL CHECK (
        family IN ('referentiels', 'responsabilite', 'methodologie', 'techniques', 'reglementations')
    ),
    markdown TEXT NOT NULL CHECK (length(markdown) > 0),
    markdown_digest TEXT NOT NULL,
    source_chunk_refs JSONB NOT NULL,
    review_status TEXT NOT NULL CHECK (
        review_status IN ('generated_unreviewed', 'needs_review', 'reviewed', 'superseded')
    ),
    version INT NOT NULL CHECK (version > 0),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS knowledge_project_lookup
    ON knowledge_items (document_id, updated_at DESC);
CREATE TABLE IF NOT EXISTS knowledge_source_chunks (
    knowledge_id TEXT NOT NULL REFERENCES knowledge_items(knowledge_id) ON DELETE CASCADE,
    chunk_ref TEXT NOT NULL,
    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON DELETE RESTRICT,
    extraction_id TEXT NOT NULL REFERENCES extraction_runs(extraction_id) ON DELETE RESTRICT,
    ordinal INT NOT NULL CHECK (ordinal >= 0),
    text_digest TEXT NOT NULL,
    body_snapshot TEXT,
    source_ref TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    structural_locator TEXT NOT NULL,
    PRIMARY KEY (knowledge_id, chunk_ref)
);
CREATE TABLE IF NOT EXISTS knowledge_events (
    event_id TEXT PRIMARY KEY,
    aggregate_kind TEXT NOT NULL DEFAULT 'knowledge' CHECK (aggregate_kind = 'knowledge'),
    aggregate_ref TEXT NOT NULL REFERENCES knowledge_items(knowledge_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('knowledge_published', 'knowledge_revised', 'knowledge_review_status_changed')
    ),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'hermes', 'system')),
    expected_version INT NOT NULL CHECK (expected_version >= 0),
    resulting_version INT NOT NULL CHECK (resulting_version = expected_version + 1),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    result_snapshot JSONB NOT NULL,
    base_content_snapshot JSONB,
    resulting_content_snapshot JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE IF NOT EXISTS knowledge_edit_requests (
    request_id TEXT PRIMARY KEY,
    knowledge_id TEXT NOT NULL REFERENCES knowledge_items(knowledge_id) ON DELETE CASCADE,
    instruction_kind TEXT NOT NULL CHECK (
        instruction_kind IN ('rewrite', 'expand', 'simplify', 'verify', 'move_to_lot')
    ),
    instruction TEXT NOT NULL,
    base_version INT NOT NULL CHECK (base_version > 0),
    selection_start INT NOT NULL CHECK (selection_start >= 0),
    selection_end INT NOT NULL CHECK (selection_end >= selection_start),
    selected_text_digest TEXT NOT NULL,
    replacement_markdown TEXT,
    recompile_context_digest TEXT,
    replacement_source_chunk_refs JSONB,
    status TEXT NOT NULL CHECK (
        status IN ('queued_for_hermes', 'proposed', 'applied', 'conflict', 'rejected')
    ),
    requested_by TEXT NOT NULL,
    request_idempotency_key TEXT NOT NULL UNIQUE,
    request_payload_digest TEXT NOT NULL,
    apply_idempotency_key TEXT UNIQUE,
    apply_payload_digest TEXT,
    apply_result_snapshot JSONB,
    applied_version INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- knowledge_events is read with `ORDER BY occurred_at, event_id`, and
-- CURRENT_TIMESTAMP is the transaction start time, so events written together
-- sorted by a random UUID. CREATE TABLE IF NOT EXISTS above never revisits a
-- table that already exists, so existing databases are corrected here. Guarded on
-- the value this adds, so a started-up installation performs a catalog read only.
DO $knowledge_events$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE knowledge_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$knowledge_events$;

-- Knowledge revision history is the retained owner for exact before/after
-- snapshots. Match the repository's other event logs: rows may be appended,
-- never rewritten or deleted after they are recorded.
CREATE OR REPLACE FUNCTION reject_knowledge_event_mutation()
RETURNS trigger AS $knowledge_event_guard$
BEGIN
    RAISE EXCEPTION 'knowledge_events are append-only';
END;
$knowledge_event_guard$ LANGUAGE plpgsql;

DO $knowledge_events_append_only$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_trigger
         WHERE tgname = 'knowledge_events_append_only'
           AND tgrelid = 'knowledge_events'::regclass
           AND NOT tgisinternal
    ) THEN
        CREATE TRIGGER knowledge_events_append_only
        BEFORE UPDATE OR DELETE ON knowledge_events
        FOR EACH ROW EXECUTE FUNCTION reject_knowledge_event_mutation();
    END IF;
END;
$knowledge_events_append_only$;

-- Slice Pantheon-Next#1118 freezes the exact cited chunk body inside the existing
-- provenance relation. Legacy rows remain nullable and may use retained
-- historical chunks when their frozen digest still matches.
DO $knowledge_source_body_snapshot$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_source_chunks'
           AND column_name = 'body_snapshot'
    ) THEN
        ALTER TABLE knowledge_source_chunks
            ADD COLUMN body_snapshot TEXT;
    END IF;
END;
$knowledge_source_body_snapshot$;

-- Knowledge event replay keeps its existing compact result_snapshot contract.
-- These nullable content snapshots preserve the exact editorial Markdown and
-- source bindings across accepted revisions without creating another history
-- owner or changing idempotent replay payloads.
DO $knowledge_event_history$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_events'
           AND column_name = 'base_content_snapshot'
    ) THEN
        ALTER TABLE knowledge_events
            ADD COLUMN base_content_snapshot JSONB;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_events'
           AND column_name = 'resulting_content_snapshot'
    ) THEN
        ALTER TABLE knowledge_events
            ADD COLUMN resulting_content_snapshot JSONB;
    END IF;
END;
$knowledge_event_history$;

-- Slice Pantheon-Next#1118 extends the existing intelligent-edit request with optional
-- recompile provenance. Existing installations keep the same owner/table; the
-- two nullable columns merely bind a full-document recompilation proposal to
-- the exact source-state snapshot it was produced from.
DO $knowledge_recompile$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_edit_requests'
           AND column_name = 'recompile_context_digest'
    ) THEN
        ALTER TABLE knowledge_edit_requests
            ADD COLUMN recompile_context_digest TEXT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_edit_requests'
           AND column_name = 'replacement_source_chunk_refs'
    ) THEN
        ALTER TABLE knowledge_edit_requests
            ADD COLUMN replacement_source_chunk_refs JSONB;
    END IF;
END;
$knowledge_recompile$;
""" + STRUCTURED_EXTRACTION_DDL + VERSIONED_RETRIEVAL_DDL


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contract_digest(contract: TaskContract) -> str:
    """sha256 over the canonical contract — proves which contract version an
    ingested chunk was scoped by. Same shape/discipline as the gate's digests."""
    canonical = json.dumps(contract.raw, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _sha256(canonical)


def normalize_subject_tags(tags: list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalize explicit document topics without inferring them from content."""
    if isinstance(tags, str):
        raise ValueError("subject tags must be supplied as a list, not one string")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in tags or ():
        tag = str(value).strip()
        if not tag:
            continue
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    if len(normalized) > 100:
        raise ValueError("a document cannot carry more than 100 subject tags")
    return normalized


def _upsert_document_subject_tags(
    conn: psycopg.Connection,
    document_id: str,
    subject_tags: list[str] | tuple[str, ...] | None,
) -> None:
    # None means "not supplied" and preserves an existing classification.
    # An explicit empty list clears it.
    if subject_tags is None:
        return
    conn.execute(
        """
        INSERT INTO document_classifications (document_id, subject_tags)
        VALUES (%s, %s::jsonb)
        ON CONFLICT (document_id) DO UPDATE SET
            subject_tags = EXCLUDED.subject_tags,
            updated_at = CURRENT_TIMESTAMP
        """,
        (document_id, json.dumps(normalize_subject_tags(subject_tags))),
    )


def _document_id(dossier: str, source_ref: str) -> str:
    identity = dossier + "\0" + source_ref
    return f"doc-{_sha256(identity)[:24]}"


def _extraction_id(ingestion_id: str, document_id: str) -> str:
    return f"ext-{ingestion_id}-{document_id.removeprefix('doc-')}"


def _observation_kind(converter: DocumentConverter | None) -> str | None:
    if converter is None:
        return None
    kind = getattr(converter, "observation_kind", None)
    if kind not in {"direct_text", "fixture", "live_parser"}:
        raise DocumentConversionError(
            "document converter must declare observation_kind as direct_text, fixture or live_parser"
        )
    return kind


def _record_document_version(
    conn: psycopg.Connection,
    document_id: str,
    source_ref: str,
    source_digest: str,
    media_type: str,
    byte_size: int,
) -> None:
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        )
        SELECT %s, COALESCE(MAX(version), 0) + 1, %s, %s, %s, %s
          FROM document_versions
         WHERE document_id = %s
           AND NOT EXISTS (
               SELECT 1 FROM document_versions
                WHERE document_id = %s AND source_digest = %s
           )
        ON CONFLICT (document_id, source_digest) DO NOTHING
        """,
        (
            document_id, source_ref, source_digest, media_type, byte_size,
            document_id, document_id, source_digest,
        ),
    )


def _parent_project_id(contract: TaskContract) -> str:
    scope = contract.raw.get("scope") or {}
    return str(scope.get("parent_project_id") or scope.get("project_id") or contract.dossier)


def dsn_from_env() -> str:
    return os.environ.get(
        "MVP_PG_DSN",
        "postgresql://mvp:mvp@localhost:5433/mvp",
    )


@dataclass(frozen=True)
class RetrievedChunk:
    source_ref: str
    chunk_no: int
    body: str
    distance: float
    # Audit identity (finding #6). Default to "" so a legacy/manual construction
    # (e.g. test helpers, or a pre-migration row) stays valid.
    contract_id: str = ""
    contract_digest: str = ""
    ingestion_id: str = ""
    source_digest: str = ""
    content_type: str = ""
    page_start: int | None = None
    page_end: int | None = None
    structural_locator: str = ""
    parent_heading: str | None = None
    section_path: tuple[str, ...] = ()
    quality_flags: tuple[str, ...] = ()

    @property
    def retrieval_trace(self) -> str:
        # Unchanged format — verify_draft parses [source_ref#chunk-N] from it.
        return f"pgvector://chunks/{self.source_ref}#chunk-{self.chunk_no}"

    @property
    def retrieval_audit(self) -> dict:
        """The auditable identity of this chunk: which contract version, which
        ingestion run, and which source version produced it."""
        return {
            "contract_id": self.contract_id,
            "contract_digest": self.contract_digest,
            "ingestion_id": self.ingestion_id,
            "source_digest": self.source_digest,
        }

    @property
    def retrieval_provenance(self) -> dict:
        """Structural locator for review; still neither source nor Evidence."""
        return {
            "content_type": self.content_type,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "structural_locator": self.structural_locator,
            "parent_heading": self.parent_heading,
            "section_path": list(self.section_path),
            "quality_flags": list(self.quality_flags),
        }


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = psycopg.connect(dsn or dsn_from_env())
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    return conn


def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    blocks, current = [], ""
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 > max_chars and current:
            blocks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        blocks.append(current)
    return blocks


def _cached_conversion(
    conn: psycopg.Connection,
    *,
    document_id: str,
    source_digest: str,
    converter: DocumentConverter,
) -> tuple[ConvertedDocument, str] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT extraction_id, markdown_content, document_json, status,
                   processing_time, quality_flags
              FROM extraction_runs
             WHERE document_id = %s AND source_digest = %s
               AND converter = %s AND converter_version = %s AND config_digest = %s
               AND status IN ('ready', 'needs_review')
             ORDER BY finished_at DESC
             LIMIT 1
            """,
            (
                document_id,
                source_digest,
                converter.converter,
                converter.converter_version,
                converter.config_digest,
            ),
        )
        row = cur.fetchone()
    if row is None:
        return None
    extraction_id, markdown, document_json, status, processing_time, quality_flags = row
    return (
        ConvertedDocument(
            markdown=markdown,
            document_json=document_json,
            converter=converter.converter,
            converter_version=converter.converter_version,
            config_digest=converter.config_digest,
            status=status,
            processing_time=processing_time,
            quality_flags=tuple(quality_flags or ()) + ("cache_reused",),
        ),
        extraction_id,
    )


def _persist_compilation(
    conn: psycopg.Connection,
    *,
    extraction_id: str,
    compiled: CompilationResult,
) -> str:
    """Persist one immutable deterministic compilation, or verify its replay."""
    cref = compilation_id(extraction_id)
    conn.execute(
        """
        INSERT INTO structured_compilations (
            compilation_id, extraction_id, compiler, compiler_version,
            config_digest, output_digest, status, quality_flags, diagnostics,
            unit_count, chunk_count, page_count, table_count, anomaly_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s)
        ON CONFLICT (compilation_id) DO NOTHING
        """,
        (
            cref, extraction_id, compiled.compiler, compiled.compiler_version,
            compiled.config_digest, compiled.output_digest, compiled.status,
            json.dumps(compiled.quality_flags), json.dumps(compiled.diagnostics),
            len(compiled.units), len(compiled.chunks),
            compiled.page_count, compiled.table_count, compiled.anomaly_count,
        ),
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT output_digest FROM structured_compilations WHERE compilation_id = %s",
            (cref,),
        )
        row = cur.fetchone()
    if row is None or row[0] != compiled.output_digest:
        raise DocumentConversionError(
            "structured compilation replay changed for the same immutable identity"
        )
    for ordinal, unit in enumerate(compiled.units):
        conn.execute(
            """
            INSERT INTO extraction_units (
                unit_id, compilation_id, extraction_id, ordinal, content_type,
                body, text_digest, page_start, page_end, structural_locator,
                parent_heading, heading_level, section_path, quality_flags, table_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
            ON CONFLICT (unit_id) DO NOTHING
            """,
            (
                unit_id(cref, ordinal), cref, extraction_id, ordinal, unit.content_type,
                unit.text, unit.text_digest, unit.page_start, unit.page_end,
                unit.structural_locator, unit.parent_heading,
                unit.heading_level, json.dumps(unit.section_path),
                json.dumps(unit.quality_flags),
                json.dumps(unit.table_data) if unit.table_data is not None else None,
            ),
        )
    return cref


def _upsert_document_naming(
    conn: psycopg.Connection,
    document_id: str,
    naming: DocumentName | None,
) -> None:
    if naming is None:
        return
    conn.execute(
        """
        INSERT INTO document_naming (
            document_id, project_code, revision_index, phase_code, phase_folder,
            distributor, document_type, object_name, document_date, extension, filename
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (document_id) DO UPDATE SET
            project_code = EXCLUDED.project_code,
            revision_index = EXCLUDED.revision_index,
            phase_code = EXCLUDED.phase_code,
            phase_folder = EXCLUDED.phase_folder,
            distributor = EXCLUDED.distributor,
            document_type = EXCLUDED.document_type,
            object_name = EXCLUDED.object_name,
            document_date = EXCLUDED.document_date,
            extension = EXCLUDED.extension,
            filename = EXCLUDED.filename
        """,
        (
            document_id, naming.project_code, naming.revision_index,
            naming.phase_code, naming.phase_folder, naming.distributor,
            naming.document_type, naming.object_name, naming.document_date,
            naming.extension, naming.filename,
        ),
    )


def _record_failed_extraction(
    conn: psycopg.Connection,
    *,
    contract: TaskContract,
    source_ref: str,
    path: Path,
    source_digest: str,
    ingestion_id: str,
    converter: DocumentConverter | None,
    error: Exception,
    naming: DocumentName | None = None,
    subject_tags: list[str] | tuple[str, ...] | None = None,
) -> None:
    document_id = _document_id(contract.dossier, source_ref)
    extraction_id = _extraction_id(ingestion_id, document_id)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO source_documents (
                document_id, dossier, parent_project_id, source_ref, source_digest, media_type,
                byte_size, analysis_status, current_extraction_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'failed', %s)
            ON CONFLICT (dossier, source_ref) DO UPDATE SET
                parent_project_id = EXCLUDED.parent_project_id,
                source_digest = EXCLUDED.source_digest,
                media_type = EXCLUDED.media_type,
                byte_size = EXCLUDED.byte_size,
                analysis_status = 'failed',
                current_extraction_id = EXCLUDED.current_extraction_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                document_id, contract.dossier, _parent_project_id(contract),
                source_ref, source_digest,
                media_type, path.stat().st_size, extraction_id,
            ),
        )
        _upsert_document_subject_tags(conn, document_id, subject_tags)
        _upsert_document_naming(conn, document_id, naming)
        _record_document_version(
            conn, document_id, source_ref, source_digest, media_type, path.stat().st_size
        )
        conn.execute(
            """
            INSERT INTO extraction_runs (
                extraction_id, document_id, contract_id, contract_digest,
                source_digest, converter, converter_version, config_digest,
                status, error
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'failed', %s)
            """,
            (
                extraction_id, document_id, contract.contract_id, contract_digest(contract),
                source_digest,
                converter.converter if converter else "unavailable",
                converter.converter_version if converter else "unknown",
                converter.config_digest if converter else "unknown",
                str(error),
            ),
        )
        observation_kind = _observation_kind(converter)
        if observation_kind is not None:
            conn.execute(
                "INSERT INTO extraction_observations (extraction_id, observation_kind) "
                "VALUES (%s, %s)",
                (extraction_id, observation_kind),
            )
        conn.execute(
            """
            INSERT INTO document_extraction_bindings (
                document_id, extraction_id, ingestion_id, cache_reused
            ) VALUES (%s, %s, %s, FALSE)
            ON CONFLICT (document_id) DO UPDATE SET
                extraction_id = EXCLUDED.extraction_id,
                ingestion_id = EXCLUDED.ingestion_id,
                cache_reused = FALSE,
                bound_at = CURRENT_TIMESTAMP
            """,
            (document_id, extraction_id, ingestion_id),
        )
        conn.execute(
            "DELETE FROM document_compilation_bindings WHERE document_id = %s",
            (document_id,),
        )
    conn.commit()


def ingest(
    conn: psycopg.Connection,
    contract: TaskContract,
    root: Path,
    *,
    ingestion_id: str | None = None,
    docling: DocumentConverter | None = None,
    source_refs: tuple[str, ...] | None = None,
    naming_by_source: dict[str, DocumentName] | None = None,
    subject_tags_by_source: dict[str, list[str] | tuple[str, ...]] | None = None,
) -> int:
    """Ingest the contract's declared sources — and nothing else.

    Every chunk is stamped with its audit identity (finding #6): the contract
    id and digest, the ingestion id (a per-run nonce — injectable for tests and
    replay, finding #8; defaults to a fresh uuid), and the digest of the exact
    source content it came from. Re-ingesting refreshes only the same immutable
    digest; older digests remain indexed for exact governed retrieval.

    Re-ingestion is scoped to one immutable ``source_digest``: replaying a
    digest refreshes only itself, and other digests at the same path stay
    indexed. A ``replace_dossier`` flag used to sit here and was removed once it
    stopped deleting anything — both callers passed ``False`` for a protection
    it no longer provided, and the digest scope is what actually provides it.
    """
    ingestion_id = ingestion_id or uuid.uuid4().hex
    cdigest = contract_digest(contract)
    selected_sources = source_refs if source_refs is not None else contract.sources
    if not selected_sources:
        return 0
    subject_tags_by_source = subject_tags_by_source or {}
    unexpected_tag_sources = set(subject_tags_by_source) - set(selected_sources)
    if unexpected_tag_sources:
        raise ValueError(
            "subject tags were supplied for sources outside this ingestion: "
            + ", ".join(sorted(unexpected_tag_sources))
        )
    subject_tags_by_source = {
        source_ref: normalize_subject_tags(tags)
        for source_ref, tags in subject_tags_by_source.items()
    }
    prepared: list[
        tuple[
            str,
            Path,
            str,
            ConvertedDocument,
            CompilationResult,
            DocumentName | None,
            str,
            str | None,
            str,
            list[str] | tuple[str, ...] | None,
        ]
    ] = []
    for source_ref in selected_sources:
        assert_source_in_scope(contract, source_ref)  # explicit guard at the effect boundary
        naming = (naming_by_source or {}).get(source_ref)
        path = resolve_source_within(root, source_ref, contract.contract_id)
        sdigest = file_digest(path)
        selected: DocumentConverter | None = None
        try:
            selected = converter_for(path, docling)
            document_id = _document_id(contract.dossier, source_ref)
            cached = _cached_conversion(
                conn,
                document_id=document_id,
                source_digest=sdigest,
                converter=selected,
            )
            if cached is None:
                converted = selected.convert(path)
                reused_extraction_id = None
            else:
                converted, reused_extraction_id = cached
            try:
                compiled = compile_document(
                    markdown=converted.markdown,
                    document_json=converted.document_json,
                    converter=converted.converter,
                )
            except ValueError as exc:
                raise DocumentConversionError(
                    f"structured compilation failed for {path.name}: {exc}"
                ) from exc
            analysis_status = (
                "needs_review"
                if "needs_review" in {converted.status, compiled.status}
                else "ready"
            )
            prepared.append(
                (
                    source_ref, path, sdigest, converted, compiled, naming,
                    _observation_kind(selected), reused_extraction_id, analysis_status,
                    subject_tags_by_source.get(source_ref),
                )
            )
        except (DocumentConversionError, OSError) as exc:
            _record_failed_extraction(
                conn,
                contract=contract,
                source_ref=source_ref,
                path=path,
                source_digest=sdigest,
                ingestion_id=ingestion_id,
                converter=selected,
                error=exc,
                naming=naming,
                subject_tags=subject_tags_by_source.get(source_ref),
            )
            raise

    # Cache lookups are reads but psycopg starts a transaction for them. End
    # that read transaction before the atomic replacement below.
    conn.commit()

    # Every multi-document writer takes source-document row locks in this
    # stable identity order. Knowledge recompile apply uses the same ordering,
    # so ingestion and provenance rebinding cannot deadlock on shared sources.
    prepared.sort(key=lambda entry: _document_id(contract.dossier, entry[0]))

    total = 0
    with conn.transaction():
        for (
            source_ref, path, sdigest, converted, compiled, naming,
            observation_kind, reused_extraction_id, analysis_status, subject_tags,
        ) in prepared:
            # Replaying the same immutable source is idempotent while other
            # digests at the same path remain available for exact retrieval.
            conn.execute(
                "DELETE FROM chunks "
                "WHERE dossier = %s AND source_ref = %s AND source_digest = %s",
                (contract.dossier, source_ref, sdigest),
            )
            document_id = _document_id(contract.dossier, source_ref)
            extraction_id = reused_extraction_id or _extraction_id(ingestion_id, document_id)
            media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            conn.execute(
                """
                INSERT INTO source_documents (
                    document_id, dossier, parent_project_id, source_ref, source_digest, media_type,
                    byte_size, analysis_status, current_extraction_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (dossier, source_ref) DO UPDATE SET
                    parent_project_id = EXCLUDED.parent_project_id,
                    source_digest = EXCLUDED.source_digest,
                    media_type = EXCLUDED.media_type,
                    byte_size = EXCLUDED.byte_size,
                    analysis_status = EXCLUDED.analysis_status,
                    current_extraction_id = EXCLUDED.current_extraction_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    document_id, contract.dossier, _parent_project_id(contract), source_ref,
                    sdigest, media_type,
                    path.stat().st_size, analysis_status, extraction_id,
                ),
            )
            _upsert_document_subject_tags(conn, document_id, subject_tags)
            _upsert_document_naming(conn, document_id, naming)
            _record_document_version(
                conn, document_id, source_ref, sdigest, media_type, path.stat().st_size
            )
            if reused_extraction_id is None:
                conn.execute(
                    """
                    INSERT INTO extraction_runs (
                        extraction_id, document_id, contract_id, contract_digest,
                        source_digest, converter, converter_version, config_digest,
                        status, markdown_content, document_json, chunk_count,
                        processing_time, quality_flags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                              %s, %s, %s::jsonb)
                    """,
                    (
                        extraction_id, document_id, contract.contract_id, cdigest,
                        sdigest, converted.converter, converted.converter_version,
                        converted.config_digest, converted.status, converted.markdown,
                        json.dumps(converted.document_json), len(compiled.chunks),
                        converted.processing_time, json.dumps(converted.quality_flags),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO extraction_observations (extraction_id, observation_kind)
                    VALUES (%s, %s)
                    """,
                    (extraction_id, observation_kind),
                )
            compilation_ref = _persist_compilation(
                conn,
                extraction_id=extraction_id,
                compiled=compiled,
            )
            conn.execute(
                """
                INSERT INTO document_extraction_bindings (
                    document_id, extraction_id, ingestion_id, cache_reused
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    extraction_id = EXCLUDED.extraction_id,
                    ingestion_id = EXCLUDED.ingestion_id,
                    cache_reused = EXCLUDED.cache_reused,
                    bound_at = CURRENT_TIMESTAMP
                """,
                (document_id, extraction_id, ingestion_id, reused_extraction_id is not None),
            )
            conn.execute(
                """
                INSERT INTO document_compilation_bindings (document_id, compilation_id)
                VALUES (%s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    compilation_id = EXCLUDED.compilation_id,
                    bound_at = CURRENT_TIMESTAMP
                """,
                (document_id, compilation_ref),
            )
            for i, projection in enumerate(compiled.chunks):
                body = projection.text
                conn.execute(
                    "INSERT INTO chunks"
                    " (dossier, source_ref, chunk_no, body, embedding,"
                    "  contract_id, contract_digest, ingestion_id, source_digest)"
                    " VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s)",
                    (
                        contract.dossier, source_ref, i, body,
                        to_pgvector(embed(body)), contract.contract_id, cdigest,
                        ingestion_id, sdigest,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO retrieval_chunk_projections (
                        dossier, source_ref, source_digest, chunk_no, compilation_id,
                        content_type, text_digest, page_start, page_end, structural_locator,
                        parent_heading, section_path, quality_flags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    """,
                    (
                        contract.dossier, source_ref, sdigest, i, compilation_ref,
                        projection.content_type, projection.text_digest,
                        projection.page_start, projection.page_end,
                        projection.structural_locator, projection.parent_heading,
                        json.dumps(projection.section_path),
                        json.dumps(projection.quality_flags),
                    ),
                )
                for member_order, ordinal in enumerate(projection.unit_ordinals):
                    conn.execute(
                        """
                        INSERT INTO retrieval_chunk_units (
                            dossier, source_ref, source_digest, chunk_no, unit_id, unit_order
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            contract.dossier, source_ref, sdigest, i,
                            unit_id(compilation_ref, ordinal), member_order,
                        ),
                    )
                total += 1
    return total


def intake_document(
    conn: psycopg.Connection,
    contract: TaskContract,
    root: Path,
    source_ref: str,
    *,
    ingestion_id: str | None = None,
    docling: DocumentConverter | None = None,
    subject_tags: list[str] | tuple[str, ...] | None = None,
) -> int:
    """Validate and incrementally ingest one explicitly declared NAS document."""
    assert_source_in_scope(contract, source_ref)
    naming = parse_document_name(source_ref)
    return ingest(
        conn,
        contract,
        root,
        ingestion_id=ingestion_id,
        docling=docling,
        source_refs=(source_ref,),
        naming_by_source={source_ref: naming},
        subject_tags_by_source=(
            {source_ref: subject_tags} if subject_tags is not None else None
        ),
    )


def get_document_card(conn: psycopg.Connection, dossier: str, source_ref: str) -> dict:
    """Return the bounded Project Document Card projection.

    The projection contains no duplicate source and no inferred authority. The
    dossier is the MVP's project parent; a future cockpit may resolve its human
    display name without changing this persistence contract.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.document_id, d.parent_project_id, d.source_ref, d.source_digest,
                   d.media_type, d.byte_size, d.analysis_status,
                   COALESCE(dc.subject_tags, '[]'::jsonb),
                   e.extraction_id, e.converter, e.converter_version,
                   e.quality_flags, COALESCE(sc.chunk_count, e.chunk_count),
                   e.error, e.finished_at,
                   o.observation_kind, b.cache_reused,
                   sc.compilation_id, sc.compiler, sc.compiler_version,
                   sc.status, sc.quality_flags, sc.diagnostics, sc.unit_count, sc.page_count,
                   sc.table_count, sc.anomaly_count,
                   (SELECT COUNT(*)
                      FROM chunks current_chunk
                     WHERE current_chunk.dossier = d.dossier
                       AND current_chunk.source_ref = d.source_ref
                       AND current_chunk.source_digest = d.source_digest),
                   (SELECT COUNT(*)
                      FROM retrieval_chunk_projections flagged_chunk
                     WHERE flagged_chunk.compilation_id = sc.compilation_id
                       AND jsonb_array_length(flagged_chunk.quality_flags) > 0),
                   n.project_code, n.revision_index, n.phase_code, n.phase_folder,
                   n.distributor, n.document_type, n.object_name, n.document_date,
                   n.extension
              FROM source_documents d
              LEFT JOIN document_classifications dc ON dc.document_id = d.document_id
              LEFT JOIN extraction_runs e ON e.extraction_id = d.current_extraction_id
              LEFT JOIN extraction_observations o ON o.extraction_id = e.extraction_id
              LEFT JOIN document_extraction_bindings b ON b.document_id = d.document_id
              LEFT JOIN document_compilation_bindings cb ON cb.document_id = d.document_id
              LEFT JOIN structured_compilations sc
                ON sc.compilation_id = cb.compilation_id
               AND sc.extraction_id = e.extraction_id
              LEFT JOIN document_naming n ON n.document_id = d.document_id
             WHERE d.dossier = %s AND d.source_ref = %s
            """,
            (dossier, source_ref),
        )
        row = cur.fetchone()
    if row is None:
        raise KeyError(f"unknown document source: {dossier}/{source_ref}")
    (
        document_id, parent_project_id, locator, source_digest, media_type,
        byte_size, analysis_status, subject_tags, extraction_id, converter,
        converter_version, quality_flags, chunk_count, error, finished_at,
        observation_kind, cache_reused,
        compilation_ref, compiler, compiler_version, compilation_status,
        compilation_flags, compilation_diagnostics, unit_count, page_count,
        table_count, anomaly_count, indexed_chunk_count, flagged_chunk_count,
        project_code, revision_index, phase_code, phase_folder, distributor,
        document_type, object_name, document_date, extension,
    ) = row
    combined_quality_flags = list(
        dict.fromkeys(
            [
                *(quality_flags or []),
                *(compilation_flags or []),
                *(["cache_reused"] if cache_reused else []),
            ]
        )
    )
    return {
        "card_type": "project_document",
        "card_id": f"card-{document_id}",
        "document_id": document_id,
        "parent_project_id": parent_project_id,
        "title": Path(locator).name,
        "source_ref": locator,
        "source_digest": source_digest,
        "media_type": media_type,
        "byte_size": byte_size,
        "analysis_status": analysis_status,
        "subject_tags": list(subject_tags or []),
        "naming": {
            "project_code": project_code,
            "revision_index": revision_index,
            "phase_code": phase_code,
            "phase_folder": phase_folder,
            "distributor": distributor,
            "document_type": document_type,
            "object_name": object_name,
            "document_date": document_date.isoformat() if document_date else None,
            "extension": extension,
            "validated": project_code is not None,
        },
        "extraction": {
            "extraction_id": extraction_id,
            "converter": converter,
            "converter_version": converter_version,
            "observation_kind": observation_kind,
            "quality_flags": combined_quality_flags,
            "chunk_count": chunk_count or 0,
            "chunk_refs": [
                chunk_ref(compilation_ref, number) for number in range(chunk_count or 0)
            ] if compilation_ref else [],
            "error": error,
            "finished_at": finished_at.isoformat() if finished_at else None,
        },
        "structured_extraction": {
            "compilation_id": compilation_ref,
            "compiler": compiler,
            "compiler_version": compiler_version,
            "status": compilation_status,
            "quality_flags": list(compilation_flags or []),
            "diagnostics": list(compilation_diagnostics or []),
            "unit_count": unit_count or 0,
            "page_count": page_count or 0,
            "table_count": table_count or 0,
            "anomaly_count": anomaly_count or 0,
        },
        "chunk_summary": {
            "total": chunk_count or 0,
            "indexed": indexed_chunk_count or 0,
            "with_quality_flags": flagged_chunk_count or 0,
            "verification_status": "not_observed",
        },
        "authority": {
            "is_source": False,
            "is_evidence": False,
            "is_memory": False,
        },
    }


def list_document_cards(conn: psycopg.Connection, parent_project_id: str) -> list[dict]:
    """List stable card projections for one project parent, newest first."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT dossier, source_ref
              FROM source_documents
             WHERE parent_project_id = %s
             ORDER BY updated_at DESC, source_ref ASC
            """,
            (parent_project_id,),
        )
        locators = cur.fetchall()
    return [get_document_card(conn, dossier, source_ref) for dossier, source_ref in locators]


def get_document_card_by_id(conn: psycopg.Connection, document_id: str) -> dict:
    """Resolve a card by its stable document identity."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT dossier, source_ref FROM source_documents WHERE document_id = %s",
            (document_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise KeyError(f"unknown document: {document_id}")
    return get_document_card(conn, row[0], row[1])


def get_document_markdown(conn: psycopg.Connection, document_id: str) -> str:
    """Return the current derived Markdown representation, never the original."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.markdown_content
              FROM source_documents d
              JOIN extraction_runs e ON e.extraction_id = d.current_extraction_id
             WHERE d.document_id = %s
            """,
            (document_id,),
        )
        row = cur.fetchone()
    if row is None or row[0] is None:
        raise KeyError(f"no Markdown representation for document: {document_id}")
    return row[0]


def get_document_source(conn: psycopg.Connection, document_id: str) -> tuple[str, str]:
    """Return the dossier and bounded relative source locator for preview delivery."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT dossier, source_ref FROM source_documents WHERE document_id = %s",
            (document_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise KeyError(f"unknown document: {document_id}")
    return row[0], row[1]


def get_document_chunks(
    conn: psycopg.Connection,
    document_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
    content_type: str | None = None,
    flagged_only: bool = False,
) -> dict:
    """Inspect current derived retrieval chunks without assigning them truth.

    Similarity is deliberately absent: it exists only inside a particular
    retrieval trace, never as an intrinsic quality score for a chunk.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.dossier, d.source_ref, d.source_digest, cb.compilation_id
              FROM source_documents d
              JOIN document_compilation_bindings cb ON cb.document_id = d.document_id
             WHERE d.document_id = %s
            """,
            (document_id,),
        )
        document = cur.fetchone()
    if document is None:
        raise KeyError(f"unknown compiled document: {document_id}")

    dossier, source_ref, source_digest, compilation_ref = document
    predicates = [
        "c.dossier = %s",
        "c.source_ref = %s",
        "c.source_digest = %s",
        "p.compilation_id = %s",
    ]
    params: list[object] = [dossier, source_ref, source_digest, compilation_ref]
    if content_type:
        predicates.append("p.content_type = %s")
        params.append(content_type)
    if flagged_only:
        predicates.append("jsonb_array_length(p.quality_flags) > 0")
    where = " AND ".join(predicates)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(*)
              FROM chunks c
              JOIN retrieval_chunk_projections p
                ON p.dossier = c.dossier
               AND p.source_ref = c.source_ref
               AND p.source_digest = c.source_digest
               AND p.chunk_no = c.chunk_no
             WHERE {where}
            """,
            params,
        )
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT c.chunk_no, c.body, p.content_type, p.page_start, p.page_end,
                   p.structural_locator, p.parent_heading,
                   COALESCE(p.section_path, '[]'::jsonb),
                   COALESCE(p.quality_flags, '[]'::jsonb)
              FROM chunks c
              JOIN retrieval_chunk_projections p
                ON p.dossier = c.dossier
               AND p.source_ref = c.source_ref
               AND p.source_digest = c.source_digest
               AND p.chunk_no = c.chunk_no
             WHERE {where}
             ORDER BY c.chunk_no
             LIMIT %s OFFSET %s
            """,
            [*params, limit, offset],
        )
        rows = cur.fetchall()

    return {
        "document_id": document_id,
        "compilation_id": compilation_ref,
        "total": total,
        "limit": limit,
        "offset": offset,
        "score_context": "retrieval_query_required",
        "chunks": [
            {
                "chunk_ref": f"chunk.{compilation_ref}.{chunk_no:04d}",
                "ordinal": chunk_no,
                "body": body,
                "content_type": chunk_type,
                "page_start": page_start,
                "page_end": page_end,
                "structural_locator": locator,
                "parent_heading": parent_heading,
                "section_path": list(section_path or []),
                "quality_flags": list(quality_flags or []),
                "retrieval_status": "indexed",
                "verification_status": "not_observed",
            }
            for (
                chunk_no, body, chunk_type, page_start, page_end, locator,
                parent_heading, section_path, quality_flags,
            ) in rows
        ],
    }


def retrieve_scoped(
    conn: psycopg.Connection,
    contract: TaskContract,
    query: str,
    top_k: int = 4,
) -> list[RetrievedChunk]:
    """Scope current source versions in SQL first, then vector-rank them."""
    qvec = to_pgvector(embed(query))
    with conn.cursor() as cur:
        cur.execute(
            "SELECT c.source_ref, c.chunk_no, c.body, c.embedding <=> %s::vector AS distance,"
            "       c.contract_id, c.contract_digest, c.ingestion_id, c.source_digest,"
            "       COALESCE(p.content_type, ''), p.page_start, p.page_end,"
            "       COALESCE(p.structural_locator, ''), p.parent_heading,"
            "       COALESCE(p.section_path, '[]'::jsonb),"
            "       COALESCE(p.quality_flags, '[]'::jsonb)"
            " FROM chunks c"
            " JOIN source_documents d"
            "   ON d.dossier = c.dossier AND d.source_ref = c.source_ref"
            "  AND d.source_digest = c.source_digest"
            " LEFT JOIN retrieval_chunk_projections p"
            "   ON p.dossier = c.dossier AND p.source_ref = c.source_ref"
            "  AND p.source_digest = c.source_digest AND p.chunk_no = c.chunk_no"
            " WHERE c.dossier = %s AND c.source_ref = ANY(%s)"
            " ORDER BY distance ASC, c.source_ref ASC, c.source_digest ASC,"
            "          c.chunk_no ASC"
            " LIMIT %s",
            (qvec, contract.dossier, list(contract.sources), top_k),
        )
        return [
            RetrievedChunk(
                *row[:-2],
                section_path=tuple(row[-2] or ()),
                quality_flags=tuple(row[-1] or ()),
            )
            for row in cur.fetchall()
        ]


def retrieve_exact_scoped(
    conn: psycopg.Connection,
    contract: TaskContract,
    query: str,
    *,
    sources: tuple[tuple[str, str], ...],
    top_k: int = 4,
) -> list[RetrievedChunk]:
    """Vector-rank only exact ``(source_ref, source_digest)`` identities.

    Exact identities may point at a preserved historical digest, but each path
    must still already belong to the Task Contract perimeter. An unknown digest
    yields no candidates; it never falls forward to the current path content.
    """
    if top_k < 1 or top_k > 100:
        raise ValueError("top_k must be between 1 and 100")
    if not sources:
        return []

    source_refs: list[str] = []
    source_digests: list[str] = []
    seen: set[tuple[str, str]] = set()
    for source_ref, source_digest in sources:
        assert_source_in_scope(contract, source_ref)
        digest = str(source_digest or "").strip()
        if not digest:
            raise ValueError("exact retrieval source_digest is required")
        key = (source_ref, digest)
        if key in seen:
            continue
        seen.add(key)
        source_refs.append(source_ref)
        source_digests.append(digest)

    qvec = to_pgvector(embed(query))
    with conn.cursor() as cur:
        cur.execute(
            "WITH allowed AS ("
            " SELECT * FROM unnest(%s::text[], %s::text[])"
            " AS exact_source(source_ref, source_digest)"
            ")"
            " SELECT c.source_ref, c.chunk_no, c.body, c.embedding <=> %s::vector AS distance,"
            "        c.contract_id, c.contract_digest, c.ingestion_id, c.source_digest,"
            "        COALESCE(p.content_type, ''), p.page_start, p.page_end,"
            "        COALESCE(p.structural_locator, ''), p.parent_heading,"
            "        COALESCE(p.section_path, '[]'::jsonb),"
            "        COALESCE(p.quality_flags, '[]'::jsonb)"
            " FROM chunks c"
            " JOIN allowed a"
            "   ON a.source_ref = c.source_ref AND a.source_digest = c.source_digest"
            " LEFT JOIN retrieval_chunk_projections p"
            "   ON p.dossier = c.dossier AND p.source_ref = c.source_ref"
            "  AND p.source_digest = c.source_digest AND p.chunk_no = c.chunk_no"
            " WHERE c.dossier = %s"
            " ORDER BY distance ASC, c.source_ref ASC, c.source_digest ASC,"
            "          c.chunk_no ASC"
            " LIMIT %s",
            (source_refs, source_digests, qvec, contract.dossier, top_k),
        )
        return [
            RetrievedChunk(
                *row[:-2],
                section_path=tuple(row[-2] or ()),
                quality_flags=tuple(row[-1] or ()),
            )
            for row in cur.fetchall()
        ]
