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


WITH
  -- Determine every single choice value's original order number
  "orders" AS (

    SELECT
        "schema"."name" AS "schema_name"
      , MIN("schema"."publish_date") AS "original_publish_date"
      , "attribute"."name" AS "attribute_name"
      , "choice"."value" AS "choice_value"
      , ( SELECT "lchoice"."order"
          FROM "choice" AS "lchoice"
          JOIN "attribute" AS "lattribute" ON "lattribute"."id" = "lchoice"."attribute_id"
          JOIN "schema" AS "lschema" ON "lschema"."id" = "lattribute"."schema_id"
          WHERE "lchoice"."value" = "choice"."value"
          AND   "lattribute"."name" = "attribute"."name"
          AND   "lschema"."name" = "schema"."name"
          ORDER BY "lschema"."publish_date" ASC NULLS LAST
          LIMIT 1) AS "original_order"
    FROM "choice"
    JOIN "attribute" ON "attribute"."id" = "choice"."attribute_id"
    JOIN "schema" ON "schema"."id" = "attribute"."schema_id"
    GROUP BY "schema"."name"
            ,"attribute"."name"
            ,"choice"."value"
  )

  -- Sort choice orders within an attribute scope based on their original
  -- publish date order number
  -- This will stack newer choice values at the end of the code list
  ,"codes" AS (
    SELECT
      "orders".*
      , row_number() OVER(PARTITION BY "schema_name"
                                      ,"attribute_name"
                        -- Order the partition by the choice's orginal order number
                        ORDER BY "original_publish_date" ASC NULLS LAST
                                ,"original_order" ASC) AS "code"
    FROM "orders"
  )
-- Profit
SELECT
    "schema"."name"
  , "schema"."publish_date"
  , "attribute"."name"
  , "choice"."title"
  , "choice"."value"
  , "choice"."order"
  , ( SELECT "code"
      FROM "codes"
      WHERE "schema_name" = "schema"."name"
      AND   "attribute_name" = "attribute"."name"
      AND   "choice_value" = "choice"."value") AS "code"
FROM "choice"
JOIN "attribute" ON "attribute"."id" = "choice"."attribute_id"
JOIN "schema" ON "schema"."id" = "attribute"."schema_id"
ORDER BY "schema"."name" ASC
        ,"schema"."publish_date" ASC NULLS LAST
        ,"attribute"."name" ASC
        ,"choice"."order" ASC
;

-- Swap with above
UPDATE "choice"
SET value = CASE value
                WHEN 'yes' THEN '1'
                WHEN 'true' THEN '1'
                WHEN 'no' THEN '0'
                WHEN 'false' THEN '0'
                ELSE "codes"."code"
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

