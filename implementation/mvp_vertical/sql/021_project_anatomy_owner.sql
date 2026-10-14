-- Clean-install Project Anatomy owner.
--
-- The schema installs the sole V0.2 carrier directly. It has no predecessor
-- tables, compatibility projection or owner-upgrade ledger.

CREATE TABLE IF NOT EXISTS agency_apu_project_state (
    project_id TEXT PRIMARY KEY REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    model_version INTEGER NOT NULL DEFAULT 2 CHECK (model_version = 2),
    model_authority_ref TEXT NOT NULL CHECK (btrim(model_authority_ref) <> ''),
    model_doctrine_ref TEXT NOT NULL CHECK (btrim(model_doctrine_ref) <> ''),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

COMMENT ON COLUMN agency_apu_project_state.model_authority_ref IS
    'Exact Project Anatomy validation-contract authority pin.';
COMMENT ON COLUMN agency_apu_project_state.model_doctrine_ref IS
    'Exact Project Anatomy conceptual doctrine pin.';

CREATE TABLE IF NOT EXISTS agency_apu_objects (
    object_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    object_family TEXT NOT NULL CHECK (
        object_family IN (
            'spatial', 'element', 'assembly', 'material',
            'system', 'datum', 'group', 'type_definition'
        )
    ),
    stable_object_payload JSONB NOT NULL CHECK (jsonb_typeof(stable_object_payload) = 'object'),
    payload_digest TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    retired_at TIMESTAMPTZ,
    retired_by TEXT,
    UNIQUE (project_id, object_id),
    CHECK (stable_object_payload ->> 'stable_object_id' = object_id),
    CHECK (stable_object_payload ->> 'project_ref' = project_id),
    CHECK (stable_object_payload ->> 'object_family' = object_family),
    CHECK (
        (retired_at IS NULL AND retired_by IS NULL)
        OR (retired_at IS NOT NULL AND retired_by IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS agency_apu_objects_project_lookup
    ON agency_apu_objects (project_id, retired_at, object_family, object_id);

CREATE TABLE IF NOT EXISTS agency_apu_source_representations (
    representation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    source_kind TEXT NOT NULL CHECK (
        source_kind IN (
            'revit', 'ifc', 'drawing', 'drawing_takeoff', 'image',
            'photo', 'manual', 'scan', 'point_cloud', 'other'
        )
    ),
    proof_status TEXT NOT NULL CHECK (proof_status IN (
        'candidate', 'source_missing', 'source_incomplete', 'source_complete_for_task',
        'source_superseded', 'contradictory_evidence', 'authority_too_low',
        'requires_more_evidence', 'accepted_as_support', 'rejected', 'obsolete', 'superseded'
    )),
    representation_payload JSONB NOT NULL CHECK (jsonb_typeof(representation_payload) = 'object'),
    payload_digest TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (project_id, representation_id),
    CHECK (representation_payload ->> 'representation_id' = representation_id),
    CHECK (representation_payload ->> 'project_ref' = project_id),
    CHECK (representation_payload ->> 'source_kind' = source_kind),
    CHECK (representation_payload ->> 'proof_status' = proof_status)
);

CREATE INDEX IF NOT EXISTS agency_apu_source_representations_project_lookup
    ON agency_apu_source_representations (project_id, source_kind, representation_id);

CREATE TABLE IF NOT EXISTS agency_apu_attribute_claims (
    claim_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    subject_entity_type TEXT NOT NULL CHECK (
        subject_entity_type IN ('stable_object', 'source_representation')
    ),
    subject_entity_id TEXT NOT NULL,
    attribute_key TEXT NOT NULL,
    assertion_mode TEXT NOT NULL CHECK (
        assertion_mode IN ('observed', 'proposed', 'derived', 'human_asserted', 'as_built')
    ),
    source_authority TEXT NOT NULL,
    proof_status TEXT NOT NULL,
    claim_payload JSONB NOT NULL CHECK (jsonb_typeof(claim_payload) = 'object'),
    payload_digest TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (claim_payload ->> 'attribute_claim_id' = claim_id),
    CHECK (claim_payload -> 'subject_ref' ->> 'entity_type' = subject_entity_type),
    CHECK (claim_payload -> 'subject_ref' ->> 'entity_id' = subject_entity_id),
    CHECK (claim_payload ->> 'attribute_key' = attribute_key)
);

CREATE INDEX IF NOT EXISTS agency_apu_attribute_claims_subject_lookup
    ON agency_apu_attribute_claims (project_id, subject_entity_type, subject_entity_id, attribute_key);

CREATE TABLE IF NOT EXISTS agency_apu_relation_claims (
    claim_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    subject_entity_type TEXT NOT NULL CHECK (
        subject_entity_type IN ('stable_object', 'source_representation')
    ),
    subject_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (relation_type ~ '^[a-z][a-z0-9_.-]*$'),
    object_entity_type TEXT NOT NULL CHECK (
        object_entity_type IN ('stable_object', 'source_representation')
    ),
    object_entity_id TEXT NOT NULL,
    assertion_mode TEXT NOT NULL CHECK (
        assertion_mode IN ('observed', 'proposed', 'derived', 'human_asserted', 'as_built')
    ),
    source_authority TEXT NOT NULL,
    proof_status TEXT NOT NULL,
    claim_payload JSONB NOT NULL CHECK (jsonb_typeof(claim_payload) = 'object'),
    payload_digest TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (claim_payload ->> 'relation_claim_id' = claim_id),
    CHECK (claim_payload -> 'subject_ref' ->> 'entity_type' = subject_entity_type),
    CHECK (claim_payload -> 'subject_ref' ->> 'entity_id' = subject_entity_id),
    CHECK (claim_payload ->> 'relation_type' = relation_type),
    CHECK (claim_payload -> 'object_ref' ->> 'entity_type' = object_entity_type),
    CHECK (claim_payload -> 'object_ref' ->> 'entity_id' = object_entity_id),
    CHECK (
        relation_type <> 'identity.represents'
        OR (
            subject_entity_type = 'source_representation'
            AND object_entity_type = 'stable_object'
        )
    )
);

CREATE INDEX IF NOT EXISTS agency_apu_relation_claims_subject_lookup
    ON agency_apu_relation_claims (project_id, subject_entity_type, subject_entity_id, relation_type);
CREATE INDEX IF NOT EXISTS agency_apu_relation_claims_object_lookup
    ON agency_apu_relation_claims (project_id, object_entity_type, object_entity_id, relation_type);

CREATE TABLE IF NOT EXISTS agency_apu_events (
    event_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'reviewed_dossier_imported', 'source_match_applied', 'object_retired'
    )),
    expected_revision INTEGER NOT NULL CHECK (expected_revision >= 0),
    resulting_revision INTEGER NOT NULL CHECK (resulting_revision = expected_revision + 1),
    actor TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
    command_ref TEXT,
    authorization_ref TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS agency_apu_events_project_lookup
    ON agency_apu_events (project_id, occurred_at, event_id);

CREATE OR REPLACE FUNCTION agency_apu_entity_exists(
    expected_project_id TEXT,
    entity_type_value TEXT,
    entity_id_value TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF entity_type_value = 'stable_object' THEN
        RETURN EXISTS (
            SELECT 1 FROM agency_apu_objects
             WHERE project_id = expected_project_id AND object_id = entity_id_value
        );
    ELSIF entity_type_value = 'source_representation' THEN
        RETURN EXISTS (
            SELECT 1 FROM agency_apu_source_representations
             WHERE project_id = expected_project_id AND representation_id = entity_id_value
        );
    END IF;
    RETURN FALSE;
END;
$$;

CREATE OR REPLACE FUNCTION validate_agency_apu_attribute_claim()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT agency_apu_entity_exists(
        NEW.project_id, NEW.subject_entity_type, NEW.subject_entity_id
    ) THEN
        RAISE EXCEPTION 'attribute claim subject is unknown or belongs to another Project';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION validate_agency_apu_relation_claim()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT agency_apu_entity_exists(
        NEW.project_id, NEW.subject_entity_type, NEW.subject_entity_id
    ) THEN
        RAISE EXCEPTION 'relation claim subject is unknown or belongs to another Project';
    END IF;
    IF NOT agency_apu_entity_exists(
        NEW.project_id, NEW.object_entity_type, NEW.object_entity_id
    ) THEN
        RAISE EXCEPTION 'relation claim object is unknown or belongs to another Project';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION reject_agency_apu_append_only_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Project Anatomy event, source and claim records are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_events_no_update'
          AND tgrelid = 'agency_apu_events'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_events_no_update BEFORE UPDATE ON agency_apu_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_apu_append_only_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_events_no_delete'
          AND tgrelid = 'agency_apu_events'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_events_no_delete BEFORE DELETE ON agency_apu_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_apu_append_only_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_attribute_claims_validate'
          AND tgrelid = 'agency_apu_attribute_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_attribute_claims_validate
        BEFORE INSERT ON agency_apu_attribute_claims
        FOR EACH ROW EXECUTE FUNCTION validate_agency_apu_attribute_claim();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_relation_claims_validate'
          AND tgrelid = 'agency_apu_relation_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_relation_claims_validate
        BEFORE INSERT ON agency_apu_relation_claims
        FOR EACH ROW EXECUTE FUNCTION validate_agency_apu_relation_claim();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_source_representations_append_only'
          AND tgrelid = 'agency_apu_source_representations'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_source_representations_append_only
        BEFORE UPDATE OR DELETE ON agency_apu_source_representations
        FOR EACH ROW EXECUTE FUNCTION reject_agency_apu_append_only_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_attribute_claims_append_only'
          AND tgrelid = 'agency_apu_attribute_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_attribute_claims_append_only
        BEFORE UPDATE OR DELETE ON agency_apu_attribute_claims
        FOR EACH ROW EXECUTE FUNCTION reject_agency_apu_append_only_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'agency_apu_relation_claims_append_only'
          AND tgrelid = 'agency_apu_relation_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_apu_relation_claims_append_only
        BEFORE UPDATE OR DELETE ON agency_apu_relation_claims
        FOR EACH ROW EXECUTE FUNCTION reject_agency_apu_append_only_mutation();
    END IF;
END;
$$;
