-- Bounded cross-family references to stable APU object identities.
--
-- Decision Requests own immutable scope refs. ProjectClaims continue to use their
-- existing backing_ref. Neither carrier creates an APU domain relation, transfers
-- authority, admits Evidence, confirms professional identity or mutates the APU.

CREATE TABLE IF NOT EXISTS agency_decision_request_scope_refs (
    request_id TEXT NOT NULL
        REFERENCES agency_decision_requests(request_id) ON DELETE RESTRICT,
    entity_type TEXT NOT NULL CHECK (entity_type = 'apu_object'),
    entity_id TEXT NOT NULL
        REFERENCES agency_apu_objects(object_id) ON DELETE RESTRICT,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (request_id, entity_type, entity_id),
    UNIQUE (request_id, ordinal)
);

CREATE INDEX IF NOT EXISTS decision_request_scope_apu_lookup
    ON agency_decision_request_scope_refs (entity_type, entity_id, request_id);

CREATE OR REPLACE FUNCTION validate_decision_request_apu_scope_ref()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    request_project_id TEXT;
    object_project_id TEXT;
BEGIN
    SELECT project_id
      INTO request_project_id
      FROM agency_decision_requests
     WHERE request_id = NEW.request_id;

    IF request_project_id IS NULL THEN
        RAISE EXCEPTION 'APU-scoped Decision Request requires a Project classification';
    END IF;

    SELECT project_id
      INTO object_project_id
      FROM agency_apu_objects
     WHERE object_id = NEW.entity_id;

    IF object_project_id IS NULL THEN
        RAISE EXCEPTION 'unknown APU scope object: %', NEW.entity_id;
    END IF;
    IF object_project_id <> request_project_id THEN
        RAISE EXCEPTION
            'Decision Request APU scope object % belongs to another Project', NEW.entity_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION reject_decision_request_scope_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Decision Request scope refs are immutable and retained';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'decision_request_scope_ref_guard'
           AND tgrelid = 'agency_decision_request_scope_refs'::regclass
    ) THEN
        CREATE TRIGGER decision_request_scope_ref_guard
        BEFORE INSERT ON agency_decision_request_scope_refs
        FOR EACH ROW EXECUTE FUNCTION validate_decision_request_apu_scope_ref();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'decision_request_scope_refs_no_update'
           AND tgrelid = 'agency_decision_request_scope_refs'::regclass
    ) THEN
        CREATE TRIGGER decision_request_scope_refs_no_update
        BEFORE UPDATE OR DELETE ON agency_decision_request_scope_refs
        FOR EACH ROW EXECUTE FUNCTION reject_decision_request_scope_mutation();
    END IF;
END;
$$;

-- Any ProjectClaim may cite an APU object through the already-existing backing_ref,
-- but the backing object must exist in the exact Claim Project.
CREATE OR REPLACE FUNCTION validate_project_claim_apu_backing_ref()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    backing_project_id TEXT;
BEGIN
    IF NEW.backing_entity_type IS DISTINCT FROM 'apu_object' THEN
        RETURN NEW;
    END IF;

    SELECT project_id
      INTO backing_project_id
      FROM agency_apu_objects
     WHERE object_id = NEW.backing_entity_id;

    IF backing_project_id IS NULL THEN
        RAISE EXCEPTION 'ProjectClaim references an unknown APU backing object';
    END IF;
    IF backing_project_id <> NEW.project_id THEN
        RAISE EXCEPTION 'ProjectClaim APU backing must belong to the Claim Project';
    END IF;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_project_claims_validate_apu_backing'
           AND tgrelid = 'agency_project_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_project_claims_validate_apu_backing
        BEFORE INSERT ON agency_project_claims
        FOR EACH ROW EXECUTE FUNCTION validate_project_claim_apu_backing_ref();
    END IF;
END;
$$;

-- Evolve the tranche-F candidate validation in place. The ProjectClaim schema has
-- always allowed a governed semantic backing_ref; this slice opens only apu_object in
-- addition to the already executable project/information cases.
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
        IF NEW.backing_entity_type NOT IN ('project', 'information', 'apu_object') THEN
            RAISE EXCEPTION
                'candidate-backed Claim admits only project, information or apu_object backing';
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
        ELSIF NEW.backing_entity_type = 'information' THEN
            SELECT project_id
              INTO backing_project_id
              FROM agency_information_cards
             WHERE information_id = NEW.backing_entity_id;
            IF backing_project_id IS NULL OR backing_project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'ProjectClaim information backing must belong to the Claim Project';
            END IF;
        ELSE
            SELECT project_id
              INTO backing_project_id
              FROM agency_apu_objects
             WHERE object_id = NEW.backing_entity_id;
            IF backing_project_id IS NULL OR backing_project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'ProjectClaim APU backing must belong to the Claim Project';
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;
