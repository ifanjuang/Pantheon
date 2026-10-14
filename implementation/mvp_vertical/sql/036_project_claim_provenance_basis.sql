-- P2: preserve the exact structured basis of ProjectClaim candidates.
--
-- This migration adds provenance only. It creates no Claim, admits no Evidence,
-- approves nothing and does not turn a candidate basis into project truth.
-- Existing Claims remain valid and receive an empty basis list because their
-- historical creation path did not persist the candidate's full basis array.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_claims' AND column_name = 'basis_refs'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD COLUMN basis_refs JSONB NOT NULL DEFAULT '[]'::jsonb;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_basis_refs_array_check'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_basis_refs_array_check
            CHECK (jsonb_typeof(basis_refs) = 'array') NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_basis_refs_source_check'
    ) THEN
        ALTER TABLE agency_project_claims
            ADD CONSTRAINT agency_project_claims_basis_refs_source_check
            CHECK (source_kind = 'execution_result' OR basis_refs = '[]'::jsonb)
            NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_basis_refs_array_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_basis_refs_array_check;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_project_claims'::regclass
           AND conname = 'agency_project_claims_basis_refs_source_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_project_claims
            VALIDATE CONSTRAINT agency_project_claims_basis_refs_source_check;
    END IF;
END;
$$;

-- Candidate identity, reviewed disposition, value, unit and time binding remain
-- owned by 019_project_claim_candidates.sql. This trigger adds only the missing
-- provenance invariant: a newly created execution-backed Claim must preserve the
-- candidate's exact immutable basis_refs array.
CREATE OR REPLACE FUNCTION validate_agency_project_claim_candidate_basis_refs()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    candidate_payload JSONB;
BEGIN
    IF NEW.source_kind <> 'execution_result' THEN
        RETURN NEW;
    END IF;

    IF to_regclass('execution_result_items') IS NULL THEN
        RAISE EXCEPTION 'execution result authority is unavailable for ProjectClaim provenance binding';
    END IF;

    SELECT payload
      INTO candidate_payload
      FROM execution_result_items
     WHERE result_id = NEW.candidate_result_id;

    IF candidate_payload IS NULL THEN
        RAISE EXCEPTION 'ProjectClaim provenance candidate result is unavailable';
    END IF;

    IF COALESCE(candidate_payload->'basis_refs', '[]'::jsonb)
       IS DISTINCT FROM NEW.basis_refs THEN
        RAISE EXCEPTION 'ProjectClaim basis_refs must exactly match the reviewed candidate basis_refs';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agency_project_claims_validate_candidate_basis_refs
    ON agency_project_claims;
CREATE TRIGGER agency_project_claims_validate_candidate_basis_refs
BEFORE INSERT ON agency_project_claims
FOR EACH ROW
EXECUTE FUNCTION validate_agency_project_claim_candidate_basis_refs();

-- Refresh the existing Project read cache with structured provenance. The cache
-- remains a rebuildable projection and never becomes a second Claim authority.
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
                       'basis_refs', basis_refs,
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
                   'basis_refs', basis_refs,
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

-- Existing cached projections predate basis_refs. Rebuild only Projects whose
-- cached Claim refs do not yet expose the new provenance field.
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
               )
           AND (
               p.claim_refs = '{}'::jsonb
               OR p.claim_refs::text NOT LIKE '%"basis_refs"%'
           )
    LOOP
        PERFORM refresh_agency_project_claim_projection(stale_project.project_id);
    END LOOP;
END;
$$;
