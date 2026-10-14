-- Hierarchical Agency Data classification.
--
-- Category is a logical classification/navigation record. CategoryAssignment is
-- an explicit N:N membership link. Neither table is a semantic EntityRelation,
-- Project ownership, lifecycle status, authorization, Evidence, or a source
-- storage hierarchy.

CREATE TABLE IF NOT EXISTS agency_categories (
    category_id TEXT PRIMARY KEY CHECK (btrim(category_id) <> ''),
    title TEXT NOT NULL CHECK (btrim(title) <> ''),
    description TEXT NOT NULL DEFAULT '',
    parent_category_id TEXT REFERENCES agency_categories(category_id) ON DELETE RESTRICT,
    applies_to JSONB NOT NULL CHECK (
        jsonb_typeof(applies_to) = 'array'
        AND jsonb_array_length(applies_to) > 0
        AND applies_to <@ '["project", "information", "document", "knowledge", "work_issue"]'::jsonb
    ),
    sort_order INTEGER NOT NULL DEFAULT 0 CHECK (sort_order >= 0),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    updated_by TEXT NOT NULL CHECK (btrim(updated_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    archived_at TIMESTAMPTZ,
    CHECK (parent_category_id IS NULL OR parent_category_id <> category_id)
);

CREATE INDEX IF NOT EXISTS agency_categories_parent_lookup
    ON agency_categories (parent_category_id, sort_order, lower(title), category_id);
CREATE INDEX IF NOT EXISTS agency_categories_active_lookup
    ON agency_categories (sort_order, lower(title), category_id)
    WHERE archived_at IS NULL;

CREATE TABLE IF NOT EXISTS agency_category_assignments (
    assignment_id TEXT PRIMARY KEY CHECK (btrim(assignment_id) <> ''),
    category_id TEXT NOT NULL REFERENCES agency_categories(category_id) ON DELETE RESTRICT,
    entity_type TEXT NOT NULL CHECK (
        entity_type IN ('project', 'information', 'document', 'knowledge', 'work_issue')
    ),
    entity_id TEXT NOT NULL CHECK (btrim(entity_id) <> ''),
    assigned_by TEXT NOT NULL CHECK (btrim(assigned_by) <> ''),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    rationale TEXT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    retired_at TIMESTAMPTZ,
    retired_by TEXT,
    CHECK (
        (retired_at IS NULL AND retired_by IS NULL)
        OR (retired_at IS NOT NULL AND retired_by IS NOT NULL AND btrim(retired_by) <> '')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS agency_category_assignments_active_unique
    ON agency_category_assignments (category_id, entity_type, entity_id)
    WHERE retired_at IS NULL;
CREATE INDEX IF NOT EXISTS agency_category_assignments_category_lookup
    ON agency_category_assignments (category_id, retired_at, assigned_at, assignment_id);
CREATE INDEX IF NOT EXISTS agency_category_assignments_entity_lookup
    ON agency_category_assignments (entity_type, entity_id, retired_at, assigned_at, assignment_id);

-- The row-level cycle guard alone is insufficient when two transactions move
-- different Categories under each other concurrently. Acquire one transaction
-- advisory lock before UPDATE takes any target row lock, then let the row trigger
-- validate against a hierarchy that cannot change concurrently.
CREATE OR REPLACE FUNCTION serialize_agency_category_hierarchy_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(
        hashtextextended('pantheon.agency_categories.hierarchy', 0)
    );
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION agency_category_parent_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    cycle_found boolean := false;
    parent_archived_at TIMESTAMPTZ;
BEGIN
    IF NEW.parent_category_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- A parent relation and parent archival are one hierarchy invariant. Hold a
    -- shared row lock until this mutation commits so an archive cannot validate
    -- against the pre-relation state and commit an archived active parent.
    SELECT archived_at
      INTO parent_archived_at
      FROM agency_categories
     WHERE category_id = NEW.parent_category_id
     FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'unknown parent Category: %', NEW.parent_category_id;
    END IF;
    IF parent_archived_at IS NOT NULL THEN
        RAISE EXCEPTION 'archived Category cannot be used as parent: %', NEW.parent_category_id;
    END IF;

    WITH RECURSIVE descendants(category_id) AS (
        SELECT category_id
          FROM agency_categories
         WHERE parent_category_id = NEW.category_id
        UNION ALL
        SELECT child.category_id
          FROM agency_categories child
          JOIN descendants d ON child.parent_category_id = d.category_id
    )
    SELECT EXISTS (
        SELECT 1 FROM descendants WHERE category_id = NEW.parent_category_id
    ) INTO cycle_found;

    IF cycle_found THEN
        RAISE EXCEPTION 'Category hierarchy cycle is forbidden';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION agency_category_update_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.category_id <> NEW.category_id
       OR OLD.created_by <> NEW.created_by
       OR OLD.created_at <> NEW.created_at THEN
        RAISE EXCEPTION 'Category identity and creation provenance are immutable';
    END IF;
    IF OLD.archived_at IS NOT NULL THEN
        RAISE EXCEPTION 'archived Category is immutable';
    END IF;
    IF NEW.revision <> OLD.revision + 1 THEN
        RAISE EXCEPTION 'Category update must advance revision by one';
    END IF;
    IF NEW.updated_at <= OLD.updated_at THEN
        RAISE EXCEPTION 'Category update must advance updated_at';
    END IF;

    IF NEW.applies_to IS DISTINCT FROM OLD.applies_to
       AND EXISTS (
            SELECT 1
              FROM agency_category_assignments a
             WHERE a.category_id = OLD.category_id
               AND a.retired_at IS NULL
               AND NOT (NEW.applies_to ? a.entity_type)
       ) THEN
        RAISE EXCEPTION 'Category applies_to cannot exclude an active assignment type';
    END IF;

    IF OLD.archived_at IS NULL AND NEW.archived_at IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
              FROM agency_categories child
             WHERE child.parent_category_id = OLD.category_id
               AND child.archived_at IS NULL
        ) THEN
            RAISE EXCEPTION 'Category with active child Categories cannot be archived';
        END IF;
        IF EXISTS (
            SELECT 1
              FROM agency_category_assignments a
             WHERE a.category_id = OLD.category_id
               AND a.retired_at IS NULL
        ) THEN
            RAISE EXCEPTION 'Category with active assignments cannot be archived';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

-- CategoryAssignment is polymorphic, so one FK cannot express its owner target.
-- Admission therefore locks the concrete owner row FOR KEY SHARE. This both
-- proves existence and serializes with owner DELETE until the assignment insert
-- commits or aborts.
CREATE OR REPLACE FUNCTION lock_agency_category_assignment_entity(
    candidate_type TEXT,
    candidate_id TEXT
) RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    CASE candidate_type
        WHEN 'project' THEN
            PERFORM 1 FROM agency_projects
             WHERE project_id = candidate_id FOR KEY SHARE;
        WHEN 'information' THEN
            PERFORM 1 FROM agency_information_cards
             WHERE information_id = candidate_id FOR KEY SHARE;
        WHEN 'document' THEN
            PERFORM 1 FROM doc_documents
             WHERE document_id = candidate_id FOR KEY SHARE;
        WHEN 'knowledge' THEN
            PERFORM 1 FROM knowledge_items
             WHERE knowledge_id = candidate_id FOR KEY SHARE;
        WHEN 'work_issue' THEN
            PERFORM 1 FROM work_issues
             WHERE issue_id = candidate_id FOR KEY SHARE;
        ELSE
            RETURN false;
    END CASE;
    RETURN FOUND;
END;
$$;

CREATE OR REPLACE FUNCTION validate_agency_category_assignment()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    category_applies_to JSONB;
    category_archived_at TIMESTAMPTZ;
BEGIN
    -- Serialize assignment admission with Category archive/applies_to updates.
    -- Whichever mutation locks the Category first becomes visible to the other.
    SELECT applies_to, archived_at
      INTO category_applies_to, category_archived_at
      FROM agency_categories
     WHERE category_id = NEW.category_id
     FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'unknown Category: %', NEW.category_id;
    END IF;
    IF category_archived_at IS NOT NULL THEN
        RAISE EXCEPTION 'cannot assign an archived Category: %', NEW.category_id;
    END IF;
    IF NOT (category_applies_to ? NEW.entity_type) THEN
        RAISE EXCEPTION 'Category % does not apply to entity type %',
            NEW.category_id, NEW.entity_type;
    END IF;
    IF NOT lock_agency_category_assignment_entity(NEW.entity_type, NEW.entity_id) THEN
        RAISE EXCEPTION 'unknown CategoryAssignment endpoint: %:%',
            NEW.entity_type, NEW.entity_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION guard_agency_category_assignment_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'CategoryAssignment links are retained; retire instead of deleting';
    END IF;

    IF OLD.assignment_id <> NEW.assignment_id
       OR OLD.category_id <> NEW.category_id
       OR OLD.entity_type <> NEW.entity_type
       OR OLD.entity_id <> NEW.entity_id
       OR OLD.assigned_by <> NEW.assigned_by
       OR OLD.assigned_at <> NEW.assigned_at
       OR OLD.rationale IS DISTINCT FROM NEW.rationale THEN
        RAISE EXCEPTION 'CategoryAssignment identity and meaning are immutable';
    END IF;
    IF OLD.retired_at IS NOT NULL THEN
        RAISE EXCEPTION 'retired CategoryAssignment is immutable';
    END IF;
    IF NEW.revision <> OLD.revision + 1 THEN
        RAISE EXCEPTION 'CategoryAssignment retirement must advance revision by one';
    END IF;
    IF NEW.retired_at IS NULL OR NEW.retired_by IS NULL OR btrim(NEW.retired_by) = '' THEN
        RAISE EXCEPTION 'CategoryAssignment update may only retire the link';
    END IF;
    RETURN NEW;
END;
$$;

-- Polymorphic CategoryAssignment endpoints cannot use one SQL foreign key. Keep
-- the owner identity valid while an active assignment references it; callers can
-- retire the classification first, without turning CategoryAssignment into owner
-- lifecycle or authorization.
CREATE OR REPLACE FUNCTION reject_active_category_assignment_owner_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    owner_type TEXT := TG_ARGV[0];
    owner_id TEXT := to_jsonb(OLD) ->> TG_ARGV[1];
BEGIN
    IF owner_id IS NULL OR btrim(owner_id) = '' THEN
        RAISE EXCEPTION 'classified owner delete guard cannot resolve owner identity';
    END IF;
    IF EXISTS (
        SELECT 1
          FROM agency_category_assignments
         WHERE entity_type = owner_type
           AND entity_id = owner_id
           AND retired_at IS NULL
    ) THEN
        RAISE EXCEPTION
            'active CategoryAssignment must be retired before deleting %:%',
            owner_type, owner_id;
    END IF;
    RETURN OLD;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_categories_hierarchy_serialize'
           AND tgrelid = 'agency_categories'::regclass
    ) THEN
        CREATE TRIGGER agency_categories_hierarchy_serialize
        BEFORE UPDATE OF parent_category_id ON agency_categories
        FOR EACH STATEMENT EXECUTE FUNCTION serialize_agency_category_hierarchy_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_categories_parent_guard'
           AND tgrelid = 'agency_categories'::regclass
    ) THEN
        CREATE TRIGGER agency_categories_parent_guard
        BEFORE INSERT OR UPDATE OF parent_category_id ON agency_categories
        FOR EACH ROW EXECUTE FUNCTION agency_category_parent_guard();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_categories_update_guard'
           AND tgrelid = 'agency_categories'::regclass
    ) THEN
        CREATE TRIGGER agency_categories_update_guard
        BEFORE UPDATE ON agency_categories
        FOR EACH ROW EXECUTE FUNCTION agency_category_update_guard();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_category_assignment_insert_guard'
           AND tgrelid = 'agency_category_assignments'::regclass
    ) THEN
        CREATE TRIGGER agency_category_assignment_insert_guard
        BEFORE INSERT ON agency_category_assignments
        FOR EACH ROW EXECUTE FUNCTION validate_agency_category_assignment();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_category_assignments_retire_only'
           AND tgrelid = 'agency_category_assignments'::regclass
    ) THEN
        CREATE TRIGGER agency_category_assignments_retire_only
        BEFORE UPDATE ON agency_category_assignments
        FOR EACH ROW EXECUTE FUNCTION guard_agency_category_assignment_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_category_assignments_no_delete'
           AND tgrelid = 'agency_category_assignments'::regclass
    ) THEN
        CREATE TRIGGER agency_category_assignments_no_delete
        BEFORE DELETE ON agency_category_assignments
        FOR EACH ROW EXECUTE FUNCTION guard_agency_category_assignment_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_projects_category_assignment_delete_guard'
           AND tgrelid = 'agency_projects'::regclass
    ) THEN
        CREATE TRIGGER agency_projects_category_assignment_delete_guard
        BEFORE DELETE ON agency_projects
        FOR EACH ROW EXECUTE FUNCTION reject_active_category_assignment_owner_delete(
            'project', 'project_id'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'agency_information_category_assignment_delete_guard'
           AND tgrelid = 'agency_information_cards'::regclass
    ) THEN
        CREATE TRIGGER agency_information_category_assignment_delete_guard
        BEFORE DELETE ON agency_information_cards
        FOR EACH ROW EXECUTE FUNCTION reject_active_category_assignment_owner_delete(
            'information', 'information_id'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'doc_documents_category_assignment_delete_guard'
           AND tgrelid = 'doc_documents'::regclass
    ) THEN
        CREATE TRIGGER doc_documents_category_assignment_delete_guard
        BEFORE DELETE ON doc_documents
        FOR EACH ROW EXECUTE FUNCTION reject_active_category_assignment_owner_delete(
            'document', 'document_id'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'knowledge_items_category_assignment_delete_guard'
           AND tgrelid = 'knowledge_items'::regclass
    ) THEN
        CREATE TRIGGER knowledge_items_category_assignment_delete_guard
        BEFORE DELETE ON knowledge_items
        FOR EACH ROW EXECUTE FUNCTION reject_active_category_assignment_owner_delete(
            'knowledge', 'knowledge_id'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'work_issues_category_assignment_delete_guard'
           AND tgrelid = 'work_issues'::regclass
    ) THEN
        CREATE TRIGGER work_issues_category_assignment_delete_guard
        BEFORE DELETE ON work_issues
        FOR EACH ROW EXECUTE FUNCTION reject_active_category_assignment_owner_delete(
            'work_issue', 'issue_id'
        );
    END IF;
END;
$$;

COMMENT ON TABLE agency_categories IS
    'Hierarchical Agency Data classification records; Category is not a physical folder, lifecycle status, authorization or Project ownership.';
COMMENT ON TABLE agency_category_assignments IS
    'Explicit N:N Category memberships; assignment does not transfer entity ownership, establish Evidence or authorize an action.';
