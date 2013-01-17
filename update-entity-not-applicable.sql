-- Adds a new enum to the database because it is not supported in PostgreSQL 8.3
BEGIN;

-- Backup the old type
ALTER TYPE entity_state RENAME TO entity_state_old;

-- Declare the new ENUM
CREATE TYPE entity_state AS ENUM (
        'complete',
        'error',
        'inaccurate',
        'inline',
        'not-applicable',
        'not-done',
        'pending-entry',
        'pending-review');

-- Remove the old default so it doesn't interfere with the type
ALTER TABLE entity ALTER COLUMN state DROP DEFAULT;
ALTER TABLE entity_audit ALTER COLUMN state DROP DEFAULT;

-- Replace the type
ALTER TABLE entity ALTER COLUMN state TYPE entity_state USING state::text::entity_state;
ALTER TABLE entity_audit ALTER COLUMN state TYPE entity_state USING state::text::entity_state;

-- Restore the default
ALTER TABLE entity ALTER COLUMN state SET DEFAULT 'pending-entry';
ALTER TABLE entity_audit ALTER COLUMN state SET DEFAULT 'pending-entry';

-- Delete the old type
DROP TYPE entity_state_old;

COMMIT;

SELECT e.enumlabel
FROM pg_enum e
JOIN pg_type t ON e.enumtypid = t.oid
WHERE t.typname = 'entity_state';

