CREATE TABLE IF NOT EXISTS hermes_result_candidates (
    result_candidate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES hermes_runs(run_id) ON DELETE RESTRICT,
    admission_id TEXT NOT NULL REFERENCES hermes_execution_admissions(admission_id) ON DELETE RESTRICT,
    issue_id TEXT NOT NULL REFERENCES work_issues(issue_id) ON DELETE RESTRICT,
    result_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    candidate_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence_note TEXT,
    known_limits JSONB NOT NULL DEFAULT '[]'::jsonb,
    open_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    trace_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_candidate_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    governance_result_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (governance_result_status = 'candidate'),
    evidence_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (evidence_status = 'candidate'),
    trace_is_not_proof BOOLEAN NOT NULL DEFAULT TRUE
        CHECK (trace_is_not_proof = TRUE),
    approval_still_required BOOLEAN NOT NULL DEFAULT TRUE
        CHECK (approval_still_required = TRUE),
    human_decision_required BOOLEAN NOT NULL DEFAULT TRUE
        CHECK (human_decision_required = TRUE),
    result_digest TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS hermes_result_candidates_issue_lookup
    ON hermes_result_candidates (issue_id, created_at DESC);

CREATE INDEX IF NOT EXISTS hermes_result_candidates_admission_lookup
    ON hermes_result_candidates (admission_id, created_at DESC);

CREATE OR REPLACE FUNCTION reject_hermes_result_candidate_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'hermes_result_candidates are immutable candidate snapshots';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_result_candidates_no_update'
          AND tgrelid = 'hermes_result_candidates'::regclass
    ) THEN
        CREATE TRIGGER hermes_result_candidates_no_update
        BEFORE UPDATE ON hermes_result_candidates
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_result_candidate_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'hermes_result_candidates_no_delete'
          AND tgrelid = 'hermes_result_candidates'::regclass
    ) THEN
        CREATE TRIGGER hermes_result_candidates_no_delete
        BEFORE DELETE ON hermes_result_candidates
        FOR EACH ROW EXECUTE FUNCTION reject_hermes_result_candidate_mutation();
    END IF;
END;
$$;
