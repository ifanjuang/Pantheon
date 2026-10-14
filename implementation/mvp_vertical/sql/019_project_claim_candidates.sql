-- Tranche F: qualify ProjectClaims and preserve exact Execution Result provenance.
--
-- Existing Claims remain valid but acquire certainty E0 because no stronger
-- certainty was recorded. The migration creates no Claim and promotes no result.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_claims' AND column_name = 'certainty'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD COLUMN certainty TEXT NOT NULL DEFAULT 'E0';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_claims' AND column_name = 'effective_at'
    ) THEN
        ALTER TABLE agency_project_claims ADD COLUMN effective_at TIMESTAMPTZ;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_claims' AND column_name = 'candidate_execution_id'
    ) THEN
        ALTER TABLE agency_project_claims ADD COLUMN candidate_execution_id TEXT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_claims' AND column_name = 'candidate_result_id'
    ) THEN
        ALTER TABLE agency_project_claims ADD COLUMN candidate_result_id TEXT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_claims' AND column_name = 'candidate_review_disposition_id'
    ) THEN
        ALTER TABLE agency_project_claims ADD COLUMN candidate_review_disposition_id TEXT;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_certainty_check'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_certainty_check
            CHECK (certainty IN ('E0', 'E1', 'E2', 'E3', 'E4')) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_source_kind_check'
           AND pg_get_constraintdef(oid) LIKE '%execution_result%'
    ) THEN
        ALTER TABLE agency_project_claims
            DROP CONSTRAINT IF EXISTS agency_project_claims_source_kind_check;
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_source_kind_check
            CHECK (source_kind IN (
                'information', 'document', 'human_assertion', 'derived',
                'execution_result', 'external_projection'
            )) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_candidate_identity_check'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_candidate_identity_check
            CHECK (
                (candidate_execution_id IS NULL AND candidate_result_id IS NULL
                 AND candidate_review_disposition_id IS NULL)
                OR
                (candidate_execution_id IS NOT NULL AND candidate_result_id IS NOT NULL
                 AND candidate_review_disposition_id IS NOT NULL)
            ) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_execution_source_check'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_execution_source_check
            CHECK (
                (source_kind = 'execution_result'
                 AND candidate_execution_id IS NOT NULL
                 AND candidate_result_id IS NOT NULL
                 AND candidate_review_disposition_id IS NOT NULL)
                OR
                (source_kind <> 'execution_result'
                 AND candidate_execution_id IS NULL
                 AND candidate_result_id IS NULL
                 AND candidate_review_disposition_id IS NULL)
            ) NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_certainty_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_certainty_check;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_source_kind_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_source_kind_check;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_candidate_identity_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_candidate_identity_check;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_execution_source_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_execution_source_check;
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS agency_project_claims_one_claim_per_candidate
    ON agency_project_claims (candidate_execution_id, candidate_result_id)
    WHERE candidate_execution_id IS NOT NULL AND candidate_result_id IS NOT NULL;

-- These references are installed only when the execution-result owner is present.
-- Standalone Agency Data initialization remains valid; composed startup replays
-- this migration after execution_results and installs the references.
DO $$
BEGIN
    IF to_regclass('execution_results') IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM pg_constraint
            WHERE conrelid = 'agency_project_claims'::regclass
              AND conname = 'agency_project_claims_candidate_execution_fk'
       ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_candidate_execution_fk
            FOREIGN KEY (candidate_execution_id)
            REFERENCES execution_results(execution_result_id) ON DELETE RESTRICT
            NOT VALID;
    END IF;

    IF to_regclass('execution_result_items') IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM pg_constraint
            WHERE conrelid = 'agency_project_claims'::regclass
              AND conname = 'agency_project_claims_candidate_result_fk'
       ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_candidate_result_fk
            FOREIGN KEY (candidate_result_id)
            REFERENCES execution_result_items(result_id) ON DELETE RESTRICT
            NOT VALID;
    END IF;

    IF to_regclass('execution_result_review_dispositions') IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM pg_constraint
            WHERE conrelid = 'agency_project_claims'::regclass
              AND conname = 'agency_project_claims_candidate_disposition_fk'
       ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_candidate_disposition_fk
            FOREIGN KEY (candidate_review_disposition_id)
            REFERENCES execution_result_review_dispositions(disposition_id)
            ON DELETE RESTRICT NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_candidate_execution_fk'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_candidate_execution_fk;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_candidate_result_fk'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_candidate_result_fk;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_candidate_disposition_fk'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_candidate_disposition_fk;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION validate_agency_project_claim_candidate_ref()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    actual_execution_id TEXT;
    candidate_kind TEXT;
    candidate_payload JSONB;
    execution_project_ref TEXT;
    review_result_ref TEXT;
    review_disposition TEXT;
    review_kind TEXT;
    latest_disposition_id TEXT;
    matching_basis JSONB;
    backing_project_id TEXT;
BEGIN
    IF NEW.source_kind <> 'execution_result' THEN
        RETURN NEW;
    END IF;

    IF to_regclass('execution_result_items') IS NULL
       OR to_regclass('execution_result_review_dispositions') IS NULL THEN
        RAISE EXCEPTION 'execution result authorities are unavailable for ProjectClaim creation';
    END IF;

    SELECT i.execution_result_id, i.result_kind, i.payload, e.project_ref
      INTO actual_execution_id, candidate_kind, candidate_payload, execution_project_ref
      FROM execution_result_items i
      JOIN execution_results e
        ON e.execution_result_id = i.execution_result_id
     WHERE i.result_id = NEW.candidate_result_id
     FOR UPDATE OF i;

    IF actual_execution_id IS NULL OR actual_execution_id <> NEW.candidate_execution_id THEN
        RAISE EXCEPTION 'ProjectClaim candidate result does not belong to the declared execution';
    END IF;
    IF candidate_kind <> 'project_claim_candidate' THEN
        RAISE EXCEPTION 'ProjectClaim creation requires a project_claim_candidate result';
    END IF;
    IF execution_project_ref IS DISTINCT FROM NEW.project_id
       OR candidate_payload->>'project_ref' IS DISTINCT FROM NEW.project_id THEN
        RAISE EXCEPTION 'ProjectClaim candidate and execution must belong to the Claim Project';
    END IF;
    IF candidate_payload->>'claim_type' IS DISTINCT FROM NEW.claim_type THEN
        RAISE EXCEPTION 'ProjectClaim claim_type must match the reviewed candidate';
    END IF;
    IF candidate_payload->'proposed_value' IS DISTINCT FROM NEW.value THEN
        RAISE EXCEPTION 'ProjectClaim value must match the reviewed candidate';
    END IF;
    IF candidate_payload->>'unit' IS DISTINCT FROM NEW.unit THEN
        RAISE EXCEPTION 'ProjectClaim unit must match the reviewed candidate';
    END IF;
    IF (candidate_payload->>'observed_at')::timestamptz IS DISTINCT FROM NEW.observed_at THEN
        RAISE EXCEPTION 'ProjectClaim observed_at must match the reviewed candidate';
    END IF;
    IF (candidate_payload->>'effective_at')::timestamptz IS DISTINCT FROM NEW.effective_at THEN
        RAISE EXCEPTION 'ProjectClaim effective_at must match the reviewed candidate';
    END IF;

    SELECT result_ref, disposition, reviewer_kind
      INTO review_result_ref, review_disposition, review_kind
      FROM execution_result_review_dispositions
     WHERE disposition_id = NEW.candidate_review_disposition_id;

    IF review_result_ref IS NULL OR review_result_ref <> NEW.candidate_result_id THEN
        RAISE EXCEPTION 'ProjectClaim review disposition does not belong to the candidate result';
    END IF;
    IF review_disposition <> 'accepted_for_claim' OR review_kind <> 'human' THEN
        RAISE EXCEPTION 'ProjectClaim creation requires a human accepted_for_claim disposition';
    END IF;

    SELECT disposition_id
      INTO latest_disposition_id
      FROM execution_result_review_dispositions
     WHERE result_ref = NEW.candidate_result_id
     ORDER BY occurred_at DESC, disposition_id DESC
     LIMIT 1;

    IF latest_disposition_id <> NEW.candidate_review_disposition_id THEN
        RAISE EXCEPTION 'ProjectClaim creation requires the latest candidate disposition';
    END IF;

    IF NEW.backing_entity_type IS NOT NULL THEN
        IF NEW.backing_entity_type NOT IN ('project', 'information') THEN
            RAISE EXCEPTION 'candidate-backed Claim currently admits only project or information backing';
        END IF;

        SELECT basis
          INTO matching_basis
          FROM jsonb_array_elements(COALESCE(candidate_payload->'basis_refs', '[]'::jsonb)) basis
         WHERE basis->>'entity_type' = NEW.backing_entity_type
           AND basis->>'entity_id' = NEW.backing_entity_id
         LIMIT 1;

        IF matching_basis IS NULL THEN
            RAISE EXCEPTION 'ProjectClaim backing_ref must be one of the candidate basis_refs';
        END IF;
        IF matching_basis->>'observed_status' IS DISTINCT FROM NEW.backing_observed_status THEN
            RAISE EXCEPTION 'ProjectClaim backing observed_status must match the candidate basis_ref';
        END IF;

        IF NEW.backing_entity_type = 'project' THEN
            IF NEW.backing_entity_id <> NEW.project_id THEN
                RAISE EXCEPTION 'ProjectClaim project backing must identify the Claim Project';
            END IF;
        ELSE
            SELECT project_id
              INTO backing_project_id
              FROM agency_information_cards
             WHERE information_id = NEW.backing_entity_id;
            IF backing_project_id IS NULL OR backing_project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'ProjectClaim information backing must belong to the Claim Project';
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agency_project_claims_validate_candidate_ref
    ON agency_project_claims;
CREATE TRIGGER agency_project_claims_validate_candidate_ref
BEFORE INSERT ON agency_project_claims
FOR EACH ROW
EXECUTE FUNCTION validate_agency_project_claim_candidate_ref();

-- Refresh the existing Project read cache with the qualified Claim shape. The
-- cache remains derived and never becomes a second Claim authority.
CREATE OR REPLACE FUNCTION refresh_agency_project_claim_projection(target_project_id TEXT)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    scalar_values JSONB := '{}'::jsonb;
    scalar_refs JSONB := '{}'::jsonb;
    parcel_values JSONB := '[]'::jsonb;
    parcel_refs JSONB := '[]'::jsonb;
BEGIN
    WITH active_scalar AS (
        SELECT DISTINCT ON (c.claim_type) c.*
          FROM agency_project_claims c
         WHERE c.project_id = target_project_id
           AND c.claim_type <> 'parcelle'
           AND c.status <> 'retired'
           AND NOT EXISTS (
               SELECT 1 FROM agency_project_claims newer
                WHERE newer.supersedes = c.claim_id
           )
         ORDER BY c.claim_type, c.observed_at DESC, c.created_at DESC, c.claim_id DESC
    ), projected AS (
        SELECT claim_type,
               value,
               jsonb_build_object(
                   'claim_id', claim_id,
                   'status', status,
                   'certainty', certainty,
                   'unit', unit,
                   'backing_ref', CASE
                       WHEN backing_entity_type IS NULL THEN NULL
                       ELSE jsonb_build_object(
                           'entity_type', backing_entity_type,
                           'entity_id', backing_entity_id,
                           'observed_status', backing_observed_status
                       )
                   END,
                   'provenance', jsonb_build_object(
                       'source_kind', source_kind,
                       'source_ref', source_ref,
                       'candidate_ref', CASE
                           WHEN candidate_execution_id IS NULL THEN NULL
                           ELSE jsonb_build_object(
                               'execution_id', candidate_execution_id,
                               'result_id', candidate_result_id,
                               'review_disposition_id', candidate_review_disposition_id
                           )
                       END,
                       'asserted_by', asserted_by,
                       'derivation_note', derivation_note
                   ),
                   'observed_at', observed_at,
                   'effective_at', effective_at
               ) AS ref
          FROM active_scalar
    )
    SELECT COALESCE(jsonb_object_agg(claim_type, value), '{}'::jsonb),
           COALESCE(jsonb_object_agg(claim_type, ref), '{}'::jsonb)
      INTO scalar_values, scalar_refs
      FROM projected;

    WITH active_parcels AS (
        SELECT c.*
          FROM agency_project_claims c
         WHERE c.project_id = target_project_id
           AND c.claim_type = 'parcelle'
           AND c.status <> 'retired'
           AND NOT EXISTS (
               SELECT 1 FROM agency_project_claims newer
                WHERE newer.supersedes = c.claim_id
           )
         ORDER BY c.observed_at DESC, c.created_at DESC, c.claim_id DESC
    )
    SELECT COALESCE(jsonb_agg(value), '[]'::jsonb),
           COALESCE(jsonb_agg(jsonb_build_object(
               'claim_id', claim_id,
               'status', status,
               'certainty', certainty,
               'backing_ref', CASE
                   WHEN backing_entity_type IS NULL THEN NULL
                   ELSE jsonb_build_object(
                       'entity_type', backing_entity_type,
                       'entity_id', backing_entity_id,
                       'observed_status', backing_observed_status
                   )
               END,
               'provenance', jsonb_build_object(
                   'source_kind', source_kind,
                   'source_ref', source_ref,
                   'candidate_ref', CASE
                       WHEN candidate_execution_id IS NULL THEN NULL
                       ELSE jsonb_build_object(
                           'execution_id', candidate_execution_id,
                           'result_id', candidate_result_id,
                           'review_disposition_id', candidate_review_disposition_id
                       )
                   END,
                   'asserted_by', asserted_by,
                   'derivation_note', derivation_note
               ),
               'observed_at', observed_at,
               'effective_at', effective_at
           )), '[]'::jsonb)
      INTO parcel_values, parcel_refs
      FROM active_parcels;

    IF jsonb_array_length(parcel_values) > 0 THEN
        scalar_values := scalar_values || jsonb_build_object('parcelle', parcel_values);
        scalar_refs := scalar_refs || jsonb_build_object('parcelle', parcel_refs);
    END IF;

    UPDATE agency_projects
       SET claim_values = scalar_values,
           claim_refs = scalar_refs
     WHERE project_id = target_project_id;
END;
$$;

DO $$
DECLARE
    stale_project RECORD;
BEGIN
    FOR stale_project IN
        SELECT p.project_id
          FROM agency_projects p
         WHERE EXISTS (
                   SELECT 1
                     FROM agency_project_claims c
                    WHERE c.project_id = p.project_id
                      AND c.status <> 'retired'
                      AND NOT EXISTS (
                          SELECT 1 FROM agency_project_claims newer
                           WHERE newer.supersedes = c.claim_id
                      )
               )
           AND (
               p.claim_refs = '{}'::jsonb
               OR p.claim_refs::text NOT LIKE '%"certainty"%'
           )
    LOOP
        PERFORM refresh_agency_project_claim_projection(stale_project.project_id);
    END LOOP;
END;
$$;
