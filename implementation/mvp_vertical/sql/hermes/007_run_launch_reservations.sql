CREATE TABLE IF NOT EXISTS hermes_run_launch_reservations (
    launch_reservation_id TEXT PRIMARY KEY,
    admission_id TEXT NOT NULL UNIQUE REFERENCES hermes_execution_admissions(admission_id) ON DELETE RESTRICT,
    snapshot_id TEXT NOT NULL UNIQUE,
    snapshot_digest TEXT NOT NULL,
    snapshot_payload JSONB NOT NULL,
    field_projection_version TEXT NOT NULL,
    work_issue_version INTEGER NOT NULL CHECK (work_issue_version >= 1),
    launch_expires_at TIMESTAMPTZ NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    reserved_by TEXT NOT NULL,
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS hermes_run_launch_reservations_admission_lookup
    ON hermes_run_launch_reservations (admission_id, reserved_at DESC);

ALTER TABLE hermes_runs
    ADD COLUMN IF NOT EXISTS launch_reservation_ref TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'hermes_runs_launch_reservation_ref_fkey'
           AND conrelid = 'hermes_runs'::regclass
    ) THEN
        ALTER TABLE hermes_runs
            ADD CONSTRAINT hermes_runs_launch_reservation_ref_fkey
            FOREIGN KEY (launch_reservation_ref)
            REFERENCES hermes_run_launch_reservations(launch_reservation_id)
            ON DELETE RESTRICT;
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS hermes_runs_one_per_launch_reservation
    ON hermes_runs (launch_reservation_ref)
    WHERE launch_reservation_ref IS NOT NULL;

CREATE OR REPLACE FUNCTION reject_hermes_run_launch_reservation_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'hermes_run_launch_reservations are immutable';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_run_launch_reservations_no_update'
          AND tgrelid = 'hermes_run_launch_reservations'::regclass
    ) THEN
        CREATE TRIGGER hermes_run_launch_reservations_no_update
        BEFORE UPDATE ON hermes_run_launch_reservations
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_run_launch_reservation_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_run_launch_reservations_no_delete'
          AND tgrelid = 'hermes_run_launch_reservations'::regclass
    ) THEN
        CREATE TRIGGER hermes_run_launch_reservations_no_delete
        BEFORE DELETE ON hermes_run_launch_reservations
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_run_launch_reservation_mutation();
    END IF;
END;
$$;
