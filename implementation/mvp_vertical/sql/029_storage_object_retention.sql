-- A7b: exact-byte retention registry for technical document versions.
--
-- Storage Object identity is byte-content identity. Physical locations remain
-- replaceable adapter state. This migration does not create Evidence, access
-- authority, professional currentness or provider adoption.

CREATE TABLE IF NOT EXISTS storage_objects (
    storage_object_id TEXT PRIMARY KEY,
    content_sha256 TEXT NOT NULL UNIQUE CHECK (content_sha256 ~ '^[A-Fa-f0-9]{64}$'),
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    media_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS storage_object_locations (
    location_id TEXT PRIMARY KEY,
    storage_object_id TEXT NOT NULL REFERENCES storage_objects(storage_object_id) ON DELETE RESTRICT,
    storage_provider_ref TEXT NOT NULL CHECK (btrim(storage_provider_ref) <> ''),
    locator TEXT NOT NULL CHECK (btrim(locator) <> ''),
    retention_guarantee TEXT NOT NULL CHECK (
        retention_guarantee IN ('content_addressed', 'provider_version', 'immutable_object', 'unknown')
    ),
    location_status TEXT NOT NULL CHECK (
        location_status IN ('verified', 'unverified', 'unavailable')
    ),
    verification_method TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (storage_provider_ref, locator),
    CHECK (
        (location_status = 'verified' AND verification_method = 'full_sha256' AND verified_at IS NOT NULL)
        OR location_status <> 'verified'
    )
);

CREATE TABLE IF NOT EXISTS document_version_storage_bindings (
    document_id TEXT NOT NULL,
    version INT NOT NULL CHECK (version > 0),
    storage_object_id TEXT NOT NULL REFERENCES storage_objects(storage_object_id) ON DELETE RESTRICT,
    bound_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (document_id, version),
    FOREIGN KEY (document_id, version)
        REFERENCES document_versions(document_id, version) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS storage_object_locations_object_lookup
    ON storage_object_locations (storage_object_id, location_status, created_at, location_id);

CREATE INDEX IF NOT EXISTS document_version_storage_object_lookup
    ON document_version_storage_bindings (storage_object_id, document_id, version);

CREATE OR REPLACE FUNCTION reject_storage_object_identity_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'storage_objects exact-content identity is immutable';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'storage_objects_identity_immutable'
           AND tgrelid = 'storage_objects'::regclass
    ) THEN
        CREATE TRIGGER storage_objects_identity_immutable
        BEFORE UPDATE OR DELETE ON storage_objects
        FOR EACH ROW EXECUTE FUNCTION reject_storage_object_identity_mutation();
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION reject_document_version_storage_binding_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'document_version_storage_bindings is immutable';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'document_version_storage_bindings_immutable'
           AND tgrelid = 'document_version_storage_bindings'::regclass
    ) THEN
        CREATE TRIGGER document_version_storage_bindings_immutable
        BEFORE UPDATE OR DELETE ON document_version_storage_bindings
        FOR EACH ROW EXECUTE FUNCTION reject_document_version_storage_binding_mutation();
    END IF;
END;
$$;

COMMENT ON TABLE storage_objects IS
    'Exact retained byte identities; stored and verified does not mean professionally validated or Evidence.';
COMMENT ON TABLE storage_object_locations IS
    'Replaceable physical locations for Storage Objects; provider availability does not confer adoption or authority.';
COMMENT ON TABLE document_version_storage_bindings IS
    'Immutable exact technical document-version to Storage Object binding; physical deduplication does not merge access scope.';
