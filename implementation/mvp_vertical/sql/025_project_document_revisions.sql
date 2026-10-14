-- Additive professional Project Document identity/revision owner.
--
-- Existing source_documents + document_versions remain the technical source
-- history used by ingestion/extraction. These tables add only a professional
-- grouping layer above exact technical captures. No existing source is grouped
-- automatically and no revision becomes approved, contractual or authoritative
-- merely because it is persisted here.

CREATE TABLE IF NOT EXISTS doc_documents (
    document_id TEXT PRIMARY KEY,
    parent_project_id TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (btrim(document_type) <> ''),
    title TEXT NOT NULL CHECK (btrim(title) <> ''),
    lot_id TEXT,
    discipline_code TEXT,
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS doc_documents_project_lookup
    ON doc_documents (parent_project_id, document_type, lower(title), document_id);

CREATE TABLE IF NOT EXISTS doc_document_versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES doc_documents(document_id) ON DELETE RESTRICT,
    version_seq INTEGER NOT NULL CHECK (version_seq > 0),
    revision_label TEXT,
    source_document_id TEXT NOT NULL,
    source_version INTEGER NOT NULL CHECK (source_version > 0),
    source_ref TEXT NOT NULL,
    source_digest TEXT NOT NULL CHECK (btrim(source_digest) <> ''),
    media_type TEXT NOT NULL CHECK (btrim(media_type) <> ''),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    received_at TIMESTAMPTZ NOT NULL,
    supersedes_version_id TEXT REFERENCES doc_document_versions(version_id) ON DELETE RESTRICT,
    linked_by TEXT NOT NULL CHECK (btrim(linked_by) <> ''),
    linked_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (document_id, version_seq),
    UNIQUE (document_id, source_digest),
    FOREIGN KEY (source_document_id, source_version)
        REFERENCES document_versions(document_id, version) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS doc_document_versions_received_lookup
    ON doc_document_versions (document_id, received_at DESC, version_seq DESC);
CREATE INDEX IF NOT EXISTS doc_document_versions_source_lookup
    ON doc_document_versions (source_document_id, source_version);

CREATE TABLE IF NOT EXISTS doc_document_events (
    event_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES doc_documents(document_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('document_created', 'revision_linked')),
    actor TEXT NOT NULL CHECK (btrim(actor) <> ''),
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'system')),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL CHECK (btrim(payload_digest) <> ''),
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS doc_document_events_document_lookup
    ON doc_document_events (document_id, occurred_at, event_id);

CREATE OR REPLACE FUNCTION reject_doc_document_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'doc_document_events is append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'doc_document_events_append_only'
           AND tgrelid = 'doc_document_events'::regclass
    ) THEN
        CREATE TRIGGER doc_document_events_append_only
        BEFORE UPDATE OR DELETE ON doc_document_events
        FOR EACH ROW EXECUTE FUNCTION reject_doc_document_event_mutation();
    END IF;
END;
$$;

COMMENT ON TABLE doc_documents IS
    'Stable professional Project Document identities; persistence does not confer Evidence, approval, contractual or execution authority.';
COMMENT ON TABLE doc_document_versions IS
    'Professional revision links to exact technical document_versions captures; version_seq is internal order and revision_label remains external vocabulary.';
COMMENT ON TABLE doc_document_events IS
    'Append-only provenance for logical document creation and revision linking; event success is not professional validation.';
