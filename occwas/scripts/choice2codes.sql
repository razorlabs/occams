-- Converts all legacy choices to code format
-- This is necessary in order to be able to keep legacy/future databases synchronized

BEGIN;

-- Update choice values in order of their introduction
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
UPDATE "choice"
SET value = CASE LOWER(value)
                WHEN 'yes' THEN '1'
                WHEN 'true' THEN '1'
                WHEN 'no' THEN '0'
                WHEN 'false' THEN '0'
                ELSE (SELECT CASE

                                -- Overrides for backwards compatibility --

                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'vironostika' THEN  '1'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'BED' THEN  '2'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'vitros' THEN  '3'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'oraquick' THEN  '4'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'abbot' THEN  '5'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'unknown' THEN  '6'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'error' THEN  '7'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'delviron' THEN  '8'
                                WHEN ("schema_name", "attribute_name") = ('DetunedEIA', 'test_kit_type') AND "choice_value" ILIKE 'lag' THEN  '9'

                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'anti-hiv' THEN  '1'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'enzygnost' THEN  '2'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'genscreen' THEN  '3'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'hiv' THEN  '4'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'hiv a' THEN  '5'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'vironostika' THEN  '6'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'uni-form' THEN  '7'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'bio-rad' THEN  '8'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'unknown' THEN  '9'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'error' THEN  '10'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'icma' THEN  '11'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'oraquick' THEN  '12'
                                WHEN ("schema_name", "attribute_name") = ('HivSerology', 'test_kit_type') AND "choice_value" ILIKE 'abbot' THEN  '13'

                                WHEN ("schema_name", "attribute_name") = ('HivNAT', 'test_kit_type') AND "choice_value" ILIKE '%Procleix%' THEN  '1'
                                WHEN ("schema_name", "attribute_name") = ('HivNAT', 'test_kit_type') AND "choice_value" ILIKE '%APTIMA%' THEN  '2'
                                WHEN ("schema_name", "attribute_name") = ('HivNAT', 'test_kit_type') AND "choice_value" ILIKE '%Unknown%' THEN  '3'
                                WHEN ("schema_name", "attribute_name") = ('HivNAT', 'test_kit_type') AND "choice_value" ILIKE '%Error%' THEN  '4'
                                WHEN ("schema_name", "attribute_name") = ('HivNAT', 'test_kit_type') AND "choice_value" ILIKE '%Roche%' THEN  '5'

                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Roche RT-PCR (Amplicor) HIV-1 Monitor' THEN  '1'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Roche Ultra-sensitive' THEN  '2'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Chiron 1st Generation bDNA' THEN  '3'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Chiron 2nd Generation bDNA (Ultra-sensitive)' THEN  '4'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Organon (Teknika) NASBA' THEN  '5'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Organon (Tenika) Nuclisens' THEN  '6'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Roche RT-PCR (Amplicor) HIV-1 Monitor V 1.5' THEN  '7'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Roche COBAS (Amplicor) Ultrasensitive V 1.5' THEN  '8'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Bayer HIV-1 RNA Assay V 3.0 (bDNA)' THEN  '9'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Roche Ampliprep Taqman' THEN  '10'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Abbot M2000 Taqman' THEN  '11'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Unknown' THEN  '12'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Error' THEN  '13'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Chiron Reference Lab' THEN  '14'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Abbot Real-Time HIV-1' THEN  '15'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Procleix' THEN  '16'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Proprietary Method Of National Genetics Institute' THEN  '17'
                                WHEN ("schema_name", "attribute_name") = ('ViralLoad', 'test_kit_type') AND "choice_value" ILIKE 'Roche Ampliprep Taqman V 2.l' THEN  '18'

                                -- Requested changes --

                                WHEN "schema_name" ILIKE 'Demographics%' AND "attribute_name" = 'orientation' THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'men' THEN '1'
                                    WHEN "choice_value" ILIKE 'women' THEN '2'
                                    WHEN "choice_value" ILIKE 'transgenderFM' THEN '3'
                                    WHEN "choice_value" ILIKE 'transgenderMF' THEN '4'
                                    WHEN "choice_value" ILIKE 'unknown' THEN '5'
                                  END

                                WHEN "schema_name" ILIKE 'Demographics%' AND "attribute_name" = 'language' THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'english' THEN '1'
                                    WHEN "choice_value" ILIKE 'spanish' THEN '2'
                                    WHEN "choice_value" ILIKE 'french' THEN '3'
                                    WHEN "choice_value" ILIKE 'other' THEN '4'
                                  END

                                WHEN "schema_name" ILIKE 'HIVSerologySelfReport' AND "attribute_name" = 'test_kit_type' THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'anti-hiv' THEN '1'
                                    WHEN "choice_value" ILIKE 'enzygnost' THEN '2'
                                    WHEN "choice_value" ILIKE 'genscreen' THEN '3'
                                    WHEN "choice_value" ILIKE 'hiv' THEN '4'
                                    WHEN "choice_value" ILIKE 'hiv a' THEN '5'
                                    WHEN "choice_value" ILIKE 'vironostika' THEN '6'
                                    WHEN "choice_value" ILIKE 'uni-form' THEN '7'
                                    WHEN "choice_value" ILIKE 'bio-rad' THEN '8'
                                    WHEN "choice_value" ILIKE 'unknown' THEN '9'
                                    WHEN "choice_value" ILIKE 'error' THEN '10'
                                    WHEN "choice_value" ILIKE 'icma' THEN '11'
                                    WHEN "choice_value" ILIKE 'oraquick' THEN '12'
                                    WHEN "choice_value" ILIKE 'abbot' THEN '13'
                                  END

                                WHEN "schema_name" ILIKE 'IEarlyTest%' AND "attribute_name" = 'hiv_sex' THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'na' THEN '0'
                                    WHEN "choice_value" ILIKE 'men' THEN '1'
                                    WHEN "choice_value" ILIKE 'women' THEN '2'
                                    WHEN "choice_value" ILIKE 'transgenderFM' THEN '3'
                                    WHEN "choice_value" ILIKE 'transgenderMF' THEN '4'
                                    WHEN "choice_value" ILIKE 'unknown' THEN '5'
                                    WHEN "choice_value" ILIKE 'transgender' THEN '6'
                                  END

                                WHEN (("schema_name" ILIKE 'IPartnerDemographics%' AND "attribute_name" = 'gender')
                                      OR ("schema_name" ILIKE 'Demographics%' AND "attribute_name" = 'gender')) THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'male' THEN '1'
                                    WHEN "choice_value" ILIKE 'female' THEN '2'
                                    WHEN "choice_value" ILIKE 'transfemale2male' THEN '3'
                                    WHEN "choice_value" ILIKE 'transmale2female' THEN '4'
                                    WHEN "choice_value" ILIKE 'other' THEN '5' -- (Not in regular demographics)
                                  END

                                WHEN (("schema_name" ILIKE 'IPartnerDemographics%' AND "attribute_name" = 'ethnicity')
                                      OR ("schema_name" ILIKE 'Demographics%' AND "attribute_name" = 'ethnicity')) THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'hispanic' THEN '1'
                                    WHEN "choice_value" ILIKE 'not_hispanic' THEN '2'
                                    WHEN "choice_value" ILIKE 'unknown' THEN '3'
                                    WHEN "choice_value" ILIKE 'decline' THEN '4'
                                    WHEN "choice_value" ILIKE 'other' THEN '5'
                                  END

                                WHEN (("schema_name" ILIKE 'IPartnerDemographics%' AND "attribute_name" = 'race')
                                      OR ("schema_name" ILIKE 'Demographics%' AND "attribute_name" = 'race')) THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'caucasian' THEN '1'
                                    WHEN "choice_value" ILIKE 'native_american' THEN '2'
                                    WHEN "choice_value" ILIKE 'alaskan' THEN '3'
                                    WHEN "choice_value" ILIKE 'asian' THEN '4'
                                    WHEN "choice_value" ILIKE 'hawaiian' THEN '5'
                                    WHEN "choice_value" ILIKE 'pacific_islander' THEN '6'
                                    WHEN "choice_value" ILIKE 'black' THEN '7'
                                    WHEN "choice_value" ILIKE 'decline' THEN '8'
                                    WHEN "choice_value" ILIKE 'unknown' THEN '9'
                                    WHEN "choice_value" ILIKE 'other' THEN '10'
                                  END

                                WHEN "schema_name" ILIKE 'IPartnerDisclosure%' AND "attribute_name" = 'test_result' THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'Early Test Site' THEN '0'
                                    WHEN "choice_value" ILIKE 'Other' THEN '1'
                                    WHEN "choice_value" ILIKE 'Unknown' THEN '2'
                                  END

                                -- seems like nothing changed with this one...
                                WHEN (("schema_name" ILIKE 'RapidTest%' AND "attribute_name" IN ('verify_result', 'result'))
                                      OR ("schema_name" ILIKE 'IFA%' AND "attribute_name" = 'result')) THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'Negative' THEN '0'
                                    WHEN "choice_value" ILIKE 'positive' THEN '1'
                                    WHEN "choice_value" ILIKE 'Indeterminate' THEN '2'
                                  END

                                WHEN "schema_name" ILIKE 'ScreeningRouteOfTransmission027%' AND "attribute_name" = 'referral_source' THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'community' THEN '1'
                                    WHEN "choice_value" ILIKE 'nat' THEN '2'
                                    WHEN "choice_value" ILIKE 'rds 022' THEN '3'
                                    WHEN "choice_value" ILIKE 'rds 027' THEN '4'
                                    WHEN "choice_value" ILIKE 'unknown' THEN '5'
                                    WHEN "choice_value" ILIKE 'error' THEN '6'
                                    WHEN "choice_value" ILIKE 'aeh 020' THEN '7'
                                    WHEN "choice_value" ILIKE 'partner 020' THEN '8'
                                  END

                                WHEN "schema_name" ILIKE 'WesternBlot%' AND "attribute_name" IN ('gp120', 'gp160', 'gp40', 'gp41', 'p18', 'p24', 'p31', 'p40', 'p51', 'p55', 'p65', 'p66', 'result') THEN
                                  CASE
                                    WHEN "choice_value" ILIKE 'negative' THEN '0'
                                    WHEN "choice_value" ILIKE 'positive' THEN '1'
                                    WHEN "choice_value" ILIKE 'indeterminate' THEN '2'
                                    WHEN "choice_value" ILIKE 'na' THEN '3'
                                  END

                                -- Preferred case --

                                ELSE "code"::text
                              END
                      FROM "codes"
                      WHERE "codes"."choice_value" = "choice"."value"
                      AND   "codes"."attribute_name" = "attribute"."name"
                      AND   "codes"."schema_name" = "schema"."name"
                      LIMIT 1)
            END
FROM "attribute", "schema"
WHERE "attribute"."id" = "choice"."attribute_id"
AND   "schema"."id" = "attribute"."schema_id"
AND   EXISTS(SELECT 1
             FROM "choice" AS "lchoice"
             WHERE "lchoice"."attribute_id" = "choice"."attribute_id"
             AND "value" !~ '^[0-9]+$')
;


-- Lockdown the choice
ALTER TABLE choice ADD CONSTRAINT ck_value_numeric CHECK(value ~ '^[0-9]+$');
ALTER TABLE choice ALTER COLUMN value SET DATA TYPE VARCHAR(8);


-- Update string values (OCCWAS stores BOTH value and choice_id)
UPDATE "string"
SET "value" = "choice"."value"
FROM "choice"
WHERE "choice"."id" = "string"."choice_id"
;

-- Migrate integer-based choices (Going forward with strings as choices in OCCWAS)
WITH deleted AS (
  DELETE FROM "integer"
  WHERE "choice_id" IS NOT NULL
  RETURNING *
)
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
FROM deleted
;

-- Force choices as strings until we get to OCCAMS
UPDATE "attribute"
SET "type" = 'string'
WHERE EXISTS(SELECT 1
             FROM "choice"
             WHERE "choice"."attribute_id" = "attribute"."id")
;

COMMIT;
