-- Preserve retrieval projections for every immutable source digest.
--
-- Fresh databases are created directly in the target shape by store.DDL and
-- 008_structured_extraction.sql. This guarded block exists only to evolve a
-- database created before digest was part of the retrieval identity. The outer
-- guard keeps normal startup to a catalog read; the advisory lock + inner guard
-- serializes the one-time destructive upgrade when several workers start at once.
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'chunks_retrieval_identity_key'
           AND conrelid = 'chunks'::regclass
    ) THEN
        PERFORM pg_advisory_xact_lock(
            hashtextextended('pantheon.versioned_retrieval_chunks.v1', 0)
        );

        -- Another startup transaction may have completed the migration while
        -- this transaction waited for the advisory lock.
        IF NOT EXISTS (
            SELECT 1
              FROM pg_constraint
             WHERE conname = 'chunks_retrieval_identity_key'
               AND conrelid = 'chunks'::regclass
        ) THEN
            ALTER TABLE retrieval_chunk_projections
                ADD COLUMN IF NOT EXISTS source_digest TEXT;
            ALTER TABLE retrieval_chunk_units
                ADD COLUMN IF NOT EXISTS source_digest TEXT;

            UPDATE retrieval_chunk_projections p
               SET source_digest = c.source_digest
              FROM chunks c
             WHERE p.dossier = c.dossier
               AND p.source_ref = c.source_ref
               AND p.chunk_no = c.chunk_no
               AND p.source_digest IS NULL;

            UPDATE retrieval_chunk_units u
               SET source_digest = c.source_digest
              FROM chunks c
             WHERE u.dossier = c.dossier
               AND u.source_ref = c.source_ref
               AND u.chunk_no = c.chunk_no
               AND u.source_digest IS NULL;

            IF EXISTS (
                SELECT 1 FROM retrieval_chunk_projections WHERE source_digest IS NULL
            ) OR EXISTS (
                SELECT 1 FROM retrieval_chunk_units WHERE source_digest IS NULL
            ) THEN
                RAISE EXCEPTION 'cannot version retrieval chunks: historical digest backfill incomplete';
            END IF;

            -- Drop only the old identity constraints. Discover names from the
            -- catalog because PostgreSQL truncates long auto-generated FK names.
            FOR constraint_name IN
                SELECT conname
                  FROM pg_constraint
                 WHERE conrelid = 'retrieval_chunk_units'::regclass
                   AND (
                        contype = 'p'
                        OR (contype = 'f' AND confrelid = 'retrieval_chunk_projections'::regclass)
                   )
            LOOP
                EXECUTE format(
                    'ALTER TABLE retrieval_chunk_units DROP CONSTRAINT %I',
                    constraint_name
                );
            END LOOP;

            FOR constraint_name IN
                SELECT conname
                  FROM pg_constraint
                 WHERE conrelid = 'retrieval_chunk_projections'::regclass
                   AND (
                        contype = 'p'
                        OR (contype = 'f' AND confrelid = 'chunks'::regclass)
                   )
            LOOP
                EXECUTE format(
                    'ALTER TABLE retrieval_chunk_projections DROP CONSTRAINT %I',
                    constraint_name
                );
            END LOOP;

            FOR constraint_name IN
                SELECT conname
                  FROM pg_constraint
                 WHERE conrelid = 'chunks'::regclass
                   AND contype = 'u'
                   AND pg_get_constraintdef(oid) NOT LIKE '%source_digest%'
            LOOP
                EXECUTE format('ALTER TABLE chunks DROP CONSTRAINT %I', constraint_name);
            END LOOP;

            ALTER TABLE retrieval_chunk_projections
                ALTER COLUMN source_digest SET NOT NULL;
            ALTER TABLE retrieval_chunk_units
                ALTER COLUMN source_digest SET NOT NULL;

            ALTER TABLE chunks
                ADD CONSTRAINT chunks_retrieval_identity_key
                UNIQUE (dossier, source_ref, source_digest, chunk_no);
            ALTER TABLE retrieval_chunk_projections
                ADD PRIMARY KEY (dossier, source_ref, source_digest, chunk_no),
                ADD CONSTRAINT retrieval_chunk_projections_chunk_fkey
                    FOREIGN KEY (dossier, source_ref, source_digest, chunk_no)
                    REFERENCES chunks(dossier, source_ref, source_digest, chunk_no)
                    ON DELETE CASCADE;
            ALTER TABLE retrieval_chunk_units
                ADD PRIMARY KEY (dossier, source_ref, source_digest, chunk_no, unit_id),
                ADD CONSTRAINT retrieval_chunk_units_chunk_fkey
                    FOREIGN KEY (dossier, source_ref, source_digest, chunk_no)
                    REFERENCES retrieval_chunk_projections(
                        dossier, source_ref, source_digest, chunk_no
                    ) ON DELETE CASCADE;
        END IF;
    END IF;
END;
$$;
