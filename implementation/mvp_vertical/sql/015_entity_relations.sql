-- Explicit relations keyed by two EntityRef values.
--
-- The physical shape is generic and the endpoint vocabulary is open to every
-- project-scoped type the plan names, so a later tranche adds a resolver arm
-- rather than migrating this constraint. `relation_type` stays closed on the four
-- canonical meanings — that is where the doctrinal control lives.
--
-- A relation is NOT canonical on write. Hermes may propose one; only a human
-- canonizes, rejects or retires it.

CREATE TABLE IF NOT EXISTS agency_entity_relations (
    relation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    from_entity_type TEXT NOT NULL CHECK (from_entity_type IN (
        'project', 'information', 'decision',
        'person', 'organization', 'apu_object'
    )),
    from_entity_id TEXT NOT NULL,
    to_entity_type TEXT NOT NULL CHECK (to_entity_type IN (
        'project', 'information', 'decision',
        'person', 'organization', 'apu_object'
    )),
    to_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN ('responds_to', 'relies_on', 'supersedes', 'contradicts')
    ),
    rationale TEXT,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_refs) = 'array'),
    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed', 'canonical', 'rejected', 'retired')),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    retired_at TIMESTAMPTZ,
    retired_by TEXT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    CHECK (
        from_entity_type <> to_entity_type
        OR from_entity_id <> to_entity_id
    ),
    -- retired_at/retired_by mark the closing decision, whichever it was: a
    -- proposal refused before canonization closes the same way a canonical
    -- relation retired later does. An open relation has neither set.
    CHECK (
        (status IN ('proposed', 'canonical') AND retired_at IS NULL AND retired_by IS NULL)
        OR (status IN ('rejected', 'retired') AND retired_at IS NOT NULL AND retired_by IS NOT NULL)
    )
);

-- Databases created before relations became reviewable carry rows that were
-- canonical the moment they were written, and a schema that cannot express a
-- proposal. Each block below is guarded on the value it adds, so a started-up
-- installation performs catalog reads only.
--
-- The backfill preserves meaning exactly: revision 1 meant active, which under
-- the old rules meant canonical; revision 2 meant retired. Nothing becomes a
-- proposal retroactively — no human ever reviewed these, and pretending they did
-- is the one mapping that would be a lie.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'agency_entity_relations' AND column_name = 'status'
    ) THEN
        -- The scope guard installed by the previous version of this migration
        -- accepts exactly one UPDATE shape: active -> retired, advancing the
        -- revision. A backfill is neither — it is one row keeping its meaning and
        -- gaining a column — so the guard refuses it and the migration dies on the
        -- next boot of every installation that already has rows. Drop it here; the
        -- guarded CREATE TRIGGER further down puts the new one back, and the whole
        -- file runs in one transaction, so no writer ever sees the table unguarded.
        DROP TRIGGER IF EXISTS agency_entity_relations_scope_guard
            ON agency_entity_relations;
        ALTER TABLE agency_entity_relations
            ADD COLUMN status TEXT NOT NULL DEFAULT 'proposed';
        UPDATE agency_entity_relations
           SET status = CASE WHEN retired_at IS NULL THEN 'canonical' ELSE 'retired' END;
        ALTER TABLE agency_entity_relations
            ADD CONSTRAINT agency_entity_relations_status_check
            CHECK (status IN ('proposed', 'canonical', 'rejected', 'retired')) NOT VALID;
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS agency_entity_relations_active_edge_unique
    ON agency_entity_relations (
        project_id,
        from_entity_type,
        from_entity_id,
        relation_type,
        to_entity_type,
        to_entity_id
    )
    WHERE status IN ('proposed', 'canonical');

CREATE INDEX IF NOT EXISTS agency_entity_relations_project_lookup
    ON agency_entity_relations (project_id, created_at, relation_id);
CREATE INDEX IF NOT EXISTS agency_entity_relations_from_lookup
    ON agency_entity_relations (from_entity_type, from_entity_id, retired_at);
CREATE INDEX IF NOT EXISTS agency_entity_relations_to_lookup
    ON agency_entity_relations (to_entity_type, to_entity_id, retired_at);

CREATE OR REPLACE FUNCTION resolve_agency_entity_relation_project(
    target_entity_type TEXT,
    target_entity_id TEXT
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    resolved_project_id TEXT;
    owner_exists boolean := false;
BEGIN
    -- Returns the endpoint's Project, or NULL when the endpoint is agency-level
    -- and belongs to no Project. NULL is a valid answer, not a missing one — the
    -- caller distinguishes them, and an endpoint that does not exist raises.
    --
    -- A tranche that introduces an owner adds its arm here. That is a
    -- CREATE OR REPLACE, so it takes no table lock and touches no constraint;
    -- widening a CHECK on every tranche is what this avoids.
    CASE target_entity_type
        WHEN 'project' THEN
            SELECT project_id INTO resolved_project_id
              FROM agency_projects WHERE project_id = target_entity_id;
            owner_exists := resolved_project_id IS NOT NULL;
        WHEN 'information' THEN
            SELECT project_id INTO resolved_project_id
              FROM agency_information_cards WHERE information_id = target_entity_id;
            owner_exists := FOUND;
        WHEN 'person' THEN
            SELECT EXISTS(
                SELECT 1 FROM agency_people WHERE person_id = target_entity_id
            ) INTO owner_exists;
            resolved_project_id := NULL;   -- Contacts are agency-level.
        WHEN 'organization' THEN
            SELECT EXISTS(
                SELECT 1 FROM agency_organizations WHERE organization_id = target_entity_id
            ) INTO owner_exists;
            resolved_project_id := NULL;   -- Contacts are agency-level.
        WHEN 'decision' THEN
            IF to_regclass('agency_decision_records') IS NULL THEN
                RAISE EXCEPTION 'Entity relation endpoint owner is not implemented: decision';
            END IF;
            -- A Decision carries its Project through the Request it answers, and a
            -- global Decision has none. So existence and Project are two separate
            -- questions here: collapsing them would report every global Decision as
            -- an unknown endpoint.
            EXECUTE 'SELECT EXISTS (SELECT 1 FROM agency_decision_records WHERE decision_id = $1)'
                INTO owner_exists USING target_entity_id;
            EXECUTE 'SELECT r.project_id FROM agency_decision_records d '
                    'JOIN agency_decision_requests r ON r.request_id = d.request_id '
                    'WHERE d.decision_id = $1'
                INTO resolved_project_id USING target_entity_id;
        WHEN 'apu_object' THEN
            IF to_regclass('agency_apu_objects') IS NULL THEN
                RAISE EXCEPTION 'Entity relation endpoint owner is not implemented: apu_object';
            END IF;
            EXECUTE 'SELECT project_id FROM agency_apu_objects WHERE object_id = $1'
                INTO resolved_project_id USING target_entity_id;
            owner_exists := resolved_project_id IS NOT NULL;
        ELSE
            RAISE EXCEPTION 'unsupported EntityRef type: %', target_entity_type;
    END CASE;

    IF NOT owner_exists THEN
        RAISE EXCEPTION 'unknown % EntityRef: %', target_entity_type, target_entity_id;
    END IF;
    RETURN resolved_project_id;
END;
$$;

CREATE OR REPLACE FUNCTION enforce_agency_entity_relation_scope()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    from_project_id TEXT;
    to_project_id TEXT;
BEGIN
    from_project_id := resolve_agency_entity_relation_project(
        NEW.from_entity_type, NEW.from_entity_id
    );
    to_project_id := resolve_agency_entity_relation_project(
        NEW.to_entity_type, NEW.to_entity_id
    );

    -- An agency-level endpoint (a Contact) resolves to NULL and constrains no
    -- Project. Every endpoint that does have one must agree, and at least one
    -- endpoint must be project-scoped, because the relation itself is.
    IF from_project_id IS NULL AND to_project_id IS NULL THEN
        RAISE EXCEPTION 'Entity relation needs at least one project-scoped endpoint';
    END IF;
    IF from_project_id IS NOT NULL AND to_project_id IS NOT NULL
       AND from_project_id <> to_project_id THEN
        RAISE EXCEPTION 'Entity relation endpoints belong to different Projects';
    END IF;
    IF NEW.project_id <> COALESCE(from_project_id, to_project_id) THEN
        RAISE EXCEPTION 'Entity relation project does not match endpoint Project';
    END IF;

    IF TG_OP = 'INSERT' THEN
        -- Nothing arrives canonical. A human canonizes in a separate, audited act.
        IF NEW.status <> 'proposed' THEN
            RAISE EXCEPTION 'Entity relation is created as a proposal, not as %', NEW.status;
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF OLD.relation_id <> NEW.relation_id
           OR OLD.project_id <> NEW.project_id
           OR OLD.from_entity_type <> NEW.from_entity_type
           OR OLD.from_entity_id <> NEW.from_entity_id
           OR OLD.to_entity_type <> NEW.to_entity_type
           OR OLD.to_entity_id <> NEW.to_entity_id
           OR OLD.relation_type <> NEW.relation_type
           OR OLD.rationale IS DISTINCT FROM NEW.rationale
           OR OLD.source_refs IS DISTINCT FROM NEW.source_refs
           OR OLD.created_by <> NEW.created_by
           OR OLD.created_at <> NEW.created_at THEN
            RAISE EXCEPTION 'Entity relation identity and meaning are immutable';
        END IF;
        IF NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'Entity relation update must advance the revision by one';
        END IF;
        -- proposed -> canonical -> retired, or proposed -> rejected. Nothing else,
        -- and nothing out of a closed state.
        IF NOT (
            (OLD.status = 'proposed'  AND NEW.status IN ('canonical', 'rejected'))
            OR (OLD.status = 'canonical' AND NEW.status = 'retired')
        ) THEN
            RAISE EXCEPTION 'unsupported Entity relation transition: % -> %',
                OLD.status, NEW.status;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relations_scope_guard'
           AND tgrelid = 'agency_entity_relations'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relations_scope_guard
        BEFORE INSERT OR UPDATE ON agency_entity_relations
        FOR EACH ROW EXECUTE FUNCTION enforce_agency_entity_relation_scope();
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION reject_agency_entity_relation_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Entity relations are retained; retire instead of deleting';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relations_no_delete'
           AND tgrelid = 'agency_entity_relations'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relations_no_delete
        BEFORE DELETE ON agency_entity_relations
        FOR EACH ROW EXECUTE FUNCTION reject_agency_entity_relation_delete();
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS agency_entity_relation_events (
    event_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL REFERENCES agency_entity_relations(relation_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'relation_proposed', 'relation_canonized', 'relation_rejected',
        'relation_created', 'relation_retired'
    )),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'hermes')),
    -- The gate, in the schema rather than only in the caller: Hermes reaches this
    -- log through a proposal and through nothing else. Canonizing, rejecting and
    -- retiring stay human acts.
    CHECK (actor_kind = 'human' OR event_type = 'relation_proposed'),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_snapshot JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS agency_entity_relation_events_relation_lookup
    ON agency_entity_relation_events (relation_id, occurred_at, event_id);

CREATE OR REPLACE FUNCTION reject_agency_entity_relation_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Entity relation events are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relation_events_no_update'
           AND tgrelid = 'agency_entity_relation_events'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relation_events_no_update
        BEFORE UPDATE ON agency_entity_relation_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_entity_relation_event_mutation();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_entity_relation_events_no_delete'
           AND tgrelid = 'agency_entity_relation_events'::regclass
    ) THEN
        CREATE TRIGGER agency_entity_relation_events_no_delete
        BEFORE DELETE ON agency_entity_relation_events
        FOR EACH ROW EXECUTE FUNCTION reject_agency_entity_relation_event_mutation();
    END IF;
END;
$$;

-- The endpoint vocabulary opens to every project-scoped type the plan names, so a
-- later tranche adds a resolver arm instead of migrating this constraint again.
DO $$
DECLARE
    widened CONSTANT TEXT :=
        $vocab$IN ('project', 'information', 'decision', 'person', 'organization', 'apu_object')$vocab$;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_entity_relations'::regclass
           AND pg_get_constraintdef(oid) LIKE '%apu_object%'
           AND pg_get_constraintdef(oid) LIKE '%from_entity_type%'
    ) THEN
        ALTER TABLE agency_entity_relations
            DROP CONSTRAINT IF EXISTS agency_entity_relations_from_entity_type_check;
        EXECUTE 'ALTER TABLE agency_entity_relations
            ADD CONSTRAINT agency_entity_relations_from_entity_type_check
            CHECK (from_entity_type ' || widened || ') NOT VALID';
        ALTER TABLE agency_entity_relations
            DROP CONSTRAINT IF EXISTS agency_entity_relations_to_entity_type_check;
        EXECUTE 'ALTER TABLE agency_entity_relations
            ADD CONSTRAINT agency_entity_relations_to_entity_type_check
            CHECK (to_entity_type ' || widened || ') NOT VALID';
    END IF;
END;
$$;

-- revision stops being a two-valued flag: proposed -> canonical -> retired is
-- three states, and the old CHECK (revision IN (1, 2)) refuses the third.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_entity_relations'::regclass
           AND pg_get_constraintdef(oid) LIKE '%revision = ANY%'
    ) THEN
        ALTER TABLE agency_entity_relations
            DROP CONSTRAINT IF EXISTS agency_entity_relations_revision_check;
        ALTER TABLE agency_entity_relations
            ADD CONSTRAINT agency_entity_relations_revision_check
            CHECK (revision >= 1) NOT VALID;
    END IF;
END;
$$;

-- The open/closed invariant is now driven by status rather than by revision.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_entity_relations'::regclass
           AND conname = 'agency_entity_relations_open_or_closed_check'
    ) THEN
        ALTER TABLE agency_entity_relations
            DROP CONSTRAINT IF EXISTS agency_entity_relations_check1;
        ALTER TABLE agency_entity_relations
            ADD CONSTRAINT agency_entity_relations_open_or_closed_check
            CHECK (
                (status IN ('proposed', 'canonical') AND retired_at IS NULL AND retired_by IS NULL)
                OR (status IN ('rejected', 'retired') AND retired_at IS NOT NULL AND retired_by IS NOT NULL)
            ) NOT VALID;
    END IF;
END;
$$;

-- Uniqueness must cover proposals: two agents must not be able to propose the
-- same edge, and a proposal must not duplicate a canonical one.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
         WHERE indexname = 'agency_entity_relations_active_edge_unique'
           AND indexdef LIKE '%status%'
    ) THEN
        DROP INDEX IF EXISTS agency_entity_relations_active_edge_unique;
        CREATE UNIQUE INDEX agency_entity_relations_active_edge_unique
            ON agency_entity_relations (
                project_id, from_entity_type, from_entity_id,
                relation_type, to_entity_type, to_entity_id
            )
            WHERE status IN ('proposed', 'canonical');
    END IF;
END;
$$;

-- The review vocabulary, and the gate that admits Hermes to a proposal and to
-- nothing else. `relation_created` is retained: it names what older rows record.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_entity_relation_events'::regclass
           AND pg_get_constraintdef(oid) LIKE '%relation_proposed%'
    ) THEN
        ALTER TABLE agency_entity_relation_events
            DROP CONSTRAINT IF EXISTS agency_entity_relation_events_event_type_check;
        ALTER TABLE agency_entity_relation_events
            ADD CONSTRAINT agency_entity_relation_events_event_type_check
            CHECK (event_type IN (
                'relation_proposed', 'relation_canonized', 'relation_rejected',
                'relation_created', 'relation_retired'
            )) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'agency_entity_relation_events'::regclass
           AND conname = 'agency_entity_relation_events_hermes_proposes_only'
    ) THEN
        ALTER TABLE agency_entity_relation_events
            DROP CONSTRAINT IF EXISTS agency_entity_relation_events_actor_kind_check;
        ALTER TABLE agency_entity_relation_events
            ADD CONSTRAINT agency_entity_relation_events_actor_kind_check
            CHECK (actor_kind IN ('human', 'hermes')) NOT VALID;
        ALTER TABLE agency_entity_relation_events
            ADD CONSTRAINT agency_entity_relation_events_hermes_proposes_only
            CHECK (actor_kind = 'human' OR event_type = 'relation_proposed') NOT VALID;
    END IF;
END;
$$;
