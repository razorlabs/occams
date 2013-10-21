--
-- Adds ``is_pii` property to attributes
--

BEGIN;

ALTER TABLE "attribute" ADD COLUMN is_pii BOOLEAN;
ALTER TABLE "attribute_audit" ADD COLUMN is_pii BOOLEAN;

UPDATE "attribute" SET is_pii = FALSE;
UPDATE "attribute_audit" SET is_pii = FALSE;

ALTER TABLE "attribute" ALTER is_pii SET NOT NULL;
ALTER TABLE "attribute_audit" ALTER is_pii SET NOT NULL;

COMMIT;

