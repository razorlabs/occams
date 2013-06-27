--
-- Modifies schema to use choice type where necessary
--
BEGIN;

-- move value to name
-- not will not break checksum since it uses value anyway,
-- which will be configured in the algorithm


UPDATE "choice" SET "name" = "value";
UPDATE "choice_audit" SET "name" = "value";


-- drop the cold column


ALTER TABLE "choice" DROP COLUMN "value";
ALTER TABLE "choice_audit" DROP COLUMN "value";


-- update choice codes for booleans

UPDATE "choice" SET
  "name" = CASE "name" WHEN 'False' THEN '0' WHEN 'True' THEN '1' END
WHERE EXISTS(
  SELECT 1
  FROM "attribute"
  WHERE "attribute"."id" = "choice"."attribute_id"
  AND "attribute"."type" = 'boolean')
;

-- update all string codes to use the order number
-- note that there are some numeric strings that we need to watch out for
-- (e.g. 00332, in this case leave those alone)
UPDATE "choice" SET
  "name" = CAST("order" AS VARCHAR)
WHERE EXISTS(
  SELECT 1
  FROM "attribute"
  WHERE "attribute"."id" = "choice"."attribute_id"
  AND "attribute"."type" = 'string')
AND EXISTS(
  SELECT 1
  FROM "choice" as "group"
  WHERE "group"."attribute_id" = "choice"."attribute_id"
  AND "name" ~ '[^0-9]')
;


UPDATE "attribute" SET
  -- map numeric string to auto_choice=False
  "type" =
    CASE
      WHEN EXISTS(SELECT 1 FROM "choice" WHERE "choice"."attribute_id" = "attribute"."id") THEN 'choice'
      ELSE "type"
      END
;

COMMIT;

