-- Bind authorized APU write commands to their canonical owner events.
--
-- The owning tables are created at their final shape by 012 and 021. This file
-- only installs the cross-owner foreign keys once both sides exist.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'agency_apu_events_command_ref_fkey'
           AND conrelid = 'agency_apu_events'::regclass
    ) THEN
        ALTER TABLE agency_apu_events
            ADD CONSTRAINT agency_apu_events_command_ref_fkey
            FOREIGN KEY (command_ref)
            REFERENCES apu_write_command_candidates(command_id)
            ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'agency_apu_events_authorization_ref_fkey'
           AND conrelid = 'agency_apu_events'::regclass
    ) THEN
        ALTER TABLE agency_apu_events
            ADD CONSTRAINT agency_apu_events_authorization_ref_fkey
            FOREIGN KEY (authorization_ref)
            REFERENCES apu_write_authorization_events(authorization_id)
            ON DELETE RESTRICT;
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS agency_apu_source_match_command_once
    ON agency_apu_events (command_ref)
    WHERE event_type = 'source_match_applied' AND command_ref IS NOT NULL;

CREATE INDEX IF NOT EXISTS agency_apu_source_match_authorization_lookup
    ON agency_apu_events (authorization_ref)
    WHERE event_type = 'source_match_applied' AND authorization_ref IS NOT NULL;
