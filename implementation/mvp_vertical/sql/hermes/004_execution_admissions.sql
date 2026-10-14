CREATE TABLE IF NOT EXISTS hermes_execution_admissions (
    admission_id TEXT PRIMARY KEY,
    handoff_id TEXT NOT NULL UNIQUE REFERENCES cockpit_hermes_handoffs(handoff_id) ON DELETE RESTRICT,
    work_issue_id TEXT NOT NULL UNIQUE REFERENCES work_issues(issue_id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (decision = 'allow'),
    requested_effect TEXT NOT NULL CHECK (requested_effect = 'read_only'),
    task_contract_ref TEXT NOT NULL,
    context_pack_ref TEXT NOT NULL,
    preview_digest TEXT NOT NULL,
    handoff_request_digest TEXT NOT NULL,
    admission_digest TEXT NOT NULL UNIQUE,
    idempotency_key TEXT NOT NULL UNIQUE,
    admitted_by TEXT NOT NULL,
    admitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS hermes_execution_admissions_issue_lookup
    ON hermes_execution_admissions (work_issue_id, admitted_at DESC);

ALTER TABLE hermes_runs
    ADD COLUMN IF NOT EXISTS admission_ref TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'hermes_runs_admission_ref_fkey'
           AND conrelid = 'hermes_runs'::regclass
    ) THEN
        ALTER TABLE hermes_runs
            ADD CONSTRAINT hermes_runs_admission_ref_fkey
            FOREIGN KEY (admission_ref)
            REFERENCES hermes_execution_admissions(admission_id)
            ON DELETE RESTRICT;
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS hermes_runs_one_per_admission
    ON hermes_runs (admission_ref)
    WHERE admission_ref IS NOT NULL;

CREATE OR REPLACE FUNCTION reject_hermes_execution_admission_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'hermes_execution_admissions are immutable';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_execution_admissions_no_update'
          AND tgrelid = 'hermes_execution_admissions'::regclass
    ) THEN
        CREATE TRIGGER hermes_execution_admissions_no_update
        BEFORE UPDATE ON hermes_execution_admissions
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_execution_admission_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_execution_admissions_no_delete'
          AND tgrelid = 'hermes_execution_admissions'::regclass
    ) THEN
        CREATE TRIGGER hermes_execution_admissions_no_delete
        BEFORE DELETE ON hermes_execution_admissions
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_execution_admission_mutation();
    END IF;
END;
$$;
