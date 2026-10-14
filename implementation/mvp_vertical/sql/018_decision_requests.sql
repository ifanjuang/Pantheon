-- Decision Requests are human-attention Gates. Resolving one creates a separate
-- immutable decision_record. Neither object resumes a runtime or transitions a
-- WorkIssue automatically.
--
-- The agency_ prefix is a PostgreSQL namespace for agency-owned data. It does
-- not define an agency_decision entity or an agency-level Decision authority.

CREATE TABLE IF NOT EXISTS agency_decision_requests (
    request_id TEXT PRIMARY KEY CHECK (request_id ~ '^[a-z0-9][a-z0-9._-]*$'),
    status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'cancelled')),
    decision_type TEXT NOT NULL CHECK (
        decision_type IN ('question', 'validation', 'approval', 'arbitration')
    ),
    question TEXT NOT NULL CHECK (length(question) BETWEEN 1 AND 20000),
    priority TEXT NOT NULL CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    response_mode TEXT NOT NULL CHECK (
        response_mode IN ('decision_value', 'single_option', 'multiple_options', 'free_text')
    ),
    recommendation_candidate TEXT,
    blocking BOOLEAN NOT NULL DEFAULT false,
    project_id TEXT REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    work_issue_id TEXT REFERENCES work_issues(issue_id) ON DELETE RESTRICT,
    conversation_ref TEXT,
    candidate_ref TEXT NOT NULL,
    candidate_digest TEXT NOT NULL CHECK (candidate_digest ~ '^[a-f0-9]{64}$'),
    evidence_pack_ref TEXT,
    evidence_pack_digest TEXT CHECK (
        evidence_pack_digest IS NULL OR evidence_pack_digest ~ '^[a-f0-9]{64}$'
    ),
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_refs) = 'array'),
    evidence_gaps JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(evidence_gaps) = 'array'),
    blocked_action TEXT,
    next_safe_action TEXT,
    decision_surface TEXT NOT NULL,
    decision_owner TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    resolved_decision_id TEXT,
    resolved_at TIMESTAMPTZ,
    cancelled_by TEXT,
    cancelled_at TIMESTAMPTZ,
    CHECK (NOT blocking OR work_issue_id IS NOT NULL),
    CHECK (
        (evidence_pack_ref IS NULL AND evidence_pack_digest IS NULL)
        OR (evidence_pack_ref IS NOT NULL AND evidence_pack_digest IS NOT NULL)
    ),
    CHECK (
        (status = 'pending'
         AND resolved_decision_id IS NULL AND resolved_at IS NULL
         AND cancelled_by IS NULL AND cancelled_at IS NULL)
        OR
        (status = 'resolved'
         AND resolved_decision_id IS NOT NULL AND resolved_at IS NOT NULL
         AND cancelled_by IS NULL AND cancelled_at IS NULL)
        OR
        (status = 'cancelled'
         AND resolved_decision_id IS NULL AND resolved_at IS NULL
         AND cancelled_by IS NOT NULL AND cancelled_at IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS decision_request_one_pending_blocker_per_work_issue
    ON agency_decision_requests (work_issue_id)
    WHERE status = 'pending' AND blocking = true;

CREATE INDEX IF NOT EXISTS decision_request_attention_lookup
    ON agency_decision_requests (status, priority, created_at, request_id);

CREATE INDEX IF NOT EXISTS decision_request_project_lookup
    ON agency_decision_requests (project_id, status, priority, created_at, request_id);

CREATE INDEX IF NOT EXISTS decision_request_work_issue_lookup
    ON agency_decision_requests (work_issue_id, status, created_at, request_id);

CREATE TABLE IF NOT EXISTS agency_decision_options (
    request_id TEXT NOT NULL REFERENCES agency_decision_requests(request_id) ON DELETE RESTRICT,
    option_id TEXT NOT NULL CHECK (option_id ~ '^[a-z0-9][a-z0-9._-]*$'),
    label TEXT NOT NULL,
    consequence TEXT NOT NULL,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(limitations) = 'array'),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    PRIMARY KEY (request_id, option_id),
    UNIQUE (request_id, ordinal)
);

CREATE TABLE IF NOT EXISTS agency_decision_records (
    decision_id TEXT PRIMARY KEY CHECK (decision_id ~ '^[a-z0-9][a-z0-9._-]*$'),
    request_id TEXT NOT NULL UNIQUE REFERENCES agency_decision_requests(request_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'recorded' CHECK (status = 'recorded'),
    applies_to TEXT NOT NULL,
    related_evidence_pack TEXT,
    decision TEXT NOT NULL CHECK (
        decision IN ('approve', 'refuse', 'request_revision', 'request_more_evidence')
    ),
    decided_by TEXT NOT NULL,
    identity_assurance TEXT NOT NULL CHECK (
        identity_assurance IN ('declared', 'authenticated')
    ),
    authenticated_principal JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    supersedes_decision_id TEXT REFERENCES agency_decision_records(decision_id) ON DELETE RESTRICT,
    candidate_digest TEXT NOT NULL CHECK (candidate_digest ~ '^[a-f0-9]{64}$'),
    evidence_pack_digest TEXT CHECK (
        evidence_pack_digest IS NULL OR evidence_pack_digest ~ '^[a-f0-9]{64}$'
    ),
    decision_surface TEXT NOT NULL,
    rationale TEXT,
    consequences JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(consequences) = 'object'),
    CHECK (
        (identity_assurance = 'declared' AND authenticated_principal IS NULL)
        OR
        (identity_assurance = 'authenticated'
         AND authenticated_principal IS NOT NULL
         AND jsonb_typeof(authenticated_principal) = 'object')
    )
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'agency_decision_requests_resolved_decision_fk'
           AND conrelid = 'agency_decision_requests'::regclass
    ) THEN
        ALTER TABLE agency_decision_requests
            ADD CONSTRAINT agency_decision_requests_resolved_decision_fk
            FOREIGN KEY (resolved_decision_id)
            REFERENCES agency_decision_records(decision_id)
            ON DELETE RESTRICT
            DEFERRABLE INITIALLY DEFERRED;
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS agency_decision_events (
    event_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES agency_decision_requests(request_id) ON DELETE RESTRICT,
    decision_id TEXT REFERENCES agency_decision_records(decision_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('request_created', 'request_resolved', 'request_cancelled')
    ),
    actor TEXT NOT NULL,
    expected_revision INTEGER NOT NULL CHECK (expected_revision >= 0),
    resulting_revision INTEGER NOT NULL CHECK (resulting_revision = expected_revision + 1),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS decision_events_request_lookup
    ON agency_decision_events (request_id, occurred_at, event_id);

CREATE OR REPLACE FUNCTION validate_decision_request_links()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.project_id IS NOT NULL AND NEW.work_issue_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
              FROM work_issue_scope_links scope_link
             WHERE scope_link.issue_id = NEW.work_issue_id
               AND scope_link.entity_type = 'project'
               AND scope_link.entity_id = NEW.project_id
               AND scope_link.retired_at IS NULL
        ) THEN
            RAISE EXCEPTION
                'blocking or linked WorkIssue is not scoped to Project %', NEW.project_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION guard_decision_request_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Decision Requests are retained; cancel instead of deleting';
    END IF;

    IF OLD.request_id IS DISTINCT FROM NEW.request_id
       OR OLD.decision_type IS DISTINCT FROM NEW.decision_type
       OR OLD.question IS DISTINCT FROM NEW.question
       OR OLD.priority IS DISTINCT FROM NEW.priority
       OR OLD.response_mode IS DISTINCT FROM NEW.response_mode
       OR OLD.recommendation_candidate IS DISTINCT FROM NEW.recommendation_candidate
       OR OLD.blocking IS DISTINCT FROM NEW.blocking
       OR OLD.project_id IS DISTINCT FROM NEW.project_id
       OR OLD.work_issue_id IS DISTINCT FROM NEW.work_issue_id
       OR OLD.conversation_ref IS DISTINCT FROM NEW.conversation_ref
       OR OLD.candidate_ref IS DISTINCT FROM NEW.candidate_ref
       OR OLD.candidate_digest IS DISTINCT FROM NEW.candidate_digest
       OR OLD.evidence_pack_ref IS DISTINCT FROM NEW.evidence_pack_ref
       OR OLD.evidence_pack_digest IS DISTINCT FROM NEW.evidence_pack_digest
       OR OLD.source_refs IS DISTINCT FROM NEW.source_refs
       OR OLD.evidence_gaps IS DISTINCT FROM NEW.evidence_gaps
       OR OLD.blocked_action IS DISTINCT FROM NEW.blocked_action
       OR OLD.next_safe_action IS DISTINCT FROM NEW.next_safe_action
       OR OLD.decision_surface IS DISTINCT FROM NEW.decision_surface
       OR OLD.decision_owner IS DISTINCT FROM NEW.decision_owner
       OR OLD.created_by IS DISTINCT FROM NEW.created_by
       OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION 'Decision Request review material is immutable';
    END IF;

    IF OLD.status <> 'pending' THEN
        RAISE EXCEPTION 'resolved or cancelled Decision Requests are immutable';
    END IF;
    IF NEW.status NOT IN ('resolved', 'cancelled') THEN
        RAISE EXCEPTION 'Decision Request may only resolve or cancel from pending';
    END IF;
    IF NEW.revision <> OLD.revision + 1 THEN
        RAISE EXCEPTION 'Decision Request revision must increment exactly once';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION reject_decision_immutable_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% rows are immutable and retained', TG_TABLE_NAME;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'decision_request_link_guard'
          AND tgrelid = 'agency_decision_requests'::regclass
    ) THEN
        CREATE TRIGGER decision_request_link_guard
        BEFORE INSERT ON agency_decision_requests
        FOR EACH ROW EXECUTE FUNCTION validate_decision_request_links();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'decision_requests_no_delete'
          AND tgrelid = 'agency_decision_requests'::regclass
    ) THEN
        CREATE TRIGGER decision_requests_no_delete
        BEFORE DELETE ON agency_decision_requests
        FOR EACH ROW EXECUTE FUNCTION guard_decision_request_update();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'decision_requests_resolve_or_cancel_only'
          AND tgrelid = 'agency_decision_requests'::regclass
    ) THEN
        CREATE TRIGGER decision_requests_resolve_or_cancel_only
        BEFORE UPDATE ON agency_decision_requests
        FOR EACH ROW EXECUTE FUNCTION guard_decision_request_update();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'decision_options_no_update'
          AND tgrelid = 'agency_decision_options'::regclass
    ) THEN
        CREATE TRIGGER decision_options_no_update
        BEFORE UPDATE OR DELETE ON agency_decision_options
        FOR EACH ROW EXECUTE FUNCTION reject_decision_immutable_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'decision_records_no_update'
          AND tgrelid = 'agency_decision_records'::regclass
    ) THEN
        CREATE TRIGGER decision_records_no_update
        BEFORE UPDATE OR DELETE ON agency_decision_records
        FOR EACH ROW EXECUTE FUNCTION reject_decision_immutable_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'decision_events_no_update'
          AND tgrelid = 'agency_decision_events'::regclass
    ) THEN
        CREATE TRIGGER decision_events_no_update
        BEFORE UPDATE OR DELETE ON agency_decision_events
        FOR EACH ROW EXECUTE FUNCTION reject_decision_immutable_mutation();
    END IF;
END;
$$;
