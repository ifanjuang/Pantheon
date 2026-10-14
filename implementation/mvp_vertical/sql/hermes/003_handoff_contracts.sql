CREATE TABLE IF NOT EXISTS cockpit_hermes_handoffs (
    handoff_id TEXT PRIMARY KEY,
    work_issue_id TEXT NOT NULL UNIQUE REFERENCES work_issues(issue_id) ON DELETE RESTRICT,
    case_ref TEXT NOT NULL,
    root_entity_id TEXT NOT NULL,
    root_entity_type TEXT NOT NULL,
    question TEXT NOT NULL,
    requested_effect TEXT NOT NULL CHECK (requested_effect = 'read_only'),
    task_contract_ref TEXT NOT NULL,
    context_pack_ref TEXT NOT NULL,
    preview_digest TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    task_contract JSONB NOT NULL,
    context_pack JSONB NOT NULL,
    selected_context JSONB NOT NULL DEFAULT '[]'::jsonb,
    include_declared_descendants BOOLEAN NOT NULL DEFAULT FALSE,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS cockpit_hermes_handoffs_case_lookup
    ON cockpit_hermes_handoffs (case_ref, created_at DESC);

CREATE OR REPLACE FUNCTION reject_cockpit_hermes_handoff_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'cockpit_hermes_handoffs are immutable contract snapshots';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'cockpit_hermes_handoffs_no_update'
          AND tgrelid = 'cockpit_hermes_handoffs'::regclass
    ) THEN
        CREATE TRIGGER cockpit_hermes_handoffs_no_update
        BEFORE UPDATE ON cockpit_hermes_handoffs
        FOR EACH ROW EXECUTE FUNCTION reject_cockpit_hermes_handoff_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'cockpit_hermes_handoffs_no_delete'
          AND tgrelid = 'cockpit_hermes_handoffs'::regclass
    ) THEN
        CREATE TRIGGER cockpit_hermes_handoffs_no_delete
        BEFORE DELETE ON cockpit_hermes_handoffs
        FOR EACH ROW EXECUTE FUNCTION reject_cockpit_hermes_handoff_mutation();
    END IF;
END;
$$;
