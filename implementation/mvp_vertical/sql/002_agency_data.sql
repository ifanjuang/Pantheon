CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS agency_projects (
    project_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT,
    phase TEXT,
    location TEXT,
    primary_client TEXT,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    contacts JSONB NOT NULL DEFAULT '[]'::jsonb,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    claim_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    claim_refs JSONB NOT NULL DEFAULT '{}'::jsonb,
    owner_system TEXT NOT NULL DEFAULT 'postgres' CHECK (owner_system = 'postgres'),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Existing development databases may predate the extensible Project fields.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agency_projects' AND column_name = 'contacts') THEN
        ALTER TABLE agency_projects ADD COLUMN contacts JSONB NOT NULL DEFAULT '[]'::jsonb;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agency_projects' AND column_name = 'attributes') THEN
        ALTER TABLE agency_projects ADD COLUMN attributes JSONB NOT NULL DEFAULT '{}'::jsonb;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agency_projects' AND column_name = 'claim_values') THEN
        ALTER TABLE agency_projects ADD COLUMN claim_values JSONB NOT NULL DEFAULT '{}'::jsonb;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agency_projects' AND column_name = 'claim_refs') THEN
        ALTER TABLE agency_projects ADD COLUMN claim_refs JSONB NOT NULL DEFAULT '{}'::jsonb;
    END IF;
END;
$$;

-- Pre-production cleanup: consequential values formerly stored as unqualified
-- Project attributes are deliberately removed instead of maintaining two source
-- models. New values live only as ProjectClaims. Descriptive attributes remain.
UPDATE agency_projects
   SET attributes = attributes - ARRAY[
       'budget',
       'surface_terrain',
       'surface_existante',
       'surface_projet',
       'emprise',
       'parcelles',
       'plu_zone',
       'permit_number',
       'permit_date',
       'reception_date',
       'erp_type'
   ]::text[]
 WHERE attributes ?| ARRAY[
       'budget',
       'surface_terrain',
       'surface_existante',
       'surface_projet',
       'emprise',
       'parcelles',
       'plu_zone',
       'permit_number',
       'permit_date',
       'reception_date',
       'erp_type'
   ];

CREATE INDEX IF NOT EXISTS agency_projects_code_lookup
    ON agency_projects (lower(code));
CREATE INDEX IF NOT EXISTS agency_projects_name_lookup
    ON agency_projects (lower(display_name));

-- People and Organizations remain optional directory sources. They are not
-- related to projects by a participation table; each Project owns its current
-- contacts snapshot in agency_projects.contacts.
CREATE TABLE IF NOT EXISTS agency_people (
    person_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    owner_system TEXT NOT NULL DEFAULT 'postgres' CHECK (owner_system = 'postgres'),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agency_organizations (
    organization_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    siret TEXT,
    owner_system TEXT NOT NULL DEFAULT 'postgres' CHECK (owner_system = 'postgres'),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Retired legacy model. This repository is still pre-production; keeping a
-- second project/contact model would create sync ambiguity, so schema init
-- removes the obsolete relation table when upgrading an existing dev database.
DROP TABLE IF EXISTS agency_project_participations;

-- Unified Information card. A source revision owns one visible index. Editing
-- summary/details never changes that index. Once acted, the row is immutable at
-- the domain layer; a later source creates one new working row in the same series.
CREATE TABLE IF NOT EXISTS agency_information_cards (
    information_id TEXT PRIMARY KEY,
    series_id TEXT NOT NULL,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT,
    source_note TEXT,
    source_version TEXT,
    index_label TEXT NOT NULL,
    information_date DATE,
    summary TEXT NOT NULL DEFAULT '',
    details TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'in_progress', 'acted', 'superseded')),
    limits JSONB NOT NULL DEFAULT '[]'::jsonb,
    type_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    subject_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    author TEXT,
    base_acted_id TEXT REFERENCES agency_information_cards(information_id) ON DELETE RESTRICT,
    previous_source_id TEXT REFERENCES agency_information_cards(information_id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acted_at TIMESTAMPTZ,
    CHECK (source_ref IS NOT NULL OR source_note IS NOT NULL),
    CHECK ((status = 'acted' AND acted_at IS NOT NULL) OR status <> 'acted')
);

CREATE INDEX IF NOT EXISTS agency_information_project_lookup
    ON agency_information_cards (project_id, series_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS agency_information_one_working_version
    ON agency_information_cards (series_id)
    WHERE status IN ('draft', 'in_progress');

CREATE UNIQUE INDEX IF NOT EXISTS agency_information_one_current_acted
    ON agency_information_cards (series_id)
    WHERE status = 'acted';

-- ProjectClaim is semantic backend state, not a Cockpit card family. Rows are
-- append-only semantic observations: a new value supersedes an older claim
-- instead of rewriting provenance in place.
CREATE TABLE IF NOT EXISTS agency_project_claims (
    claim_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL,
    value JSONB NOT NULL,
    unit TEXT,
    backing_entity_type TEXT,
    backing_entity_id TEXT,
    backing_observed_status TEXT,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('information', 'document', 'human_assertion', 'derived', 'external_projection')),
    source_ref TEXT,
    asserted_by TEXT,
    derivation_note TEXT,
    status TEXT NOT NULL CHECK (status IN ('asserted', 'source_backed', 'verified', 'contested', 'retired')),
    observed_at TIMESTAMPTZ NOT NULL,
    revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
    supersedes TEXT REFERENCES agency_project_claims(claim_id) ON DELETE RESTRICT,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        status NOT IN ('source_backed', 'verified')
        OR (backing_entity_type IS NOT NULL AND backing_entity_id IS NOT NULL)
    ),
    CHECK (
        (backing_entity_type IS NULL AND backing_entity_id IS NULL)
        OR (backing_entity_type IS NOT NULL AND backing_entity_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS agency_project_claims_project_lookup
    ON agency_project_claims (project_id, claim_type, observed_at DESC, created_at DESC);

-- claim_values / claim_refs are derived read caches only. They are refreshed from
-- the append-only claim store, never accepted as Project writes and never bump the
-- Project business revision. This avoids N+1 queries for list/Cockpit reads while
-- preserving ProjectClaim as the semantic source.
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
        SELECT DISTINCT ON (c.claim_type)
               c.*
          FROM agency_project_claims c
         WHERE c.project_id = target_project_id
           AND c.claim_type <> 'parcelle'
           AND c.status <> 'retired'
           AND NOT EXISTS (
               SELECT 1
                 FROM agency_project_claims newer
                WHERE newer.supersedes = c.claim_id
           )
         ORDER BY c.claim_type, c.observed_at DESC, c.created_at DESC, c.claim_id DESC
    ), projected AS (
        SELECT claim_type,
               value,
               jsonb_build_object(
                   'claim_id', claim_id,
                   'status', status,
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
                       'asserted_by', asserted_by,
                       'derivation_note', derivation_note
                   ),
                   'observed_at', observed_at
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
               SELECT 1
                 FROM agency_project_claims newer
                WHERE newer.supersedes = c.claim_id
           )
         ORDER BY c.observed_at DESC, c.created_at DESC, c.claim_id DESC
    )
    SELECT COALESCE(jsonb_agg(value), '[]'::jsonb),
           COALESCE(jsonb_agg(jsonb_build_object(
               'claim_id', claim_id,
               'status', status,
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
                   'asserted_by', asserted_by,
                   'derivation_note', derivation_note
               ),
               'observed_at', observed_at
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

CREATE OR REPLACE FUNCTION refresh_agency_project_claim_projection_after_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM refresh_agency_project_claim_projection(NEW.project_id);
    RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS agency_project_events (
    event_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('project_created', 'project_updated')),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'hermes', 'system')),
    expected_revision INTEGER NOT NULL CHECK (expected_revision >= 0),
    resulting_revision INTEGER NOT NULL CHECK (resulting_revision = expected_revision + 1),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

-- A ChangeCandidate is an envelope around a proposed Project-attributes change.
-- Claim projections are not plain attributes and cannot be mutated through this
-- table. The Project keeps its own business status; candidate status never replaces it.
CREATE TABLE IF NOT EXISTS agency_change_candidates (
    candidate_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK (entity_type = 'project'),
    entity_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    base_revision INTEGER NOT NULL CHECK (base_revision >= 1),
    proposer TEXT NOT NULL,
    proposer_kind TEXT NOT NULL CHECK (proposer_kind IN ('human', 'hermes', 'system')),
    changes JSONB NOT NULL,
    reason TEXT,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    proposal_digest TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending_review', 'applied', 'rejected', 'stale')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMPTZ,
    decided_by TEXT,
    applied_revision INTEGER,
    CHECK (jsonb_typeof(changes) = 'array'),
    CHECK (jsonb_typeof(source_refs) = 'array')
);

CREATE INDEX IF NOT EXISTS agency_change_candidates_project_lookup
    ON agency_change_candidates (entity_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS agency_change_candidate_events (
    event_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL REFERENCES agency_change_candidates(candidate_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('proposed', 'applied', 'rejected', 'stale')),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'hermes', 'system')),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION reject_agency_project_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'agency_project_events are append-only';
END;
$$;

CREATE OR REPLACE FUNCTION reject_agency_change_candidate_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'agency_change_candidate_events are append-only';
END;
$$;

CREATE OR REPLACE FUNCTION reject_agency_project_claim_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'agency_project_claims are append-only; create a superseding claim';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_project_events_no_update'
          AND tgrelid = 'agency_project_events'::regclass
    ) THEN
        CREATE TRIGGER agency_project_events_no_update
        BEFORE UPDATE ON agency_project_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_project_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_project_events_no_delete'
          AND tgrelid = 'agency_project_events'::regclass
    ) THEN
        CREATE TRIGGER agency_project_events_no_delete
        BEFORE DELETE ON agency_project_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_project_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_change_candidate_events_no_update'
          AND tgrelid = 'agency_change_candidate_events'::regclass
    ) THEN
        CREATE TRIGGER agency_change_candidate_events_no_update
        BEFORE UPDATE ON agency_change_candidate_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_change_candidate_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_change_candidate_events_no_delete'
          AND tgrelid = 'agency_change_candidate_events'::regclass
    ) THEN
        CREATE TRIGGER agency_change_candidate_events_no_delete
        BEFORE DELETE ON agency_change_candidate_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_change_candidate_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_project_claims_no_update'
          AND tgrelid = 'agency_project_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_project_claims_no_update
        BEFORE UPDATE ON agency_project_claims
        FOR EACH ROW EXECUTE FUNCTION reject_agency_project_claim_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_project_claims_no_delete'
          AND tgrelid = 'agency_project_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_project_claims_no_delete
        BEFORE DELETE ON agency_project_claims
        FOR EACH ROW EXECUTE FUNCTION reject_agency_project_claim_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'agency_project_claims_refresh_projection'
          AND tgrelid = 'agency_project_claims'::regclass
    ) THEN
        CREATE TRIGGER agency_project_claims_refresh_projection
        AFTER INSERT ON agency_project_claims
        FOR EACH ROW EXECUTE FUNCTION refresh_agency_project_claim_projection_after_insert();
    END IF;
END;
$$;

-- Rebuild derived caches for any pre-existing claim rows after an upgrade.
DO $$
DECLARE
    project_row RECORD;
BEGIN
    FOR project_row IN SELECT DISTINCT project_id FROM agency_project_claims LOOP
        PERFORM refresh_agency_project_claim_projection(project_row.project_id);
    END LOOP;
END;
$$;

-- CURRENT_TIMESTAMP is the transaction start time, so events written in one
-- transaction share an occurred_at and cannot be ordered by it. clock_timestamp()
-- advances per statement. Applied here for the same reason as in 001_work_issues,
-- where the defect is demonstrated: no path in this file writes two events at once
-- today, and the point is that adding one must not silently lose their order.
-- Guarded on the value this adds, so a started-up installation performs a catalog
-- read only.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_project_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE agency_project_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_change_candidate_events'
           AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE agency_change_candidate_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;
