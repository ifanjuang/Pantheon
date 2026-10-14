-- Project change variants reuse Execution Results, review dispositions and the
-- existing Agency ChangeCandidate owner. No branch object or parallel proposal
-- store is introduced by this migration.

DO $$
BEGIN
    IF to_regclass('execution_result_items') IS NOT NULL THEN
        ALTER TABLE execution_result_items
            DROP CONSTRAINT IF EXISTS execution_result_items_result_kind_check;
        ALTER TABLE execution_result_items
            ADD CONSTRAINT execution_result_items_result_kind_check
            CHECK (result_kind IN (
                'fragment_qualification', 'document_alignment', 'spatial_observation',
                'apu_object_mapping', 'relation_candidate', 'contradiction_candidate',
                'work_issue_candidate', 'knowledge_edit_variant',
                'project_change_variant', 'project_claim_candidate',
                'observation_bundle'
            )) NOT VALID;
        ALTER TABLE execution_result_items
            VALIDATE CONSTRAINT execution_result_items_result_kind_check;
    END IF;

    IF to_regclass('execution_result_review_dispositions') IS NOT NULL THEN
        ALTER TABLE execution_result_review_dispositions
            DROP CONSTRAINT IF EXISTS execution_result_review_dispositions_disposition_check;
        ALTER TABLE execution_result_review_dispositions
            ADD CONSTRAINT execution_result_review_dispositions_disposition_check
            CHECK (disposition IN (
                'pending', 'needs_clarification', 'accepted_for_mapping',
                'selected_for_change_candidate', 'accepted_for_claim',
                'rejected', 'superseded'
            )) NOT VALID;
        ALTER TABLE execution_result_review_dispositions
            VALIDATE CONSTRAINT execution_result_review_dispositions_disposition_check;
    END IF;
END;
$$;

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

    IF NEW.disposition = 'selected_for_change_candidate' THEN
        IF candidate_kind <> 'project_change_variant' THEN
            RAISE EXCEPTION 'selected_for_change_candidate requires a project_change_variant result';
        END IF;
        IF NEW.reviewer_kind <> 'human' THEN
            RAISE EXCEPTION 'selected_for_change_candidate requires a human reviewer';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF to_regclass('execution_result_review_dispositions') IS NOT NULL THEN
        DROP TRIGGER IF EXISTS execution_dispositions_validate_candidate
            ON execution_result_review_dispositions;
        CREATE TRIGGER execution_dispositions_validate_candidate
        BEFORE INSERT ON execution_result_review_dispositions
        FOR EACH ROW EXECUTE FUNCTION validate_execution_result_review_disposition();
    END IF;
END;
$$;

-- The Agency ChangeCandidate owner can be installed independently of the
-- Execution Result surface. Add its optional provenance columns and local
-- constraints whenever that owner exists; foreign keys are attached later when
-- both sides are present.
DO $$
BEGIN
    IF to_regclass('agency_change_candidates') IS NULL THEN
        RETURN;
    END IF;

    ALTER TABLE agency_change_candidates
        ADD COLUMN IF NOT EXISTS source_execution_result_id TEXT,
        ADD COLUMN IF NOT EXISTS source_result_id TEXT,
        ADD COLUMN IF NOT EXISTS source_review_disposition_id TEXT,
        ADD COLUMN IF NOT EXISTS variant_request_ref TEXT,
        ADD COLUMN IF NOT EXISTS variant_scope_digest TEXT,
        ADD COLUMN IF NOT EXISTS variant_label TEXT,
        ADD COLUMN IF NOT EXISTS variant_title TEXT;

    ALTER TABLE agency_change_candidates
        DROP CONSTRAINT IF EXISTS agency_change_candidates_variant_provenance_check;
    ALTER TABLE agency_change_candidates
        ADD CONSTRAINT agency_change_candidates_variant_provenance_check
        CHECK (
            num_nonnulls(
                source_execution_result_id,
                source_result_id,
                source_review_disposition_id,
                variant_request_ref,
                variant_scope_digest,
                variant_label,
                variant_title
            ) IN (0, 7)
        ) NOT VALID;
    ALTER TABLE agency_change_candidates
        VALIDATE CONSTRAINT agency_change_candidates_variant_provenance_check;

    CREATE UNIQUE INDEX IF NOT EXISTS agency_change_candidates_variant_result_unique
        ON agency_change_candidates (source_result_id)
        WHERE source_result_id IS NOT NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS agency_change_candidates_variant_scope_unique
        ON agency_change_candidates (entity_id, variant_request_ref, variant_scope_digest)
        WHERE variant_request_ref IS NOT NULL;
END;
$$;

DO $$
BEGIN
    IF to_regclass('agency_change_candidates') IS NULL
       OR to_regclass('execution_results') IS NULL
       OR to_regclass('execution_result_items') IS NULL
       OR to_regclass('execution_result_review_dispositions') IS NULL THEN
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_change_candidates'::regclass
           AND conname = 'agency_change_candidates_source_execution_fk'
    ) THEN
        ALTER TABLE agency_change_candidates
            ADD CONSTRAINT agency_change_candidates_source_execution_fk
            FOREIGN KEY (source_execution_result_id)
            REFERENCES execution_results(execution_result_id) ON DELETE RESTRICT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_change_candidates'::regclass
           AND conname = 'agency_change_candidates_source_result_fk'
    ) THEN
        ALTER TABLE agency_change_candidates
            ADD CONSTRAINT agency_change_candidates_source_result_fk
            FOREIGN KEY (source_result_id)
            REFERENCES execution_result_items(result_id) ON DELETE RESTRICT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_change_candidates'::regclass
           AND conname = 'agency_change_candidates_source_disposition_fk'
    ) THEN
        ALTER TABLE agency_change_candidates
            ADD CONSTRAINT agency_change_candidates_source_disposition_fk
            FOREIGN KEY (source_review_disposition_id)
            REFERENCES execution_result_review_dispositions(disposition_id) ON DELETE RESTRICT;
    END IF;
END;
$$;
