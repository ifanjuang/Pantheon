-- Split informational human responses from governed Decision records.
--
-- A question resolves to one immutable HumanResponse. Validation, approval and
-- arbitration continue to resolve to one immutable decision_record. Neither
-- artifact resumes runtime execution, transitions a WorkIssue, admits Evidence
-- or grants authority by itself.
--
-- Historical question -> Decision rows are not reinterpreted automatically.
-- Their meaning cannot be recovered safely from storage shape alone, so this
-- migration fails closed and requires explicit human reclassification first.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM agency_decision_requests
         WHERE status = 'resolved'
           AND decision_type = 'question'
           AND resolved_decision_id IS NOT NULL
    ) THEN
        RAISE EXCEPTION
            'resolved legacy question Decision Requests require explicit human reclassification before HumanResponse migration';
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS agency_human_responses (
    response_id TEXT PRIMARY KEY CHECK (response_id ~ '^[a-z0-9][a-z0-9._-]*$'),
    request_id TEXT NOT NULL UNIQUE
        REFERENCES agency_decision_requests(request_id) ON DELETE RESTRICT,
    responded_by TEXT NOT NULL,
    identity_assurance TEXT NOT NULL CHECK (
        identity_assurance IN ('declared', 'authenticated')
    ),
    authenticated_principal JSONB,
    selected_option_ids JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (
        jsonb_typeof(selected_option_ids) = 'array'
    ),
    response_text TEXT CHECK (
        response_text IS NULL OR length(response_text) BETWEEN 1 AND 20000
    ),
    candidate_digest TEXT NOT NULL CHECK (candidate_digest ~ '^[a-f0-9]{64}$'),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (
        (identity_assurance = 'declared' AND authenticated_principal IS NULL)
        OR
        (identity_assurance = 'authenticated'
         AND authenticated_principal IS NOT NULL
         AND jsonb_typeof(authenticated_principal) = 'object')
    ),
    CHECK (
        response_text IS NOT NULL OR jsonb_array_length(selected_option_ids) > 0
    )
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_decision_requests'
           AND column_name = 'resolved_response_id'
    ) THEN
        ALTER TABLE agency_decision_requests
            ADD COLUMN resolved_response_id TEXT;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_decision_events'
           AND column_name = 'response_id'
    ) THEN
        ALTER TABLE agency_decision_events
            ADD COLUMN response_id TEXT;
    END IF;
END;
$$;

DO $$
DECLARE
    legacy_constraint RECORD;
BEGIN
    FOR legacy_constraint IN
        SELECT conname
          FROM pg_constraint
         WHERE conrelid = 'agency_decision_requests'::regclass
           AND contype = 'c'
           AND conname <> 'agency_decision_requests_resolution_check'
           AND pg_get_constraintdef(oid) LIKE '%resolved_decision_id IS NOT NULL%'
           AND pg_get_constraintdef(oid) LIKE '%cancelled_by IS NOT NULL%'
    LOOP
        EXECUTE format(
            'ALTER TABLE agency_decision_requests DROP CONSTRAINT %I',
            legacy_constraint.conname
        );
    END LOOP;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_decision_requests'::regclass
           AND conname = 'agency_decision_requests_resolution_check'
    ) THEN
        ALTER TABLE agency_decision_requests
            ADD CONSTRAINT agency_decision_requests_resolution_check
            CHECK (
                (status = 'pending'
                 AND resolved_decision_id IS NULL
                 AND resolved_response_id IS NULL
                 AND resolved_at IS NULL
                 AND cancelled_by IS NULL
                 AND cancelled_at IS NULL)
                OR
                (status = 'resolved'
                 AND decision_type = 'question'
                 AND resolved_decision_id IS NULL
                 AND resolved_response_id IS NOT NULL
                 AND resolved_at IS NOT NULL
                 AND cancelled_by IS NULL
                 AND cancelled_at IS NULL)
                OR
                (status = 'resolved'
                 AND decision_type IN ('validation', 'approval', 'arbitration')
                 AND resolved_decision_id IS NOT NULL
                 AND resolved_response_id IS NULL
                 AND resolved_at IS NOT NULL
                 AND cancelled_by IS NULL
                 AND cancelled_at IS NULL)
                OR
                (status = 'cancelled'
                 AND resolved_decision_id IS NULL
                 AND resolved_response_id IS NULL
                 AND resolved_at IS NULL
                 AND cancelled_by IS NOT NULL
                 AND cancelled_at IS NOT NULL)
            ) NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_decision_requests'::regclass
           AND conname = 'agency_decision_requests_resolution_check'
           AND NOT convalidated
    ) THEN
        ALTER TABLE agency_decision_requests
            VALIDATE CONSTRAINT agency_decision_requests_resolution_check;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_decision_requests'::regclass
           AND conname = 'agency_decision_requests_resolved_response_fk'
    ) THEN
        ALTER TABLE agency_decision_requests
            ADD CONSTRAINT agency_decision_requests_resolved_response_fk
            FOREIGN KEY (resolved_response_id)
            REFERENCES agency_human_responses(response_id)
            ON DELETE RESTRICT
            DEFERRABLE INITIALLY DEFERRED;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_decision_events'::regclass
           AND conname = 'agency_decision_events_response_fk'
    ) THEN
        ALTER TABLE agency_decision_events
            ADD CONSTRAINT agency_decision_events_response_fk
            FOREIGN KEY (response_id)
            REFERENCES agency_human_responses(response_id)
            ON DELETE RESTRICT;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION validate_human_response_request()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    request_type TEXT;
    request_digest TEXT;
BEGIN
    SELECT decision_type, candidate_digest
      INTO request_type, request_digest
      FROM agency_decision_requests
     WHERE request_id = NEW.request_id;

    IF request_type IS NULL THEN
        RAISE EXCEPTION 'HumanResponse requires an existing Decision Request';
    END IF;
    IF request_type <> 'question' THEN
        RAISE EXCEPTION 'HumanResponse may resolve only a question Decision Request';
    END IF;
    IF request_digest IS DISTINCT FROM NEW.candidate_digest THEN
        RAISE EXCEPTION 'HumanResponse candidate digest must match its Decision Request';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION validate_decision_record_request_type()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    request_type TEXT;
BEGIN
    SELECT decision_type
      INTO request_type
      FROM agency_decision_requests
     WHERE request_id = NEW.request_id;

    IF request_type = 'question' THEN
        RAISE EXCEPTION 'question Decision Requests resolve to HumanResponse, not Decision records';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS human_responses_validate_request
    ON agency_human_responses;
CREATE TRIGGER human_responses_validate_request
BEFORE INSERT ON agency_human_responses
FOR EACH ROW
EXECUTE FUNCTION validate_human_response_request();

DROP TRIGGER IF EXISTS human_responses_no_update
    ON agency_human_responses;
CREATE TRIGGER human_responses_no_update
BEFORE UPDATE OR DELETE ON agency_human_responses
FOR EACH ROW
EXECUTE FUNCTION reject_decision_immutable_mutation();

DROP TRIGGER IF EXISTS decision_records_validate_request_type
    ON agency_decision_records;
CREATE TRIGGER decision_records_validate_request_type
BEFORE INSERT ON agency_decision_records
FOR EACH ROW
EXECUTE FUNCTION validate_decision_record_request_type();
