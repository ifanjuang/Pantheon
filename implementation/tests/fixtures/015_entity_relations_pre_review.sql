-- Canonical explicit relations keyed by two EntityRef values.
-- The physical shape is generic; the first admitted endpoint type is Information.

CREATE TABLE IF NOT EXISTS agency_entity_relations (
    relation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    from_entity_type TEXT NOT NULL CHECK (from_entity_type IN ('information')),
    from_entity_id TEXT NOT NULL,
    to_entity_type TEXT NOT NULL CHECK (to_entity_type IN ('information')),
    to_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN ('responds_to', 'relies_on', 'supersedes', 'contradicts')
    ),
    rationale TEXT,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_refs) = 'array'),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    retired_at TIMESTAMPTZ,
    retired_by TEXT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision IN (1, 2)),
    CHECK (
        from_entity_type <> to_entity_type
        OR from_entity_id <> to_entity_id
    ),
    CHECK (
        (retired_at IS NULL AND retired_by IS NULL AND revision = 1)
        OR (retired_at IS NOT NULL AND retired_by IS NOT NULL AND revision = 2)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS agency_entity_relations_active_edge_unique
    ON agency_entity_relations (
        project_id,
        from_entity_type,
        from_entity_id,
        relation_type,
        to_entity_type,
        to_entity_id
    )
    WHERE retired_at IS NULL;

CREATE INDEX IF NOT EXISTS agency_entity_relations_project_lookup
    ON agency_entity_relations (project_id, created_at, relation_id);
CREATE INDEX IF NOT EXISTS agency_entity_relations_from_lookup
    ON agency_entity_relations (from_entity_type, from_entity_id, retired_at);
CREATE INDEX IF NOT EXISTS agency_entity_relations_to_lookup
    ON agency_entity_relations (to_entity_type, to_entity_id, retired_at);

CREATE OR REPLACE FUNCTION resolve_agency_entity_relation_project(
    target_entity_type TEXT,
    target_entity_id TEXT
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    resolved_project_id TEXT;
BEGIN
    CASE target_entity_type
        WHEN 'information' THEN
            SELECT project_id
              INTO resolved_project_id
              FROM agency_information_cards
             WHERE information_id = target_entity_id;
        ELSE
            RAISE EXCEPTION 'unsupported EntityRef type: %', target_entity_type;
    END CASE;

    IF resolved_project_id IS NULL THEN
        RAISE EXCEPTION 'unknown % EntityRef: %', target_entity_type, target_entity_id;
    END IF;
    RETURN resolved_project_id;
END;
$$;

CREATE OR REPLACE FUNCTION enforce_agency_entity_relation_scope()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    from_project_id TEXT;
    to_project_id TEXT;
BEGIN
    from_project_id := resolve_agency_entity_relation_project(
        NEW.from_entity_type, NEW.from_entity_id
    );
    to_project_id := resolve_agency_entity_relation_project(
        NEW.to_entity_type, NEW.to_entity_id
    );

    IF from_project_id <> to_project_id THEN
        RAISE EXCEPTION 'Entity relation endpoints belong to different Projects';
    END IF;
    IF NEW.project_id <> from_project_id THEN
        RAISE EXCEPTION 'Entity relation project does not match endpoint Project';
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF OLD.relation_id <> NEW.relation_id
           OR OLD.project_id <> NEW.project_id
           OR OLD.from_entity_type <> NEW.from_entity_type
           OR OLD.from_entity_id <> NEW.from_entity_id
           OR OLD.to_entity_type <> NEW.to_entity_type
           OR OLD.to_entity_id <> NEW.to_entity_id
           OR OLD.relation_type <> NEW.relation_type
           OR OLD.rationale IS DISTINCT FROM NEW.rationale
           OR OLD.source_refs IS DISTINCT FROM NEW.source_refs
           OR OLD.created_by <> NEW.created_by
           OR OLD.created_at <> NEW.created_at THEN
            RAISE EXCEPTION 'Entity relation identity and meaning are immutable';
        END IF;
        IF OLD.retired_at IS NOT NULL
           OR NEW.retired_at IS NULL
           OR NEW.retired_by IS NULL
           OR NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'Entity relation update must be one active-to-retired transition';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relations_scope_guard'
           AND tgrelid = 'agency_entity_relations'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relations_scope_guard
        BEFORE INSERT OR UPDATE ON agency_entity_relations
        FOR EACH ROW EXECUTE FUNCTION enforce_agency_entity_relation_scope();
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION reject_agency_entity_relation_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Entity relations are retained; retire instead of deleting';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relations_no_delete'
           AND tgrelid = 'agency_entity_relations'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relations_no_delete
        BEFORE DELETE ON agency_entity_relations
        FOR EACH ROW EXECUTE FUNCTION reject_agency_entity_relation_delete();
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS agency_entity_relation_events (
    event_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL REFERENCES agency_entity_relations(relation_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('relation_created', 'relation_retired')),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind = 'human'),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS agency_entity_relation_events_relation_lookup
    ON agency_entity_relation_events (relation_id, occurred_at, event_id);

CREATE OR REPLACE FUNCTION reject_agency_entity_relation_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Entity relation events are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relation_events_no_update'
           AND tgrelid = 'agency_entity_relation_events'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relation_events_no_update
        BEFORE UPDATE ON agency_entity_relation_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_entity_relation_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relation_events_no_delete'
           AND tgrelid = 'agency_entity_relation_events'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relation_events_no_delete
        BEFORE DELETE ON agency_entity_relation_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_entity_relation_event_mutation();
    END IF;
END;
$$;
