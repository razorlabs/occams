-- Scrambles scring values
-- Intended for PHI-type of data
-- Intened database: PostgreSQL
BEGIN;

UPDATE value_string SET value = regexp_replace(regexp_replace(regexp_replace(value, E'\\d', '9', 'g'), E'[A-Z]', 'X', 'g'), E'[a-z]', 'x', 'g');
UPDATE value_string_audit SET value = regexp_replace(regexp_replace(regexp_replace(value, E'\\d', '9', 'g'), E'[A-Z]', 'X', 'g'), E'[a-z]', 'x', 'g');

UPDATE value_datetime SET value = DATE '1976-07-04';
UPDATE value_datetime_audit SET value = DATE '1976-07-04';

COMMIT;
