-- Scrambles private information values
-- Intened database: PostgreSQL
BEGIN;

UPDATE value_string
SET value = regexp_replace(regexp_replace(regexp_replace(value, E'\\d', '9', 'g'), E'[A-Z]', 'X', 'g'), E'[a-z]', 'x', 'g')
FROM attribute
WHERE attribute.id = value_string.attribute_id
AND attribute.is_pii = TRUE
;

UPDATE value_string_audit
SET value = regexp_replace(regexp_replace(regexp_replace(value, E'\\d', '9', 'g'), E'[A-Z]', 'X', 'g'), E'[a-z]', 'x', 'g')
FROM attribute_audit
WHERE attribute_audit.id = value_string_audit.attribute_id
AND attribute.is_pii = TRUE
;

UPDATE value_datetime
SET value = regexp_replace(regexp_replace(regexp_replace(value, E'\\d', '9', 'g'), E'[A-Z]', 'X', 'g'), E'[a-z]', 'x', 'g')
SET value = DATE '1976-07-04';
FROM attribute
WHERE attribute.id = value_datetime.attribute_id
AND attribute.is_pii = TRUE
;

UPDATE value_datetime_audit
SET value = DATE '1976-07-04';
FROM attribute_audit
WHERE attribute_audit.id = value_datetime_audit.attribute_id
AND attribute.is_pii = TRUE
;

COMMIT;
