CREATE TABLE IF NOT EXISTS agency_information_projection_metadata (
    information_id TEXT PRIMARY KEY REFERENCES agency_information_cards(information_id) ON DELETE CASCADE,
    source_date DATE,
    received_at TIMESTAMPTZ,
    issued_at TIMESTAMPTZ,
    media_types JSONB NOT NULL DEFAULT '["text"]'::jsonb,
    contact_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agency_information_document_links (
    information_id TEXT NOT NULL REFERENCES agency_information_cards(information_id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON DELETE RESTRICT,
    role TEXT NOT NULL CHECK (role IN ('primary', 'supporting', 'attachment')),
    observed_version INTEGER CHECK (observed_version IS NULL OR observed_version >= 1),
    observed_digest TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (information_id, document_id)
);

CREATE INDEX IF NOT EXISTS agency_information_document_links_document_lookup
    ON agency_information_document_links (document_id, information_id);

CREATE OR REPLACE FUNCTION enforce_agency_information_document_same_project()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    information_project_id TEXT;
    document_project_id TEXT;
BEGIN
    SELECT project_id
      INTO information_project_id
      FROM agency_information_cards
     WHERE information_id = NEW.information_id;

    SELECT parent_project_id
      INTO document_project_id
      FROM source_documents
     WHERE document_id = NEW.document_id;

    IF information_project_id IS DISTINCT FROM document_project_id THEN
        RAISE EXCEPTION 'Information and Document must belong to the same project';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agency_information_document_links_same_project
    ON agency_information_document_links;
CREATE TRIGGER agency_information_document_links_same_project
BEFORE INSERT OR UPDATE ON agency_information_document_links
FOR EACH ROW EXECUTE FUNCTION enforce_agency_information_document_same_project();

CREATE TABLE IF NOT EXISTS agency_information_projection_events (
    event_id TEXT PRIMARY KEY,
    information_id TEXT NOT NULL REFERENCES agency_information_cards(information_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('projection_metadata_updated', 'document_link_added', 'document_link_updated', 'document_link_removed')),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'system')),
    expected_revision INTEGER NOT NULL CHECK (expected_revision >= 0),
    resulting_revision INTEGER NOT NULL CHECK (resulting_revision = expected_revision + 1),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION reject_agency_information_projection_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'agency_information_projection_events is append-only';
END;
$$;

DROP TRIGGER IF EXISTS agency_information_projection_events_no_update ON agency_information_projection_events;
CREATE TRIGGER agency_information_projection_events_no_update
BEFORE UPDATE ON agency_information_projection_events
FOR EACH ROW EXECUTE FUNCTION reject_agency_information_projection_event_mutation();

DROP TRIGGER IF EXISTS agency_information_projection_events_no_delete ON agency_information_projection_events;
CREATE TRIGGER agency_information_projection_events_no_delete
BEFORE DELETE ON agency_information_projection_events
FOR EACH ROW EXECUTE FUNCTION reject_agency_information_projection_event_mutation();
-- `add_document_link` upserts, so a call that changes an existing link's role or
-- observed version is a modification, not an addition. The event log recorded it
-- as `document_link_added` either way, which made the append-only history
-- describe a link creation that never happened. Widen the closed vocabulary for
-- databases created before the distinction existed. Guarded on the value this
-- adds, so a started-up installation performs a catalog read only.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'agency_information_projection_events_event_type_check'
           AND conrelid = 'agency_information_projection_events'::regclass
           AND pg_get_constraintdef(oid) LIKE $marker$%'document_link_updated'%$marker$
    ) THEN
        ALTER TABLE agency_information_projection_events
            DROP CONSTRAINT IF EXISTS agency_information_projection_events_event_type_check;
        ALTER TABLE agency_information_projection_events
            ADD CONSTRAINT agency_information_projection_events_event_type_check
            CHECK (event_type IN (
                'projection_metadata_updated', 'document_link_added',
                'document_link_updated', 'document_link_removed'
            )) NOT VALID;
    END IF;
END;
$$;

-- CURRENT_TIMESTAMP is the transaction start time, so two events written in one
-- transaction share an occurred_at and cannot be ordered by it. clock_timestamp()
-- advances per statement. 014_knowledge_edit_variants.sql already applies this to
-- its own append-only log; the other event tables still carry CURRENT_TIMESTAMP
-- and are left for a coordinated pass.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_information_projection_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE agency_information_projection_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
