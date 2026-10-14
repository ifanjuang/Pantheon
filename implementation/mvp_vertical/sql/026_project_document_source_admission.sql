-- A2: immutable provenance binding from a preserved generic Source to an exact
-- professional Project Document revision.
--
-- This does not move or upload bytes. agency_sources keeps Source admission,
-- source_documents/document_versions keep technical capture history, and
-- doc_document_versions keeps professional revision identity.

CREATE TABLE IF NOT EXISTS doc_document_version_sources (
    source_id TEXT PRIMARY KEY REFERENCES agency_sources(source_id) ON DELETE RESTRICT,
    document_version_id TEXT NOT NULL REFERENCES doc_document_versions(version_id) ON DELETE RESTRICT,
    source_revision INTEGER NOT NULL CHECK (source_revision > 0),
    source_digest TEXT NOT NULL CHECK (btrim(source_digest) <> ''),
    source_checksum TEXT,
    source_raw_ref TEXT NOT NULL CHECK (btrim(source_raw_ref) <> ''),
    origin_system TEXT NOT NULL CHECK (btrim(origin_system) <> ''),
    origin_external_ref TEXT NOT NULL CHECK (btrim(origin_external_ref) <> ''),
    reconciliation_basis TEXT NOT NULL CHECK (
        reconciliation_basis IN ('checksum', 'exact_reference')
    ),
    admitted_by TEXT NOT NULL CHECK (btrim(admitted_by) <> ''),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL CHECK (btrim(payload_digest) <> ''),
    result_snapshot JSONB NOT NULL,
    admitted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS doc_document_version_sources_revision_lookup
    ON doc_document_version_sources (document_version_id, admitted_at, source_id);

CREATE OR REPLACE FUNCTION reject_doc_document_version_source_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'doc_document_version_sources is append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'doc_document_version_sources_append_only'
           AND tgrelid = 'doc_document_version_sources'::regclass
    ) THEN
        CREATE TRIGGER doc_document_version_sources_append_only
        BEFORE UPDATE OR DELETE ON doc_document_version_sources
        FOR EACH ROW EXECUTE FUNCTION reject_doc_document_version_source_mutation();
    END IF;
END;
$$;

COMMENT ON TABLE doc_document_version_sources IS
    'Immutable admission provenance from a preserved generic Source to one exact professional document revision; binding success is not review, Evidence, approval or current authority.';