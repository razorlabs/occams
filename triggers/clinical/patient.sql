---
--- avrc_data/patient -> pirc/patient
---


CREATE FOREIGN TABLE patient_ext (
    id              INTEGER PRIMARY KEY NOT NULL

  , site_id         INTEGER NOT NULL
  , zid             INTEGER NOT NULL
  , nurse           VARCHAR
  , our             VARCHAR NOT NULL
  , legacy_number   VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'patient');


CREATE OR REPLACE FUNCTION patient_mirror() RETURNS TRIGGER AS $patient_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patient_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM patient_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE patient_ext;
      WHEN 'UPDATE' THEN
        UPDATE patient_ext
        SET id = NEW.id
          , site_id = NEW.site_id
          , zid = NEW.zid
          , nurse = NEW.nurse
          , our = NEW.our
          , legacy_number = NEW.legacy_number
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$patient_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER patient_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON patient
  FOR EACH ROW EXECUTE PROCEDURE patient_mirror();
