-- B3 append-only discussion attached to exact professional document revisions.
--
-- A comment is collaboration context only. It does not create Evidence,
-- Decision, approval, professional review, currentness or project truth.

CREATE TABLE IF NOT EXISTS doc_document_revision_comments (
    comment_id TEXT PRIMARY KEY,
    document_version_id TEXT NOT NULL
        REFERENCES doc_document_versions(version_id) ON DELETE RESTRICT,
    parent_comment_id TEXT,
    body TEXT NOT NULL CHECK (
        btrim(body) <> '' AND length(body) <= 20000
    ),
    anchor_ref TEXT CHECK (
        anchor_ref IS NULL
        OR (btrim(anchor_ref) <> '' AND length(anchor_ref) <= 2000)
    ),
    created_by TEXT NOT NULL
        REFERENCES human_principals(principal_ref) ON DELETE RESTRICT,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL CHECK (btrim(payload_digest) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (comment_id, document_version_id),
    CHECK (parent_comment_id IS NULL OR parent_comment_id <> comment_id),
    FOREIGN KEY (parent_comment_id, document_version_id)
        REFERENCES doc_document_revision_comments(comment_id, document_version_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS doc_document_revision_comments_version_lookup
    ON doc_document_revision_comments (
        document_version_id, created_at, comment_id
    );

CREATE OR REPLACE FUNCTION reject_doc_document_revision_comment_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'document revision comments are append-only';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'doc_document_revision_comments_append_only'
           AND tgrelid = 'doc_document_revision_comments'::regclass
    ) THEN
        CREATE TRIGGER doc_document_revision_comments_append_only
        BEFORE UPDATE OR DELETE ON doc_document_revision_comments
        FOR EACH ROW EXECUTE FUNCTION reject_doc_document_revision_comment_mutation();
    END IF;
END;
$$;

COMMENT ON TABLE doc_document_revision_comments IS
    'Append-only human discussion on exact Project Document revisions; comments are not review decisions, Evidence, approvals or professional currentness.';
