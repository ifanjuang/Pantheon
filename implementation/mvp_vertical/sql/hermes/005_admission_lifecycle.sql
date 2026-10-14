ALTER TABLE hermes_execution_admissions
    ADD COLUMN IF NOT EXISTS work_issue_version INTEGER;

ALTER TABLE hermes_execution_admissions
    ADD COLUMN IF NOT EXISTS ttl_seconds INTEGER;

ALTER TABLE hermes_execution_admissions
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS hermes_execution_admission_events (
    event_id TEXT PRIMARY KEY,
    admission_id TEXT NOT NULL REFERENCES hermes_execution_admissions(admission_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type = 'revoked'),
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS hermes_execution_admission_events_lookup
    ON hermes_execution_admission_events (admission_id, occurred_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS hermes_execution_admission_single_revocation
    ON hermes_execution_admission_events (admission_id)
    WHERE event_type = 'revoked';

CREATE OR REPLACE FUNCTION reject_hermes_execution_admission_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'hermes_execution_admission_events are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_execution_admission_events_no_update'
          AND tgrelid = 'hermes_execution_admission_events'::regclass
    ) THEN
        CREATE TRIGGER hermes_execution_admission_events_no_update
        BEFORE UPDATE ON hermes_execution_admission_events
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_execution_admission_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_execution_admission_events_no_delete'
          AND tgrelid = 'hermes_execution_admission_events'::regclass
    ) THEN
        CREATE TRIGGER hermes_execution_admission_events_no_delete
        BEFORE DELETE ON hermes_execution_admission_events
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_execution_admission_event_mutation();
    END IF;
END;
$$;

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
         WHERE table_name = 'hermes_execution_admission_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE hermes_execution_admission_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
