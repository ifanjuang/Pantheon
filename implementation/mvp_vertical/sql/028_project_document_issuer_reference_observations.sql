-- A6: append-only observations of external issuer document references.
--
-- The canonical semantic field is issuer_document_reference on the projected
-- professional revision. This journal is only implementation provenance: it
-- permits late observations and explicit conflicts without rewriting A1/A2
-- revision history.

CREATE TABLE IF NOT EXISTS doc_document_version_reference_observations (
    observation_id TEXT PRIMARY KEY,
    document_version_id TEXT NOT NULL REFERENCES doc_document_versions(version_id) ON DELETE RESTRICT,
    reference_value TEXT NOT NULL CHECK (btrim(reference_value) <> ''),
    basis_kind TEXT NOT NULL CHECK (
        basis_kind IN ('human_declared', 'source_observed', 'import_metadata')
    ),
    basis_ref TEXT,
    observed_by TEXT NOT NULL CHECK (btrim(observed_by) <> ''),
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'system')),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL CHECK (btrim(payload_digest) <> ''),
    result_snapshot JSONB NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS doc_document_version_reference_observations_version_lookup
    ON doc_document_version_reference_observations (
        document_version_id, observed_at, observation_id
    );

CREATE OR REPLACE FUNCTION reject_doc_document_version_reference_observation_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'doc_document_version_reference_observations is append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'doc_document_version_reference_observations_append_only'
           AND tgrelid = 'doc_document_version_reference_observations'::regclass
    ) THEN
        CREATE TRIGGER doc_document_version_reference_observations_append_only
        BEFORE UPDATE OR DELETE ON doc_document_version_reference_observations
        FOR EACH ROW EXECUTE FUNCTION reject_doc_document_version_reference_observation_mutation();
    END IF;
END;
$$;

COMMENT ON TABLE doc_document_version_reference_observations IS
    'Append-only provenance observations for opaque issuer document references on exact professional revisions; observations do not establish approval, Evidence, chronology or authority.';