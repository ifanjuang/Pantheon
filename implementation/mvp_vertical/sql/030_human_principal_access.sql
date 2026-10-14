-- Provider-neutral human principal binding and direct scoped resource access.
--
-- This is an implementation seam for authenticated agency/external humans.
-- It is not a Pantheon IAM/RBAC engine, professional role model, approval model,
-- project participation model or source of business authority.

CREATE TABLE IF NOT EXISTS human_principals (
    principal_ref TEXT PRIMARY KEY CHECK (btrim(principal_ref) <> ''),
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    disabled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS human_oidc_bindings (
    binding_id TEXT PRIMARY KEY,
    principal_ref TEXT NOT NULL REFERENCES human_principals(principal_ref) ON DELETE RESTRICT,
    issuer TEXT NOT NULL CHECK (btrim(issuer) <> ''),
    subject TEXT NOT NULL CHECK (btrim(subject) <> ''),
    bound_by TEXT NOT NULL CHECK (btrim(bound_by) <> ''),
    reason TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    valid_until TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (valid_until IS NULL OR valid_until > valid_from)
);

CREATE UNIQUE INDEX IF NOT EXISTS human_oidc_one_active_external_identity
    ON human_oidc_bindings (issuer, subject)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS human_oidc_binding_principal_lookup
    ON human_oidc_bindings (principal_ref, revoked_at, valid_from, valid_until);

CREATE TABLE IF NOT EXISTS human_resource_grants (
    grant_id TEXT PRIMARY KEY,
    principal_ref TEXT NOT NULL REFERENCES human_principals(principal_ref) ON DELETE RESTRICT,
    project_id TEXT NOT NULL REFERENCES agency_projects(project_id) ON DELETE RESTRICT,
    resource_type TEXT NOT NULL CHECK (resource_type IN ('project', 'project_document')),
    resource_id TEXT NOT NULL CHECK (btrim(resource_id) <> ''),
    action TEXT NOT NULL CHECK (action IN (
        'project.read',
        'document.read',
        'document.revision.submit'
    )),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    valid_until TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    granted_by TEXT NOT NULL CHECK (btrim(granted_by) <> ''),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (valid_until IS NULL OR valid_until > valid_from),
    CHECK (
        (resource_type = 'project' AND resource_id = project_id AND action = 'project.read')
        OR
        (resource_type = 'project_document' AND action IN ('document.read', 'document.revision.submit'))
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS human_resource_one_active_direct_grant
    ON human_resource_grants (principal_ref, project_id, resource_type, resource_id, action)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS human_resource_grant_lookup
    ON human_resource_grants (
        principal_ref, project_id, resource_type, resource_id, action,
        revoked_at, valid_from, valid_until
    );

-- The uniqueness indexes deliberately treat an unrevoked row as occupying its
-- identity even after valid_until. Before a new explicit binding/grant is
-- inserted, close only an already-expired predecessor. This preserves the old
-- row and never extends access implicitly.
CREATE OR REPLACE FUNCTION retire_expired_human_oidc_binding_before_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE human_oidc_bindings
       SET revoked_at = clock_timestamp()
     WHERE issuer = NEW.issuer
       AND subject = NEW.subject
       AND revoked_at IS NULL
       AND valid_until IS NOT NULL
       AND valid_until <= CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION retire_expired_human_resource_grant_before_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE human_resource_grants
       SET revoked_at = clock_timestamp()
     WHERE principal_ref = NEW.principal_ref
       AND project_id = NEW.project_id
       AND resource_type = NEW.resource_type
       AND resource_id = NEW.resource_id
       AND action = NEW.action
       AND revoked_at IS NULL
       AND valid_until IS NOT NULL
       AND valid_until <= CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION protect_human_principal_rows()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'human principal records are retained for historical attribution';
    END IF;
    IF NEW.principal_ref <> OLD.principal_ref
       OR NEW.created_by <> OLD.created_by
       OR NEW.created_at <> OLD.created_at THEN
        RAISE EXCEPTION 'human principal identity is immutable';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION protect_human_oidc_binding_rows()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'human OIDC bindings are retained for provenance';
    END IF;
    IF NEW.binding_id <> OLD.binding_id
       OR NEW.principal_ref <> OLD.principal_ref
       OR NEW.issuer <> OLD.issuer
       OR NEW.subject <> OLD.subject
       OR NEW.bound_by <> OLD.bound_by
       OR NEW.reason IS DISTINCT FROM OLD.reason
       OR NEW.valid_from <> OLD.valid_from
       OR NEW.valid_until IS DISTINCT FROM OLD.valid_until
       OR NEW.created_at <> OLD.created_at THEN
        RAISE EXCEPTION 'human OIDC binding identity/provenance is immutable; only revocation may change';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION protect_human_resource_grant_rows()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'human resource grants are retained for provenance';
    END IF;
    IF NEW.grant_id <> OLD.grant_id
       OR NEW.principal_ref <> OLD.principal_ref
       OR NEW.project_id <> OLD.project_id
       OR NEW.resource_type <> OLD.resource_type
       OR NEW.resource_id <> OLD.resource_id
       OR NEW.action <> OLD.action
       OR NEW.valid_from <> OLD.valid_from
       OR NEW.valid_until IS DISTINCT FROM OLD.valid_until
       OR NEW.granted_by <> OLD.granted_by
       OR NEW.reason IS DISTINCT FROM OLD.reason
       OR NEW.created_at <> OLD.created_at THEN
        RAISE EXCEPTION 'human resource grant identity/provenance is immutable; only revocation may change';
    END IF;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'human_principals_protect_history'
           AND tgrelid = 'human_principals'::regclass
    ) THEN
        CREATE TRIGGER human_principals_protect_history
        BEFORE UPDATE OR DELETE ON human_principals
        FOR EACH ROW EXECUTE FUNCTION protect_human_principal_rows();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'human_oidc_bindings_protect_history'
           AND tgrelid = 'human_oidc_bindings'::regclass
    ) THEN
        CREATE TRIGGER human_oidc_bindings_protect_history
        BEFORE UPDATE OR DELETE ON human_oidc_bindings
        FOR EACH ROW EXECUTE FUNCTION protect_human_oidc_binding_rows();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'human_resource_grants_protect_history'
           AND tgrelid = 'human_resource_grants'::regclass
    ) THEN
        CREATE TRIGGER human_resource_grants_protect_history
        BEFORE UPDATE OR DELETE ON human_resource_grants
        FOR EACH ROW EXECUTE FUNCTION protect_human_resource_grant_rows();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'human_oidc_bindings_retire_expired'
           AND tgrelid = 'human_oidc_bindings'::regclass
    ) THEN
        CREATE TRIGGER human_oidc_bindings_retire_expired
        BEFORE INSERT ON human_oidc_bindings
        FOR EACH ROW EXECUTE FUNCTION retire_expired_human_oidc_binding_before_insert();
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'human_resource_grants_retire_expired'
           AND tgrelid = 'human_resource_grants'::regclass
    ) THEN
        CREATE TRIGGER human_resource_grants_retire_expired
        BEFORE INSERT ON human_resource_grants
        FOR EACH ROW EXECUTE FUNCTION retire_expired_human_resource_grant_before_insert();
    END IF;
END;
$$;

COMMENT ON TABLE human_principals IS
    'Stable local technical human principal identities; not professional roles, project participants or decision authorities.';
COMMENT ON TABLE human_oidc_bindings IS
    'Replaceable external OIDC issuer+subject bindings to stable local principals; account binding does not grant project access.';
COMMENT ON TABLE human_resource_grants IS
    'Direct technical access grants for exact principal/project/resource/action; access does not confer approval or professional authority.';
