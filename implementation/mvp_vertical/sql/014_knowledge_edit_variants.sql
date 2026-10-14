-- Immutable A/B proposal variants projected from canonical Execution Results.
-- Projection, selection and application remain separate effects.

-- This file runs on every service start, so schema evolution is guarded on the
-- catalog rather than issued unconditionally. An unguarded ALTER TABLE takes an
-- ACCESS EXCLUSIVE lock even when it has nothing to change, and a plain
-- ADD CONSTRAINT ... CHECK re-scans the whole table each time. Guarded, a
-- started-up installation performs catalog reads only.

-- Existing installations created the result-kind constraint before the
-- knowledge_edit_variant contract existed. Rebuild only that enum constraint,
-- and only while it is still missing the new kind.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'execution_result_items_result_kind_check'
           AND conrelid = 'execution_result_items'::regclass
           AND pg_get_constraintdef(oid) LIKE '%knowledge_edit_variant%'
    ) THEN
        ALTER TABLE execution_result_items
            DROP CONSTRAINT IF EXISTS execution_result_items_result_kind_check;
        ALTER TABLE execution_result_items
            ADD CONSTRAINT execution_result_items_result_kind_check CHECK (result_kind IN (
                'fragment_qualification', 'document_alignment', 'spatial_observation',
                'apu_object_mapping', 'relation_candidate', 'contradiction_candidate',
                'work_issue_candidate', 'knowledge_edit_variant'
            ));
    END IF;
END;
$$;

DO $$
DECLARE
    missing TEXT;
BEGIN
    FOREACH missing IN ARRAY ARRAY[
        'selected_text_snapshot', 'requested_variant_count', 'request_scope_digest',
        'selected_variant_id', 'selected_by'
    ] LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_name = 'knowledge_edit_requests'
               AND column_name = missing
        ) THEN
            CASE missing
                WHEN 'requested_variant_count' THEN
                    ALTER TABLE knowledge_edit_requests
                        ADD COLUMN requested_variant_count INT NOT NULL DEFAULT 1;
                WHEN 'selected_text_snapshot' THEN
                    ALTER TABLE knowledge_edit_requests ADD COLUMN selected_text_snapshot TEXT;
                WHEN 'request_scope_digest' THEN
                    ALTER TABLE knowledge_edit_requests ADD COLUMN request_scope_digest TEXT;
                WHEN 'selected_variant_id' THEN
                    ALTER TABLE knowledge_edit_requests ADD COLUMN selected_variant_id TEXT;
                WHEN 'selected_by' THEN
                    ALTER TABLE knowledge_edit_requests ADD COLUMN selected_by TEXT;
            END CASE;
        END IF;
    END LOOP;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'knowledge_edit_requests_variant_count_check'
           AND conrelid = 'knowledge_edit_requests'::regclass
    ) THEN
        ALTER TABLE knowledge_edit_requests
            ADD CONSTRAINT knowledge_edit_requests_variant_count_check
            CHECK (requested_variant_count IN (1, 2)) NOT VALID;
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS knowledge_edit_variants (
    variant_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES knowledge_edit_requests(request_id) ON DELETE CASCADE,
    variant_label TEXT NOT NULL CHECK (variant_label IN ('A', 'B')),
    replacement_markdown TEXT NOT NULL CHECK (length(replacement_markdown) > 0),
    replacement_digest TEXT NOT NULL,
    rationale TEXT,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_execution_result_id TEXT NOT NULL REFERENCES execution_results(execution_result_id),
    source_result_ref TEXT NOT NULL REFERENCES execution_result_items(result_id),
    source_payload_digest TEXT NOT NULL,
    proposed_by TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (request_id, variant_label),
    UNIQUE (source_execution_result_id, source_result_ref)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_edit_variants' AND column_name = 'created_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE knowledge_edit_variants
            ALTER COLUMN created_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'knowledge_edit_requests_selected_variant_fk'
           AND conrelid = 'knowledge_edit_requests'::regclass
    ) THEN
        ALTER TABLE knowledge_edit_requests
            ADD CONSTRAINT knowledge_edit_requests_selected_variant_fk
            FOREIGN KEY (selected_variant_id)
            REFERENCES knowledge_edit_variants(variant_id)
            ON DELETE SET NULL;
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS knowledge_edit_review_events (
    event_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES knowledge_edit_requests(request_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('variant_projected', 'variant_selected', 'request_rejected', 'variant_applied')
    ),
    actor TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'system')),
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_digest TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'knowledge_edit_review_events' AND column_name = 'occurred_at'
           AND column_default LIKE '%clock_timestamp%'
    ) THEN
        ALTER TABLE knowledge_edit_review_events
            ALTER COLUMN occurred_at SET DEFAULT clock_timestamp();
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION reject_knowledge_edit_variant_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'knowledge_edit_variants are immutable candidate snapshots';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS knowledge_edit_variants_immutable
    ON knowledge_edit_variants;
CREATE TRIGGER knowledge_edit_variants_immutable
BEFORE UPDATE OR DELETE ON knowledge_edit_variants
FOR EACH ROW EXECUTE FUNCTION reject_knowledge_edit_variant_mutation();

CREATE OR REPLACE FUNCTION reject_knowledge_edit_review_event_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'knowledge_edit_review_events are append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS knowledge_edit_review_events_append_only
    ON knowledge_edit_review_events;
CREATE TRIGGER knowledge_edit_review_events_append_only
BEFORE UPDATE OR DELETE ON knowledge_edit_review_events
FOR EACH ROW EXECUTE FUNCTION reject_knowledge_edit_review_event_mutation();
