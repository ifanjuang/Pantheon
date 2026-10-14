CREATE TABLE IF NOT EXISTS contradictory_review_candidates (
    review_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    task_contract_ref TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    candidate_digest TEXT NOT NULL,
    execution_id TEXT NOT NULL,
    review_status TEXT NOT NULL CHECK (
        review_status IN (
            'review_completed',
            'review_completed_with_reserve',
            'review_blocked',
            'review_inconclusive'
        )
    ),
    report_digest TEXT NOT NULL,
    report JSONB NOT NULL,
    submitted_by TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((report -> 'authority' ->> 'is_evidence')::boolean = false),
    CHECK ((report -> 'authority' ->> 'is_approval')::boolean = false),
    CHECK ((report -> 'authority' ->> 'is_zeus_closure')::boolean = false),
    CHECK ((report -> 'authority' ->> 'is_task_authorization')::boolean = false)
);

CREATE INDEX IF NOT EXISTS contradictory_review_candidates_project_idx
    ON contradictory_review_candidates(project_id, submitted_at DESC);

CREATE INDEX IF NOT EXISTS contradictory_review_candidates_task_contract_idx
    ON contradictory_review_candidates(task_contract_ref, submitted_at DESC);

CREATE OR REPLACE FUNCTION reject_contradictory_review_candidate_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'contradictory review candidates are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'contradictory_review_candidates_no_update'
          AND tgrelid = 'contradictory_review_candidates'::regclass
    ) THEN
        CREATE TRIGGER contradictory_review_candidates_no_update
        BEFORE UPDATE ON contradictory_review_candidates
        FOR EACH ROW EXECUTE FUNCTION reject_contradictory_review_candidate_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'contradictory_review_candidates_no_delete'
          AND tgrelid = 'contradictory_review_candidates'::regclass
    ) THEN
        CREATE TRIGGER contradictory_review_candidates_no_delete
        BEFORE DELETE ON contradictory_review_candidates
        FOR EACH ROW EXECUTE FUNCTION reject_contradictory_review_candidate_mutation();
    END IF;
END;
$$;
