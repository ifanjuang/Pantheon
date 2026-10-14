-- B4 operational extension of the existing B1 direct human access seam.
--
-- project.access.manage is a technical project-scoped administration capability.
-- It does not encode professional role, approval, Decision, Evidence or IdP
-- invitation authority. Remote B4 routes deliberately cannot delegate this
-- action; it remains a locally provisioned bootstrap capability.

DO $$
DECLARE
    constraint_row RECORD;
BEGIN
    -- Replace only the current closed access constraints. PostgreSQL-generated
    -- names from older migrations are matched by definition to keep replay safe.
    FOR constraint_row IN
        SELECT conname, pg_get_constraintdef(oid) AS definition
          FROM pg_constraint
         WHERE conrelid = 'human_resource_grants'::regclass
           AND contype = 'c'
    LOOP
        IF constraint_row.definition LIKE '%document.comment%'
           AND constraint_row.definition NOT LIKE '%project.access.manage%' THEN
            EXECUTE format(
                'ALTER TABLE human_resource_grants DROP CONSTRAINT %I',
                constraint_row.conname
            );
        END IF;
    END LOOP;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'human_resource_grants_action_allowed_check'
           AND conrelid = 'human_resource_grants'::regclass
    ) THEN
        ALTER TABLE human_resource_grants
            ADD CONSTRAINT human_resource_grants_action_allowed_check
            CHECK (action IN (
                'project.read',
                'project.access.manage',
                'document.read',
                'document.revision.submit',
                'document.comment'
            ));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'human_resource_grants_target_action_check'
           AND conrelid = 'human_resource_grants'::regclass
    ) THEN
        ALTER TABLE human_resource_grants
            ADD CONSTRAINT human_resource_grants_target_action_check
            CHECK (
                (resource_type = 'project'
                 AND resource_id = project_id
                 AND action IN ('project.read', 'project.access.manage'))
                OR
                (resource_type = 'project_document'
                 AND action IN (
                     'document.read',
                     'document.revision.submit',
                     'document.comment'
                 ))
            );
    END IF;
END;
$$;

COMMENT ON CONSTRAINT human_resource_grants_action_allowed_check
    ON human_resource_grants IS
    'Closed technical action vocabulary. project.access.manage administers bounded project collaboration access only and confers no professional authority.';
