-- Structured human review of Project ChangeCandidates.
-- A revision request closes the current proposal without mutating the Project.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agency_change_candidates' AND column_name = 'review_annotations') THEN
        ALTER TABLE agency_change_candidates ADD COLUMN review_annotations JSONB NOT NULL DEFAULT '[]'::jsonb;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agency_change_candidates' AND column_name = 'decision_note') THEN
        ALTER TABLE agency_change_candidates ADD COLUMN decision_note TEXT;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'agency_change_candidates_status_check'
           AND conrelid = 'agency_change_candidates'::regclass
           AND pg_get_constraintdef(oid) LIKE $marker$%'revision_requested'%$marker$
    ) THEN
        ALTER TABLE agency_change_candidates DROP CONSTRAINT IF EXISTS agency_change_candidates_status_check;
        ALTER TABLE agency_change_candidates
            ADD CONSTRAINT agency_change_candidates_status_check CHECK (status IN ('pending_review', 'revision_requested', 'applied', 'rejected', 'stale')) NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'agency_change_candidate_events_event_type_check'
           AND conrelid = 'agency_change_candidate_events'::regclass
           AND pg_get_constraintdef(oid) LIKE $marker$%'revision_requested'%$marker$
    ) THEN
        ALTER TABLE agency_change_candidate_events DROP CONSTRAINT IF EXISTS agency_change_candidate_events_event_type_check;
        ALTER TABLE agency_change_candidate_events
            ADD CONSTRAINT agency_change_candidate_events_event_type_check CHECK (event_type IN ('proposed', 'revision_requested', 'applied', 'rejected', 'stale')) NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'agency_change_candidates_review_annotations_check'
           AND conrelid = 'agency_change_candidates'::regclass
    ) THEN
        ALTER TABLE agency_change_candidates
            ADD CONSTRAINT agency_change_candidates_review_annotations_check
            CHECK (jsonb_typeof(review_annotations) = 'array');
    END IF;
END;
$$;
