-- WorkIssue scopes project one task identity into several user contexts.
-- They are aggregate-owned scope links, not semantic Entity Relations and not
-- runtime authorization material.

CREATE TABLE IF NOT EXISTS work_issue_scope_links (
    scope_link_id TEXT PRIMARY KEY CHECK (scope_link_id ~ '^[a-z0-9][a-z0-9._-]*$'),
    issue_id TEXT NOT NULL REFERENCES work_issues(issue_id) ON DELETE RESTRICT,
    entity_type TEXT NOT NULL CHECK (
        entity_type IN (
            'agency', 'project', 'information', 'decision',
            'person', 'organization', 'apu_object'
        )
    ),
    entity_id TEXT NOT NULL CHECK (entity_id ~ '^[a-z0-9][a-z0-9._-]*$'),
    scope_role TEXT NOT NULL CHECK (scope_role IN ('primary', 'related')),
    rationale TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    retired_at TIMESTAMPTZ,
    retired_by TEXT,
    CHECK (
        (retired_at IS NULL AND retired_by IS NULL)
        OR (retired_at IS NOT NULL AND retired_by IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS work_issue_scope_active_entity_unique
    ON work_issue_scope_links (issue_id, entity_type, entity_id)
    WHERE retired_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS work_issue_scope_one_active_primary
    ON work_issue_scope_links (issue_id)
    WHERE retired_at IS NULL AND scope_role = 'primary';

CREATE INDEX IF NOT EXISTS work_issue_scope_entity_lookup
    ON work_issue_scope_links (entity_type, entity_id, retired_at, created_at DESC);

CREATE INDEX IF NOT EXISTS work_issue_scope_issue_lookup
    ON work_issue_scope_links (issue_id, retired_at, scope_role, created_at);

CREATE TABLE IF NOT EXISTS work_issue_scope_events (
    event_id TEXT PRIMARY KEY,
    issue_id TEXT NOT NULL REFERENCES work_issues(issue_id) ON DELETE RESTRICT,
    scope_link_id TEXT NOT NULL REFERENCES work_issue_scope_links(scope_link_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('scope_linked', 'scope_retired', 'primary_scope_replaced')
    ),
    actor TEXT NOT NULL,
    expected_version INTEGER NOT NULL CHECK (expected_version >= 1),
    resulting_version INTEGER NOT NULL CHECK (resulting_version = expected_version + 1),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS work_issue_scope_events_issue_lookup
    ON work_issue_scope_events (issue_id, occurred_at, event_id);

CREATE OR REPLACE FUNCTION work_issue_scope_endpoint_exists(
    candidate_type TEXT,
    candidate_id TEXT
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    found boolean := false;
BEGIN
    CASE candidate_type
        WHEN 'agency' THEN
            found := candidate_id <> '';
        WHEN 'project' THEN
            SELECT EXISTS(
                SELECT 1 FROM agency_projects WHERE project_id = candidate_id
            ) INTO found;
        WHEN 'information' THEN
            SELECT EXISTS(
                SELECT 1 FROM agency_information_cards WHERE information_id = candidate_id
            ) INTO found;
        WHEN 'person' THEN
            SELECT EXISTS(
                SELECT 1 FROM agency_people WHERE person_id = candidate_id
            ) INTO found;
        WHEN 'organization' THEN
            SELECT EXISTS(
                SELECT 1 FROM agency_organizations WHERE organization_id = candidate_id
            ) INTO found;
        WHEN 'decision' THEN
            IF to_regclass('agency_decision_records') IS NULL THEN
                RAISE EXCEPTION 'WorkIssue scope owner is not implemented: decision';
            END IF;
            EXECUTE 'SELECT EXISTS (SELECT 1 FROM agency_decision_records WHERE decision_id = $1)'
                INTO found USING candidate_id;
        WHEN 'apu_object' THEN
            IF to_regclass('agency_apu_objects') IS NULL THEN
                RAISE EXCEPTION 'WorkIssue scope owner is not implemented: apu_object';
            END IF;
            EXECUTE 'SELECT EXISTS (SELECT 1 FROM agency_apu_objects WHERE object_id = $1)'
                INTO found USING candidate_id;
        ELSE
            found := false;
    END CASE;
    RETURN found;
END;
$$;

CREATE OR REPLACE FUNCTION validate_work_issue_scope_endpoint()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT work_issue_scope_endpoint_exists(NEW.entity_type, NEW.entity_id) THEN
        RAISE EXCEPTION 'unknown WorkIssue scope endpoint: %:%', NEW.entity_type, NEW.entity_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION guard_work_issue_scope_link_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'WorkIssue scope links are retained; retire instead of deleting';
    END IF;

    IF OLD.issue_id IS DISTINCT FROM NEW.issue_id
       OR OLD.entity_type IS DISTINCT FROM NEW.entity_type
       OR OLD.entity_id IS DISTINCT FROM NEW.entity_id
       OR OLD.scope_role IS DISTINCT FROM NEW.scope_role
       OR OLD.rationale IS DISTINCT FROM NEW.rationale
       OR OLD.created_by IS DISTINCT FROM NEW.created_by
       OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION 'WorkIssue scope meaning is immutable';
    END IF;

    IF OLD.retired_at IS NOT NULL THEN
        RAISE EXCEPTION 'retired WorkIssue scope links are immutable';
    END IF;

    IF NEW.retired_at IS NULL OR NEW.retired_by IS NULL THEN
        RAISE EXCEPTION 'WorkIssue scope update may only retire the link';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION reject_work_issue_scope_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'work_issue_scope_events are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'work_issue_scope_endpoint_guard'
          AND tgrelid = 'work_issue_scope_links'::regclass
    ) THEN
        CREATE TRIGGER work_issue_scope_endpoint_guard
        BEFORE INSERT ON work_issue_scope_links
        FOR EACH ROW EXECUTE FUNCTION validate_work_issue_scope_endpoint();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'work_issue_scope_links_no_delete'
          AND tgrelid = 'work_issue_scope_links'::regclass
    ) THEN
        CREATE TRIGGER work_issue_scope_links_no_delete
        BEFORE DELETE ON work_issue_scope_links
        FOR EACH ROW EXECUTE FUNCTION guard_work_issue_scope_link_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'work_issue_scope_links_retire_only'
          AND tgrelid = 'work_issue_scope_links'::regclass
    ) THEN
        CREATE TRIGGER work_issue_scope_links_retire_only
        BEFORE UPDATE ON work_issue_scope_links
        FOR EACH ROW EXECUTE FUNCTION guard_work_issue_scope_link_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'work_issue_scope_events_no_update'
          AND tgrelid = 'work_issue_scope_events'::regclass
    ) THEN
        CREATE TRIGGER work_issue_scope_events_no_update
        BEFORE UPDATE ON work_issue_scope_events
        FOR EACH ROW EXECUTE FUNCTION reject_work_issue_scope_event_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'work_issue_scope_events_no_delete'
          AND tgrelid = 'work_issue_scope_events'::regclass
    ) THEN
        CREATE TRIGGER work_issue_scope_events_no_delete
        BEFORE DELETE ON work_issue_scope_events
        FOR EACH ROW EXECUTE FUNCTION reject_work_issue_scope_event_mutation();
    END IF;
END;
$$;
