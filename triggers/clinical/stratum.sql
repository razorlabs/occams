---
--- avrc_data/stratum -> pirc/stratum
---


CREATE FOREIGN TABLE stratum_ext (
    id                INTEGER PRIMARY KEY NOT NULL

  , study_id          INTEGER NOT NULL
  , arm_id            INTEGER NOT NULL
  , label             VARCHAR
  , block_number      INTEGER NOT NULL
  , reference_number  VARCHAR NOT NULL
  , patient_id        INTEGER

  , create_date       DATETIME NOT NULL
  , create_user_id    INTEGER NOT NULL
  , modify_date       DATETIME NOT NULL
  , modify_user_id    INTEGER NOT NULL
  , revision          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'stratum');


CREATE OR REPLACE FUNCTION stratum_mirror() RETURNS TRIGGER AS $stratum_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO stratum_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM stratum_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE stratum_ext;
      WHEN 'UPDATE' THEN
        UPDATE stratum_ext
        SET id = NEW.id
          , study_id = NEW.study_id
          , arm_id = NEW.arm_id
          , label = NEW.label
          , block_number = NEW.block_number
          , reference_number = NEW.reference_number
          , patient_id = NEW.patient_id
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$stratum_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER stratum_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON stratum
  FOR EACH ROW EXECUTE PROCEDURE stratum_mirror();
