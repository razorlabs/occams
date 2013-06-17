-- Configures new entity states
-- Modification of ENUMs is not very well supported in PostgreSQL so we have
-- to do a bit of hacking to get this to work properly.
BEGIN;


-- Prepare the live/audit tables for the upgrade


ALTER TABLE "entity"
  ALTER COLUMN "state" DROP DEFAULT,
  ALTER COLUMN "state" DROP NOT NULL;

ALTER TABLE "entity_audit"
  ALTER COLUMN "state" DROP DEFAULT,
  ALTER COLUMN "state" DROP NOT NULL;

UPDATE "entity" SET "state" = NULL WHERE "state" = 'inline';
UPDATE "entity_audit" SET "state" = NULL WHERE "state" = 'inline';


-- Swap out enum types with the new one.


ALTER TYPE "entity_state" RENAME TO "entity_state_old";

CREATE TYPE "entity_state" AS ENUM (
  'pending-entry',
  'in-progress',
  'pending-review',
  'pending-correction',
  'complete',
  'error',
  'inaccurate');

ALTER TABLE "entity"
  ALTER COLUMN "state" TYPE "entity_state" USING "state"::text::"entity_state";

ALTER TABLE "entity_audit"
  ALTER COLUMN "state" TYPE "entity_state" USING "state"::text::"entity_state";

DROP TYPE "entity_state_old";


COMMIT;

