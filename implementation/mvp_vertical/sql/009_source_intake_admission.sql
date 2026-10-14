CREATE TABLE IF NOT EXISTS agency_sources (
    source_id TEXT PRIMARY KEY
        CONSTRAINT agency_sources_source_id_shape_check
        CHECK (source_id ~ '^[a-z0-9._-]+$'),
    source_kind TEXT NOT NULL CHECK (source_kind IN (
        'email', 'document', 'image', 'audio', 'video', 'model',
        'url', 'text', 'archive', 'event', 'other'
    )),
    origin_system TEXT NOT NULL,
    origin_external_ref TEXT NOT NULL,
    origin_producer TEXT,
    received_by TEXT,
    raw_source_ref TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    project_link_status TEXT NOT NULL CHECK (
        project_link_status IN ('unassigned', 'suggested', 'linked', 'excluded')
    ),
    project_id TEXT REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    declared_project_name TEXT,
    candidate_project_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_date TIMESTAMPTZ,
    mime_type TEXT,
    checksum TEXT CHECK (checksum IS NULL OR checksum ~ '^[A-Fa-f0-9]{64}$'),
    confidentiality TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (project_link_status = 'linked' AND project_id IS NOT NULL)
        OR (project_link_status <> 'linked' AND project_id IS NULL)
    ),
    CHECK (
        project_link_status <> 'suggested'
        OR jsonb_array_length(candidate_project_refs) > 0
    ),
    UNIQUE (origin_system, origin_external_ref)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'agency_sources_source_id_shape_check'
           AND conrelid = 'agency_sources'::regclass
    ) THEN
        ALTER TABLE agency_sources
            ADD CONSTRAINT agency_sources_source_id_shape_check
            CHECK (source_id ~ '^[a-z0-9._-]+$') NOT VALID;
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS agency_sources_project_lookup
    ON agency_sources (project_id, received_at DESC);
CREATE INDEX IF NOT EXISTS agency_sources_status_lookup
    ON agency_sources (project_link_status, received_at DESC);
CREATE INDEX IF NOT EXISTS agency_sources_declared_project_lookup
    ON agency_sources (lower(declared_project_name))
    WHERE declared_project_name IS NOT NULL;

CREATE TABLE IF NOT EXISTS agency_source_relations (
    relation_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES agency_sources(source_id) ON DELETE RESTRICT,
    target_source_id TEXT NOT NULL REFERENCES agency_sources(source_id) ON DELETE RESTRICT,
    relation_type TEXT NOT NULL CHECK (relation_type = 'contains'),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (source_id <> target_source_id),
    UNIQUE (source_id, target_source_id, relation_type)
);

CREATE TABLE IF NOT EXISTS agency_source_events (
    event_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES agency_sources(source_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'source_created',
        'metadata_updated',
        'project_links_suggested',
        'project_linked',
        'project_unlinked',
        'source_excluded',
        'source_restored',
        'source_relation_created'
    )),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'hermes', 'system')),
    expected_revision INTEGER NOT NULL CHECK (expected_revision >= 0),
    resulting_revision INTEGER NOT NULL CHECK (resulting_revision >= expected_revision),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION reject_agency_source_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'agency_source_events is append-only';
END;
$$;

DROP TRIGGER IF EXISTS agency_source_events_reject_update ON agency_source_events;
CREATE TRIGGER agency_source_events_reject_update
BEFORE UPDATE ON agency_source_events
FOR EACH ROW EXECUTE FUNCTION reject_agency_source_event_mutation();

DROP TRIGGER IF EXISTS agency_source_events_reject_delete ON agency_source_events;
CREATE TRIGGER agency_source_events_reject_delete
BEFORE DELETE ON agency_source_events
FOR EACH ROW EXECUTE FUNCTION reject_agency_source_event_mutation();

-- CURRENT_TIMESTAMP is the transaction start time, so events written in one
-- transaction share an occurred_at and cannot be ordered by it. clock_timestamp()
-- advances per statement. Applied here for the same reason as in 001_work_issues,
-- where the defect is demonstrated: no path in this file writes two events at once
-- today, and the point is that adding one must not silently lose their order.
-- Guarded on the value this adds, so a started-up installation performs a catalog
-- read only.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_source_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE agency_source_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
