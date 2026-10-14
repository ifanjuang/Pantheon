-- A4b: append-only implementation journal for professional document-version
-- status/effect posture. This is not a Proof Register, Evidence store or
-- approval engine. Consequential authority statuses are deliberately refused
-- at the database boundary until a separately governed authority basis exists.

CREATE TABLE IF NOT EXISTS doc_document_version_effect_events (
    event_id TEXT PRIMARY KEY,
    document_version_id TEXT NOT NULL
        REFERENCES doc_document_versions(version_id) ON DELETE RESTRICT,
    event_seq INTEGER NOT NULL CHECK (event_seq > 0),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'created', 'issued', 'approved', 'signed', 'superseded',
        'marked_obsolete', 'reopened', 'corrected',
        'reclassified_effect_class', 'withdrawn', 'rejected'
    )),
    previous_status TEXT CHECK (
        previous_status IS NULL OR previous_status IN (
            'draft', 'issued', 'under_review', 'approved', 'signed',
            'effective', 'superseded', 'obsolete', 'rejected', 'withdrawn'
        )
    ),
    new_status TEXT NOT NULL CHECK (new_status IN (
        'draft', 'issued', 'under_review', 'approved', 'signed',
        'effective', 'superseded', 'obsolete', 'rejected', 'withdrawn'
    )),
    previous_effect_class TEXT CHECK (
        previous_effect_class IS NULL OR previous_effect_class IN (
            'working_revision', 'minor_correction', 'coordination_update',
            'modification_candidate', 'issued_for_review',
            'issued_for_client_approval', 'approved_phase_decision',
            'issued_for_consultation', 'issued_for_contract',
            'signed_contractual_version', 'issued_for_execution',
            'issued_for_site', 'visa_status_record',
            'signed_or_contradictory_record', 'as_built_record',
            'obsolete_superseded'
        )
    ),
    new_effect_class TEXT NOT NULL CHECK (new_effect_class IN (
        'working_revision', 'minor_correction', 'coordination_update',
        'modification_candidate', 'issued_for_review',
        'issued_for_client_approval', 'approved_phase_decision',
        'issued_for_consultation', 'issued_for_contract',
        'signed_contractual_version', 'issued_for_execution',
        'issued_for_site', 'visa_status_record',
        'signed_or_contradictory_record', 'as_built_record',
        'obsolete_superseded'
    )),
    previous_authority_status TEXT CHECK (
        previous_authority_status IS NULL OR previous_authority_status IN (
            'not_authoritative', 'internal_working_authority',
            'internal_review_authority', 'client_review_authority',
            'phase_approval_authority', 'consultation_authority',
            'execution_authority', 'site_record_authority',
            'contractual_authority', 'as_built_authority',
            'historical_evidence_only'
        )
    ),
    new_authority_status TEXT NOT NULL CHECK (new_authority_status IN (
        'not_authoritative', 'internal_working_authority',
        'internal_review_authority', 'client_review_authority',
        'historical_evidence_only'
    )),
    reason TEXT,
    basis_refs JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(basis_refs) = 'array'),
    actor TEXT NOT NULL CHECK (btrim(actor) <> ''),
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'system')),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL CHECK (payload_digest ~ '^[a-f0-9]{64}$'),
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (document_version_id, event_seq)
);

CREATE INDEX IF NOT EXISTS doc_document_version_effect_events_revision_lookup
    ON doc_document_version_effect_events
       (document_version_id, event_seq DESC, event_id);

CREATE OR REPLACE FUNCTION reject_doc_document_version_effect_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'doc_document_version_effect_events is append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'doc_document_version_effect_events_append_only'
           AND tgrelid = 'doc_document_version_effect_events'::regclass
    ) THEN
        CREATE TRIGGER doc_document_version_effect_events_append_only
        BEFORE UPDATE OR DELETE ON doc_document_version_effect_events
        FOR EACH ROW EXECUTE FUNCTION reject_doc_document_version_effect_event_mutation();
    END IF;
END;
$$;

COMMENT ON TABLE doc_document_version_effect_events IS
    'Append-only implementation journal for document revision status/effect posture. Rows do not constitute Proof, Evidence or consequential professional authority.';