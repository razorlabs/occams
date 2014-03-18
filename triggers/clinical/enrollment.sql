---
--- avrc_data/enrollment -> pirc/enrollment
---


CREATE FOREIGN TABLE enrollment_ext (
    id                  SERIAL NOT NULL

  , zid                 INTEGER NOT NULL
  , patient_id          INTEGER NOT NULL
  , study_id            INTEGER NOT NULL
  , consent_date        DATE NOT NULL
  , latest_consent_date DATE NOT NULL
  , termination_date    DATE
  , reference_number    VARCHAR

  , create_date         DATETIME NOT NULL
  , create_user_id      INTEGER NOT NULL
  , modify_date         DATETIME NOT NULL
  , modify_user_id      INTEGER NOT NULL
  , revision            INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'enrollment');


CREATE OR REPLACE FUNCTION enrollment_mirror() RETURNS TRIGGER AS $enrollment_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO enrollment_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM enrollment_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE enrollment_ext;
      WHEN 'UPDATE' THEN
        UPDATE enrollment_ext
        SET id = NEW.id
          , zid = NEW.zid
          , patient_id = NEW.patient_id
          , study_id = NEW.study_id
          , consent_date = NEW.consent_date
          , latest_consent_date = NEW.latest_consent_date
          , termination_date = NEW.termination_date
          , reference_number = NEW.reference_number
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$enrollment_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER enrollment_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON enrollment
  FOR EACH ROW EXECUTE PROCEDURE enrollment_mirror();
