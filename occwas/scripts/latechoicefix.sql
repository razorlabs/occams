
\pset pager off

ROLLBACK; BEGIN;

UPDATE choice
SET value = (1000000 + value::integer)::varchar
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND (
     (schema.name ILIKE 'Demographics%' AND attribute.name = 'orientation')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'language')
  OR (schema.name ILIKE 'HIVSerologySelfReport' AND attribute.name = 'test_kit')
  OR (schema.name ILIKE 'IEarlyTest%' AND attribute.name = 'hiv_sex')
  OR (schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'gender')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'gender')
  OR (schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'ethnicity')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'ethnicity')
  OR (schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'race')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'race')
  OR (schema.name ILIKE 'IPartnerDisclosure%' AND attribute.name = 'test_result')
  OR (schema.name ILIKE 'RapidTest%' AND attribute.name IN ('rapid2', 'result'))
  OR (schema.name ILIKE 'IFA%' AND attribute.name = 'result')
  OR (schema.name ILIKE 'ScreeningRouteOfTransmission027%' AND attribute.name = 'referral_source')
  OR (schema.name ILIKE 'WesternBlot%' AND attribute.name IN ('gp120', 'gp160', 'gp40', 'gp41', 'p18', 'p24', 'p31', 'p40', 'p51', 'p55', 'p65', 'p66', 'result'))
)
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'men' THEN '1'
    WHEN 'women' THEN '2'
    WHEN 'transgenderfm' THEN '3'
    WHEN 'transgendermf' THEN '4'
    WHEN 'unknown' THEN '5'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'Demographics%'
AND attribute.name = 'orientation'
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'english' THEN '1'
    WHEN 'spanish' THEN '2'
    WHEN 'french' THEN '3'
    WHEN 'other' THEN '4'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'Demographics%'
AND attribute.name = 'language'
;

-- checked
UPDATE ONLY choice SET value =
    CASE LOWER(choice.name)
      WHEN 'anti-hiv' THEN '1'
      WHEN 'enzygnost' THEN '2'
      WHEN 'genscreen' THEN '3'
      WHEN 'hiv' THEN '4'
      WHEN 'hiv-a' THEN '5'
      WHEN 'vironostika' THEN '6'
      WHEN 'uni-form' THEN '7'
      WHEN 'bio-rad' THEN '8'
      WHEN 'unknown' THEN '9'
      WHEN 'error' THEN '10'
      WHEN 'icma' THEN '11'
      WHEN 'oraquick' THEN '12'
      WHEN 'abbot' THEN '13'
    END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'HIVSerologySelfReport'
AND attribute.name = 'test_kit'
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'na' THEN '0'
    WHEN 'men' THEN '1'
    WHEN 'women' THEN '2'
    WHEN 'transgenderfm' THEN '3'
    WHEN 'transgendermf' THEN '4'
    WHEN 'unknown' THEN '5'
    WHEN 'transgender' THEN '6'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'IEarlyTest%'
AND attribute.name = 'hiv_sex'
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'male' THEN '1'
    WHEN 'female' THEN '2'
    WHEN 'transfemale2male' THEN '3'
    WHEN 'transmale2female' THEN '4'
    WHEN 'other' THEN '5' -- (Not in regular demographics)
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND ((schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'gender')
      OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'gender'))
;

--checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'hispanic' THEN '1'
    WHEN 'not_hispanic' THEN '2'
    WHEN 'unknown' THEN '3'
    WHEN 'decline' THEN '4'
    WHEN 'other' THEN '5'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND ((schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'ethnicity')
      OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'ethnicity'))
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'caucasian' THEN '1'
    WHEN 'native_american' THEN '2'
    WHEN 'alaskan' THEN '3'
    WHEN 'asian' THEN '4'
    WHEN 'hawaiian' THEN '5'
    WHEN 'pacific_islander' THEN '6'
    WHEN 'black' THEN '7'
    WHEN 'decline' THEN '8'
    WHEN 'unknown' THEN '9'
    WHEN 'other' THEN '10'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND ((schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'race')
      OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'race'))
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'hiv negative' THEN '0'
    WHEN 'hiv positive' THEN '1'
    WHEN 'unknown' THEN '2'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'IPartnerDisclosure%'
AND attribute.name = 'test_result'
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'negative' THEN '0'
    WHEN 'positive' THEN '1'
    WHEN 'indeterminate' THEN '2'
  END
-- seems like nothing changed with this one...
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND ((schema.name ILIKE 'RapidTest%' AND attribute.name IN ('rapid2', 'result'))
      OR (schema.name ILIKE 'IFA%' AND attribute.name = 'result'))
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'community' THEN '1'
    WHEN 'nat' THEN '2'
    WHEN 'rds 022' THEN '3'
    WHEN 'rds 027' THEN '4'
    WHEN 'unknown' THEN '5'
    WHEN 'error' THEN '6'
    WHEN 'aeh 020' THEN '7'
    WHEN 'partner 020' THEN '8'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'ScreeningRouteOfTransmission027%'
AND attribute.name = 'referral_source'
;

-- checked
UPDATE ONLY choice SET value =
  CASE LOWER(choice.name)
    WHEN 'negative' THEN '0'
    WHEN 'positive' THEN '1'
    WHEN 'indeterminate' THEN '2'
    WHEN 'na' THEN '3'
  END
FROM attribute, schema
WHERE attribute.id = choice.attribute_id
AND schema.id = attribute.schema_id
AND schema.name ILIKE 'WesternBlot%'
AND attribute.name IN ('gp120', 'gp160', 'gp40', 'gp41', 'p18', 'p24', 'p31', 'p40', 'p51', 'p55', 'p65', 'p66', 'result')
;

-- Update the choice values only if they're not the same

ALTER TABLE string DISABLE TRIGGER value_string_mirror;

UPDATE ONLY "string"
SET value = choice.value
FROM choice, attribute, schema
WHERE choice.id = string.choice_id
AND attribute.id = string.attribute_id
AND schema.id = attribute.schema_id
AND choice.value != "string".value
AND (
     (schema.name ILIKE 'Demographics%' AND attribute.name = 'orientation')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'language')
  OR (schema.name ILIKE 'HIVSerologySelfReport' AND attribute.name = 'test_kit')
  OR (schema.name ILIKE 'IEarlyTest%' AND attribute.name = 'hiv_sex')
  OR (schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'gender')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'gender')
  OR (schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'ethnicity')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'ethnicity')
  OR (schema.name ILIKE 'IPartnerDemographics%' AND attribute.name = 'race')
  OR (schema.name ILIKE 'Demographics%' AND attribute.name = 'race')
  OR (schema.name ILIKE 'IPartnerDisclosure%' AND attribute.name = 'test_result')
  OR (schema.name ILIKE 'RapidTest%' AND attribute.name IN ('rapid2', 'result'))
  OR (schema.name ILIKE 'IFA%' AND attribute.name = 'result')
  OR (schema.name ILIKE 'ScreeningRouteOfTransmission027%' AND attribute.name = 'referral_source')
  OR (schema.name ILIKE 'WesternBlot%' AND attribute.name IN ('gp120', 'gp160', 'gp40', 'gp41', 'p18', 'p24', 'p31', 'p40', 'p51', 'p55', 'p65', 'p66', 'result'))
)
;

ALTER TABLE string ENABLE TRIGGER value_string_mirror;

--COMMIT;
