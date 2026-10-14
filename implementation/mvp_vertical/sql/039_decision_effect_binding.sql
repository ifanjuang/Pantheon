-- Bind consequential Decisions to the exact effect material presented before review.
--
-- DecisionRequest owns the proposed bounds. DecisionRecord snapshots those bounds
-- when the human decides. The effect owner may later derive an EffectExpectation,
-- but it may not manufacture or mutate any Decision field.
--
-- A signature authenticates the issuer over the immutable Decision bounds. It is
-- not an approval and does not authorize execution by itself.

ALTER TABLE agency_decision_requests
    ADD COLUMN IF NOT EXISTS approval_level TEXT,
    ADD COLUMN IF NOT EXISTS decision_scope JSONB,
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

ALTER TABLE agency_decision_records
    ADD COLUMN IF NOT EXISTS approval_level TEXT,
    ADD COLUMN IF NOT EXISTS scope JSONB,
    ADD COLUMN IF NOT EXISTS object_identity TEXT,
    ADD COLUMN IF NOT EXISTS content_digest TEXT,
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS signature TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_decision_requests'::regclass
           AND conname = 'agency_decision_requests_effect_binding_check'
    ) THEN
        ALTER TABLE agency_decision_requests
            ADD CONSTRAINT agency_decision_requests_effect_binding_check
            CHECK (
                (
                    approval_level IS NULL
                    AND decision_scope IS NULL
                    AND expires_at IS NULL
                )
                OR
                (
                    decision_type <> 'question'
                    AND approval_level ~ '^C[0-5]$'
                    AND decision_scope IS NOT NULL
                    AND jsonb_typeof(decision_scope) = 'object'
                    AND nullif(decision_scope->>'scope_type', '') IS NOT NULL
                    AND nullif(decision_scope->>'scope_id', '') IS NOT NULL
                    AND expires_at IS NOT NULL
                    AND expires_at > created_at
                )
            ) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_decision_records'::regclass
           AND conname = 'agency_decision_records_effect_binding_check'
    ) THEN
        ALTER TABLE agency_decision_records
            ADD CONSTRAINT agency_decision_records_effect_binding_check
            CHECK (
                (
                    approval_level IS NULL
                    AND scope IS NULL
                    AND object_identity IS NULL
                    AND content_digest IS NULL
                    AND expires_at IS NULL
                    AND signature IS NULL
                )
                OR
                (
                    approval_level ~ '^C[0-5]$'
                    AND scope IS NOT NULL
                    AND jsonb_typeof(scope) = 'object'
                    AND nullif(scope->>'scope_type', '') IS NOT NULL
                    AND nullif(scope->>'scope_id', '') IS NOT NULL
                    AND nullif(object_identity, '') IS NOT NULL
                    AND content_digest ~ '^[a-f0-9]{64}$'
                    AND expires_at IS NOT NULL
                    AND (
                        signature IS NULL
                        OR identity_assurance = 'authenticated'
                    )
                )
            ) NOT VALID;
    END IF;

    ALTER TABLE agency_decision_requests
        VALIDATE CONSTRAINT agency_decision_requests_effect_binding_check;
    ALTER TABLE agency_decision_records
        VALIDATE CONSTRAINT agency_decision_records_effect_binding_check;
END;
$$;

CREATE OR REPLACE FUNCTION validate_decision_record_request_type()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    request_type TEXT;
    request_level TEXT;
    request_scope JSONB;
    request_object TEXT;
    request_digest TEXT;
    request_expiry TIMESTAMPTZ;
BEGIN
    SELECT decision_type, approval_level, decision_scope,
           candidate_ref, candidate_digest, expires_at
      INTO request_type, request_level, request_scope,
           request_object, request_digest, request_expiry
      FROM agency_decision_requests
     WHERE request_id = NEW.request_id;

    IF request_type IS NULL THEN
        RAISE EXCEPTION 'Decision record requires an existing Decision Request';
    END IF;
    IF request_type = 'question' THEN
        RAISE EXCEPTION 'question Decision Requests resolve to HumanResponse, not Decision records';
    END IF;

    IF request_level IS NULL THEN
        IF NEW.approval_level IS NOT NULL
           OR NEW.scope IS NOT NULL
           OR NEW.object_identity IS NOT NULL
           OR NEW.content_digest IS NOT NULL
           OR NEW.expires_at IS NOT NULL
           OR NEW.signature IS NOT NULL THEN
            RAISE EXCEPTION 'unbound Decision Request cannot produce effect-bound Decision fields';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.approval_level IS DISTINCT FROM request_level
       OR NEW.scope IS DISTINCT FROM request_scope
       OR NEW.object_identity IS DISTINCT FROM request_object
       OR NEW.content_digest IS DISTINCT FROM request_digest
       OR NEW.expires_at IS DISTINCT FROM request_expiry THEN
        RAISE EXCEPTION 'Decision effect bounds must exactly match the immutable Decision Request';
    END IF;

    IF NEW.signature IS NOT NULL AND NEW.identity_assurance <> 'authenticated' THEN
        RAISE EXCEPTION 'issuer signature requires authenticated human identity assurance';
    END IF;
    RETURN NEW;
END;
$$;
