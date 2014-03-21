-- Converts all legacy choices to code format
-- This is necessary in order to be able to keep legacy/future databases synchronized

ROLLBACK; BEGIN;

UPDATE choice SET "order" = 1000000000 + "order";

UPDATE choice
SET "order" = "sorted"."new_order"
FROM (
  SELECT id, row_number() OVER (
        PARTITION BY attribute_id
        ORDER BY "order"
        ) AS new_order
  FROM choice
) AS "sorted"
WHERE "sorted".id = choice.id
;

UPDATE "choice"
SET value = CASE value
                WHEN 'yes' THEN '1'
                WHEN 'true' THEN '1'
                WHEN 'no' THEN '0'
                WHEN 'false' THEN '0'
                ELSE "order"
            END
WHERE EXISTS(SELECT 1
             FROM "choice" AS "lchoice"
             WHERE "lchoice"."attribute_id" = "choice"."attribute_id"
             AND "value" !~ '^[0-9]+$')
;


ALTER TABLE choice ADD CONSTRAINT ck_value_numeric CHECK(value ~ '^[0-9]+$');

UPDATE "string"
SET "value" = "choice"."value"
FROM "choice"
WHERE "choice"."id" = "string"."choice_id"
;

INSERT INTO "string" (
    entity_id
  , attribute_id
  , choice_id
  , value
  , create_date
  , create_user_id
  , modify_date
  , modify_user_id
  , revision
)
SELECT
    entity_id
  , attribute_id
  , choice_id
  , value
  , create_date
  , create_user_id
  , modify_date
  , modify_user_id
  , revision
FROM "integer"
WHERE "choice_id" IS NOT NULL
;

DELETE FROM "integer" WHERE "choice_id" IS NOT NULL;


UPDATE "attribute"
SET "type" = 'string'
WHERE EXISTS(SELECT 1
             FROM "choice"
             WHERE "choice"."attribute_id" = "attribute"."id")
;

