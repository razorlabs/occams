-- Remove form workflow in favor of simple publish/retract dates
BEGIN;

ALTER TABLE schema
  DROP CONSTRAINT ck_schema_valid_publication
  , ADD COLUMN retract_date DATE
  , ADD CONSTRAINT ck_schema_valid_publication
      CHECK (publish_date <= retract_date)
  ;

ALTER TABLE schema_audit ADD COLUMN retract_date DATE;

UPDATE schema
SET retract_date = modify_date
WHERE state = 'retracted';

UPDATE schema_audit
SET retract_date = modify_date
WHERE state = 'retracted';

ALTER TABLE schema DROP COLUMN state;
ALTER TABLE schema_audit DROP COLUMN state;

COMMIT;
