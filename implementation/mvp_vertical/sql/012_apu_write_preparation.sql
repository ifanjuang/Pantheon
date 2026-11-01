-- Candidate-only APU write preparation and explicit authorization events.
-- Prepared or authorized commands are not applied by this migration.

CREATE TABLE IF NOT EXISTS apu_write_command_candidates (
    command_id TEXT PRIMARY KEY,
    execution_result_id TEXT NOT NULL,
    result_ref TEXT NOT NULL,
    mapping_ref TEXT NOT NULL,
    source_review_ref TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN (
        'add_match_to_existing_object', 'add_claim', 'supersede_claim'
    )),
    project_ref TEXT,
    -- Match commands target one stable object; claim commands target a claim
    -- subject and leave both object columns empty (see the CHECK below).
    target_stable_object_ref TEXT,
    source_candidate_ref TEXT NOT NULL,
    source_artifact_ref TEXT,
    certainty TEXT,
    match_axis TEXT,
    rationale TEXT NOT NULL,
    command_payload JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    expected_owner_revision INTEGER NOT NULL CHECK (expected_owner_revision >= 1),
    expected_object_revision INTEGER CHECK (expected_object_revision >= 1),
    prepared_by TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT apu_write_command_target_shape CHECK (
        (operation = 'add_match_to_existing_object'
            AND target_stable_object_ref IS NOT NULL
            AND expected_object_revision IS NOT NULL)
        OR (operation <> 'add_match_to_existing_object'
            AND target_stable_object_ref IS NULL
            AND expected_object_revision IS NULL)
    )
);

-- Claim commands joined after the first installations, whose table still
-- requires an object target and allows only the match operation.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'apu_write_command_target_shape'
           AND conrelid = 'apu_write_command_candidates'::regclass
    ) THEN
        ALTER TABLE apu_write_command_candidates
            DROP CONSTRAINT IF EXISTS apu_write_command_candidates_operation_check;
        ALTER TABLE apu_write_command_candidates
            ADD CONSTRAINT apu_write_command_candidates_operation_check CHECK (operation IN (
                'add_match_to_existing_object', 'add_claim', 'supersede_claim'
            ));
        ALTER TABLE apu_write_command_candidates
            ALTER COLUMN target_stable_object_ref DROP NOT NULL;
        ALTER TABLE apu_write_command_candidates
            ALTER COLUMN expected_object_revision DROP NOT NULL;
        ALTER TABLE apu_write_command_candidates
            ADD CONSTRAINT apu_write_command_target_shape CHECK (
                (operation = 'add_match_to_existing_object'
                    AND target_stable_object_ref IS NOT NULL
                    AND expected_object_revision IS NOT NULL)
                OR (operation <> 'add_match_to_existing_object'
                    AND target_stable_object_ref IS NULL
                    AND expected_object_revision IS NULL)
            );
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS apu_write_authorization_events (
    authorization_id TEXT PRIMARY KEY,
    command_ref TEXT NOT NULL REFERENCES apu_write_command_candidates(command_id) ON DELETE RESTRICT,
    command_payload_digest TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('authorize_application', 'reject_application')),
    note TEXT,
    authorized_by TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    authorized_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION reject_apu_write_preparation_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'APU write preparation records are append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS apu_write_commands_append_only ON apu_write_command_candidates;
CREATE TRIGGER apu_write_commands_append_only
BEFORE UPDATE OR DELETE ON apu_write_command_candidates
FOR EACH ROW EXECUTE FUNCTION reject_apu_write_preparation_mutation();

DROP TRIGGER IF EXISTS apu_write_authorizations_append_only ON apu_write_authorization_events;
CREATE TRIGGER apu_write_authorizations_append_only
BEFORE UPDATE OR DELETE ON apu_write_authorization_events
FOR EACH ROW EXECUTE FUNCTION reject_apu_write_preparation_mutation();

-- The latest authorization event decides whether a command may be applied, and
-- events are read ORDER BY authorized_at. CURRENT_TIMESTAMP is the transaction
-- start, so two events written in one transaction tied (and fell back to the
-- hashed id), and an event whose transaction began earlier sorted first even
-- when it was written last. clock_timestamp() is read when the row is written,
-- under the command-row lock both writers take. Same fix as in 011.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'apu_write_authorization_events'
           AND column_name = 'authorized_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE apu_write_authorization_events
            ALTER COLUMN authorized_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
