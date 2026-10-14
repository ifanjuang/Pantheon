-- Append-only execution results and review dispositions.
-- Runtime return, review disposition and governed adoption remain separate facts.

CREATE TABLE IF NOT EXISTS execution_results (
    execution_result_id TEXT PRIMARY KEY,
    task_contract_ref TEXT NOT NULL,
    project_ref TEXT,
    producer JSONB NOT NULL,
    produced_at TIMESTAMPTZ NOT NULL,
    evidence_pack_candidate_ref TEXT,
    authority JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution_result_items (
    result_id TEXT PRIMARY KEY,
    execution_result_id TEXT NOT NULL REFERENCES execution_results(execution_result_id) ON DELETE RESTRICT,
    result_kind TEXT NOT NULL CHECK (result_kind IN (
        'fragment_qualification', 'document_alignment', 'spatial_observation',
        'apu_object_mapping', 'relation_candidate', 'contradiction_candidate',
        'work_issue_candidate', 'knowledge_edit_variant', 'project_claim_candidate',
        'observation_bundle'
    )),
    schema_ref TEXT NOT NULL,
    payload JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    ordinal INT NOT NULL CHECK (ordinal >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (execution_result_id, ordinal)
);

CREATE TABLE IF NOT EXISTS execution_clarification_requests (
    clarification_id TEXT PRIMARY KEY,
    execution_result_id TEXT NOT NULL REFERENCES execution_results(execution_result_id) ON DELETE RESTRICT,
    related_result_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    question TEXT NOT NULL,
    answer_kind TEXT NOT NULL CHECK (answer_kind IN (
        'free_text', 'single_choice', 'multiple_choice', 'confirmation', 'source_request'
    )),
    options JSONB NOT NULL DEFAULT '[]'::jsonb,
    rationale TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (jsonb_typeof(related_result_refs) = 'array'),
    CHECK (jsonb_typeof(options) = 'array')
);

CREATE TABLE IF NOT EXISTS execution_result_review_dispositions (
    disposition_id TEXT PRIMARY KEY,
    result_ref TEXT NOT NULL REFERENCES execution_result_items(result_id) ON DELETE RESTRICT,
    disposition TEXT NOT NULL CHECK (disposition IN (
        'pending', 'needs_clarification', 'accepted_for_mapping',
        'accepted_for_claim', 'rejected', 'superseded'
    )),
    reviewer TEXT NOT NULL,
    reviewer_kind TEXT NOT NULL CHECK (reviewer_kind IN ('human', 'system')),
    note TEXT,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION reject_execution_result_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'execution result records are append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS execution_results_append_only ON execution_results;
CREATE TRIGGER execution_results_append_only
BEFORE UPDATE OR DELETE ON execution_results
FOR EACH ROW EXECUTE FUNCTION reject_execution_result_mutation();

DROP TRIGGER IF EXISTS execution_result_items_append_only ON execution_result_items;
CREATE TRIGGER execution_result_items_append_only
BEFORE UPDATE OR DELETE ON execution_result_items
FOR EACH ROW EXECUTE FUNCTION reject_execution_result_mutation();

DROP TRIGGER IF EXISTS execution_clarifications_append_only ON execution_clarification_requests;
CREATE TRIGGER execution_clarifications_append_only
BEFORE UPDATE OR DELETE ON execution_clarification_requests
FOR EACH ROW EXECUTE FUNCTION reject_execution_result_mutation();

DROP TRIGGER IF EXISTS execution_dispositions_append_only ON execution_result_review_dispositions;
CREATE TRIGGER execution_dispositions_append_only
BEFORE UPDATE OR DELETE ON execution_result_review_dispositions
FOR EACH ROW EXECUTE FUNCTION reject_execution_result_mutation();

CREATE OR REPLACE FUNCTION validate_execution_result_review_disposition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    candidate_kind TEXT;
BEGIN
    SELECT result_kind
      INTO candidate_kind
      FROM execution_result_items
     WHERE result_id = NEW.result_ref
     FOR UPDATE;

    IF candidate_kind IS NULL THEN
        RAISE EXCEPTION 'unknown result candidate: %', NEW.result_ref;
    END IF;

    IF NEW.disposition = 'accepted_for_claim' THEN
        IF candidate_kind <> 'project_claim_candidate' THEN
            RAISE EXCEPTION 'accepted_for_claim requires a project_claim_candidate result';
        END IF;
        IF NEW.reviewer_kind <> 'human' THEN
            RAISE EXCEPTION 'accepted_for_claim requires a human reviewer';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS execution_dispositions_validate_candidate
    ON execution_result_review_dispositions;
CREATE TRIGGER execution_dispositions_validate_candidate
BEFORE INSERT ON execution_result_review_dispositions
FOR EACH ROW EXECUTE FUNCTION validate_execution_result_review_disposition();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'execution_result_items'::regclass
           AND conname = 'execution_result_items_result_kind_check'
           AND pg_get_constraintdef(oid) LIKE '%observation_bundle%'
    ) THEN
        ALTER TABLE execution_result_items
            DROP CONSTRAINT IF EXISTS execution_result_items_result_kind_check;
        ALTER TABLE execution_result_items
            ADD CONSTRAINT execution_result_items_result_kind_check
            CHECK (result_kind IN (
                'fragment_qualification', 'document_alignment', 'spatial_observation',
                'apu_object_mapping', 'relation_candidate', 'contradiction_candidate',
                'work_issue_candidate', 'knowledge_edit_variant', 'project_claim_candidate',
                'observation_bundle'
            )) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'execution_result_review_dispositions'::regclass
           AND conname = 'execution_result_review_dispositions_disposition_check'
           AND pg_get_constraintdef(oid) LIKE '%accepted_for_claim%'
    ) THEN
        ALTER TABLE execution_result_review_dispositions
            DROP CONSTRAINT IF EXISTS execution_result_review_dispositions_disposition_check;
        ALTER TABLE execution_result_review_dispositions
            ADD CONSTRAINT execution_result_review_dispositions_disposition_check
            CHECK (disposition IN (
                'pending', 'needs_clarification', 'accepted_for_mapping',
                'accepted_for_claim', 'rejected', 'superseded'
            )) NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'execution_result_items'::regclass
           AND conname = 'execution_result_items_result_kind_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE execution_result_items
            VALIDATE CONSTRAINT execution_result_items_result_kind_check;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'execution_result_review_dispositions'::regclass
           AND conname = 'execution_result_review_dispositions_disposition_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE execution_result_review_dispositions
            VALIDATE CONSTRAINT execution_result_review_dispositions_disposition_check;
    END IF;
END;
$$;

-- CURRENT_TIMESTAMP is the transaction start time, so events written in one
-- transaction share an occurred_at and cannot be ordered by it. clock_timestamp()
-- advances per statement. Guarded on the value this adds, so subsequent startup
-- performs a catalog read only.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'execution_result_review_dispositions'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE execution_result_review_dispositions
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
