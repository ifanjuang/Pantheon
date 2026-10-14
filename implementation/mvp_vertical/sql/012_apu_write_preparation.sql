-- Candidate-only APU write preparation and explicit authorization events.
-- Prepared or authorized commands are not applied by this migration.

CREATE TABLE IF NOT EXISTS apu_write_command_candidates (
    command_id TEXT PRIMARY KEY,
    execution_result_id TEXT NOT NULL,
    result_ref TEXT NOT NULL,
    mapping_ref TEXT NOT NULL,
    source_review_ref TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation = 'add_match_to_existing_object'),
    project_ref TEXT,
    target_stable_object_ref TEXT NOT NULL,
    source_candidate_ref TEXT NOT NULL,
    source_artifact_ref TEXT,
    certainty TEXT,
    match_axis TEXT,
    rationale TEXT NOT NULL,
    command_payload JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    expected_owner_revision INTEGER NOT NULL CHECK (expected_owner_revision >= 1),
    expected_object_revision INTEGER NOT NULL CHECK (expected_object_revision >= 1),
    prepared_by TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apu_write_authorization_events (
    authorization_id TEXT PRIMARY KEY,
    command_ref TEXT NOT NULL REFERENCES apu_write_command_candidates(command_id) ON DELETE RESTRICT,
    command_payload_digest TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('authorize_application', 'reject_application')),
    note TEXT,
    authorized_by TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    authorized_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
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
