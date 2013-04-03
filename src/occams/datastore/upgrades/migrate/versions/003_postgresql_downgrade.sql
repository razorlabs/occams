-- Reverts attribute ENUM to a state without the "blob" type
-- Modification of ENUMs is not very well supported in PostgreSQL so we have
-- to do a bit of hacking to get this to work properly.
BEGIN;

-- Backup the old type
ALTER TYPE "attribute_type" RENAME TO "attribute_type_old";

-- Declare the new ENUM
CREATE TYPE "attribute_type" AS ENUM ( 'boolean', 'date', 'datetime', 'decimal', 'integer', 'object', 'string', 'text');

-- Drop references to the ENUM
ALTER TABLE "attribute" DROP CONSTRAINT "ck_attribute_valid_object_bind";

-- Replace the type (also in the audit table)
ALTER TABLE "attribute" ALTER COLUMN "type" TYPE "attribute_type" USING "type"::text::"attribute_type";
ALTER TABLE "attribute_audit" ALTER COLUMN "type" TYPE "attribute_type" USING "type"::text::"attribute_type";

-- Re-add references to the ENUM
ALTER TABLE "attribute" ADD CONSTRAINT "ck_attribute_valid_object_bind" CHECK (
    CASE
    WHEN type = 'object'::attribute_type THEN object_schema_id IS NOT NULL
    ELSE object_schema_id IS NULL
    END);

-- Delete the old type
DROP TYPE "attribute_type_old";

COMMIT;

