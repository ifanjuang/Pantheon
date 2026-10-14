CREATE TABLE IF NOT EXISTS work_issues (
    issue_id TEXT PRIMARY KEY,
    case_ref TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ('human', 'hermes_child', 'promoted_suggestion')),
    parent_issue_ref TEXT REFERENCES work_issues(issue_id),
    primary_card_ref TEXT,
    issue_type TEXT NOT NULL CHECK (
        issue_type IN ('research', 'verification', 'correction', 'drafting', 'decision', 'action')
    ),
    priority TEXT NOT NULL,
    assigned_to TEXT,
    requested_effect TEXT NOT NULL CHECK (
        requested_effect IN ('read_only', 'draft', 'internal_write', 'external_effect', 'canonical_effect')
    ),
    status TEXT NOT NULL CHECK (
        status IN ('open', 'in_progress', 'waiting', 'review', 'done', 'cancelled')
    ),
    close_reason TEXT CHECK (
        close_reason IN ('answered', 'merged', 'duplicate', 'obsolete', 'rejected', 'impossible', 'cancelled')
    ),
    task_contract_ref TEXT,
    context_pack_ref TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (status IN ('done', 'cancelled') AND close_reason IS NOT NULL)
        OR (status NOT IN ('done', 'cancelled') AND close_reason IS NULL)
    )
);

-- Work Card presentation metadata is deliberately separate from the governed
-- Work Issue contract. It describes the visible workflow without turning the
-- Work Issue aggregate into a workflow engine.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_name = 'work_issues' AND column_name = 'workflow') THEN
        ALTER TABLE work_issues DROP COLUMN workflow;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_name = 'work_issues' AND column_name = 'information_ref') THEN
        ALTER TABLE work_issues DROP COLUMN information_ref;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_name = 'work_issues' AND column_name = 'result_ref') THEN
        ALTER TABLE work_issues DROP COLUMN result_ref;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_name = 'work_issues' AND column_name = 'decision_request') THEN
        ALTER TABLE work_issues DROP COLUMN decision_request;
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS work_card_metadata (
    issue_id TEXT PRIMARY KEY REFERENCES work_issues(issue_id) ON DELETE CASCADE,
    workflow JSONB NOT NULL DEFAULT '{}'::jsonb,
    information_ref TEXT,
    result_ref TEXT,
    decision_request JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issue_comments (
    comment_id TEXT PRIMARY KEY,
    issue_id TEXT NOT NULL REFERENCES work_issues(issue_id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hermes_runs (
    run_id TEXT PRIMARY KEY,
    issue_id TEXT NOT NULL REFERENCES work_issues(issue_id) ON DELETE CASCADE,
    task_contract_ref TEXT NOT NULL,
    context_pack_ref TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('not_started', 'running', 'returned', 'partial', 'failed', 'cancelled', 'unknown')
    ),
    requested_effect TEXT NOT NULL CHECK (
        requested_effect IN ('read_only', 'draft', 'internal_write', 'external_effect', 'canonical_effect')
    ),
    started_at TIMESTAMPTZ,
    returned_at TIMESTAMPTZ,
    normalized_return JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issue_events (
    event_id TEXT PRIMARY KEY,
    issue_id TEXT NOT NULL REFERENCES work_issues(issue_id) ON DELETE CASCADE,
    run_ref TEXT REFERENCES hermes_runs(run_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'issue_created', 'comment_added', 'status_changed', 'hermes_started',
            'hermes_returned', 'review_requested', 'issue_closed'
        )
    ),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'hermes', 'system')),
    expected_version INTEGER NOT NULL CHECK (expected_version >= 0),
    resulting_version INTEGER NOT NULL CHECK (resulting_version >= 1),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (resulting_version = expected_version + 1)
);

CREATE OR REPLACE FUNCTION reject_issue_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'issue_events are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'issue_events_no_update'
          AND tgrelid = 'issue_events'::regclass
    ) THEN
        CREATE TRIGGER issue_events_no_update
        BEFORE UPDATE ON issue_events
        FOR EACH ROW EXECUTE FUNCTION reject_issue_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'issue_events_no_delete'
          AND tgrelid = 'issue_events'::regclass
    ) THEN
        CREATE TRIGGER issue_events_no_delete
        BEFORE DELETE ON issue_events
        FOR EACH ROW EXECUTE FUNCTION reject_issue_event_mutation();
    END IF;
END;
$$;

-- CURRENT_TIMESTAMP is the transaction start time, so every event written in one
-- transaction shares an occurred_at and the append-only history cannot be ordered
-- by it. `record_hermes_return` writes three at once, all carrying the same
-- expected_version, and the read path orders by `occurred_at, event_id` — so with
-- both discriminators constant the visible order fell back to a random UUID.
-- clock_timestamp() advances per statement. Guarded on the value this adds, so a
-- started-up installation performs a catalog read only.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'issue_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE issue_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
