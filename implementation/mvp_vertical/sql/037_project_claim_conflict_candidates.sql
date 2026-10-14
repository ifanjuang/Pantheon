-- P3: bounded ProjectClaim conflict candidates.
--
-- This migration persists unresolved pairwise tensions only. It stores references
-- to immutable ProjectClaims rather than duplicating their values or provenance.
-- It does not mutate ProjectClaims, admit Evidence, create Decisions, resolve
-- conflicts, authorize effects or merge identity.

CREATE TABLE IF NOT EXISTS agency_project_claim_conflict_candidates (
    conflict_candidate_id TEXT PRIMARY KEY CHECK (
        conflict_candidate_id ~ '^pcc-[a-f0-9]{24}$'
    ),
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id),
    claim_type TEXT NOT NULL,
    left_claim_id TEXT NOT NULL REFERENCES agency_project_claims(claim_id),
    right_claim_id TEXT NOT NULL REFERENCES agency_project_claims(claim_id),
    classification TEXT NOT NULL CHECK (
        classification IN (
            'value_conflict_same_effective_start',
            'value_conflict_undated',
            'temporal_ambiguity'
        )
    ),
    detector_id TEXT NOT NULL CHECK (
        detector_id = 'project_claim_pairwise_conflict'
    ),
    detector_version TEXT NOT NULL CHECK (detector_version = '1'),
    submitted_by TEXT NOT NULL CHECK (btrim(submitted_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (left_claim_id < right_claim_id)
);

CREATE INDEX IF NOT EXISTS agency_project_claim_conflicts_project_idx
    ON agency_project_claim_conflict_candidates(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS agency_project_claim_conflicts_type_idx
    ON agency_project_claim_conflict_candidates(project_id, claim_type, created_at DESC);

CREATE INDEX IF NOT EXISTS agency_project_claim_conflicts_pair_idx
    ON agency_project_claim_conflict_candidates(left_claim_id, right_claim_id, created_at DESC);

CREATE OR REPLACE FUNCTION validate_agency_project_claim_conflict_pair()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    left_project TEXT;
    right_project TEXT;
    left_type TEXT;
    right_type TEXT;
    left_status TEXT;
    right_status TEXT;
    left_value JSONB;
    right_value JSONB;
    left_unit TEXT;
    right_unit TEXT;
    left_effective TIMESTAMPTZ;
    right_effective TIMESTAMPTZ;
    expected_classification TEXT;
BEGIN
    SELECT project_id, claim_type, status, value, unit, effective_at
      INTO left_project, left_type, left_status, left_value, left_unit, left_effective
      FROM agency_project_claims
     WHERE claim_id = NEW.left_claim_id;

    SELECT project_id, claim_type, status, value, unit, effective_at
      INTO right_project, right_type, right_status, right_value, right_unit, right_effective
      FROM agency_project_claims
     WHERE claim_id = NEW.right_claim_id;

    IF left_project IS NULL OR right_project IS NULL THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate references an unknown Claim';
    END IF;
    IF left_project <> NEW.project_id OR right_project <> NEW.project_id THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate Claims must belong to the declared Project';
    END IF;
    IF left_type <> NEW.claim_type OR right_type <> NEW.claim_type THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate Claims must share the declared claim_type';
    END IF;
    IF left_status = 'retired' OR right_status = 'retired' THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate cannot bind a retired Claim';
    END IF;
    IF EXISTS (
        SELECT 1
          FROM agency_project_claims newer
         WHERE newer.supersedes IN (NEW.left_claim_id, NEW.right_claim_id)
    ) THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate must bind unsuperseded Claims';
    END IF;
    IF left_unit IS DISTINCT FROM right_unit THEN
        RAISE EXCEPTION 'same-type ProjectClaims carry different governed units; this is a Claim integrity violation';
    END IF;
    IF left_value IS NOT DISTINCT FROM right_value THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate requires a value tension';
    END IF;

    IF left_effective IS NOT NULL
       AND right_effective IS NOT NULL
       AND left_effective = right_effective THEN
        expected_classification := 'value_conflict_same_effective_start';
    ELSIF left_effective IS NULL AND right_effective IS NULL THEN
        expected_classification := 'value_conflict_undated';
    ELSE
        expected_classification := 'temporal_ambiguity';
    END IF;

    IF NEW.classification <> expected_classification THEN
        RAISE EXCEPTION 'ProjectClaim conflict candidate classification does not match Claim time semantics';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agency_project_claim_conflicts_validate_pair
    ON agency_project_claim_conflict_candidates;
CREATE TRIGGER agency_project_claim_conflicts_validate_pair
BEFORE INSERT ON agency_project_claim_conflict_candidates
FOR EACH ROW
EXECUTE FUNCTION validate_agency_project_claim_conflict_pair();

CREATE OR REPLACE FUNCTION reject_agency_project_claim_conflict_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'ProjectClaim conflict candidates are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_project_claim_conflicts_no_update'
           AND tgrelid = 'agency_project_claim_conflict_candidates'::regclass
    ) THEN
        CREATE TRIGGER agency_project_claim_conflicts_no_update
        BEFORE UPDATE ON agency_project_claim_conflict_candidates
        FOR EACH ROW EXECUTE FUNCTION reject_agency_project_claim_conflict_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_project_claim_conflicts_no_delete'
           AND tgrelid = 'agency_project_claim_conflict_candidates'::regclass
    ) THEN
        CREATE TRIGGER agency_project_claim_conflicts_no_delete
        BEFORE DELETE ON agency_project_claim_conflict_candidates
        FOR EACH ROW EXECUTE FUNCTION reject_agency_project_claim_conflict_mutation();
    END IF;
END;
$$;
