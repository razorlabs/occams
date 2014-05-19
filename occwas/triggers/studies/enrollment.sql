---
--- avrc_data/enrollment -> pirc/enrollment
---

DROP FOREIGN TABLE IF EXISTS enrollment_ext;


CREATE FOREIGN TABLE enrollment_ext (
    id                  INTEGER NOT NULL

  , zid                 INTEGER NOT NULL
  , patient_id          INTEGER NOT NULL
  , study_id            INTEGER NOT NULL
  , consent_date        DATE NOT NULL
  , latest_consent_date DATE NOT NULL
  , termination_date    DATE
  , reference_number    VARCHAR

  , create_date         TIMESTAMP NOT NULL
  , create_user_id      INTEGER NOT NULL
  , modify_date         TIMESTAMP NOT NULL
  , modify_user_id      INTEGER NOT NULL
  , revision            INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'enrollment');


CREATE OR REPLACE FUNCTION ext_enrollment_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "enrollment_ext".id
      FROM "enrollment_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION enrollment_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO enrollment_ext(
            id
          , zid
          , patient_id
          , study_id
          , consent_date
          , latest_consent_date
          , termination_date
          , reference_number
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            (SELECT val FROM dblink('SELECT nextval(''enrollment_id_seq'') AS val') AS sec(val int))
          , NEW.zid
          , ext_patient_id(NEW.patient_id)
          , ext_study_id(NEW.study_id)
          , NEW.consent_date
          , NEW.latest_consent_date
          , NEW.termination_date
          , NEW.reference_number
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
        PERFORM dblink_disconnect();
      WHEN 'DELETE' THEN
        DELETE FROM enrollment_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE enrollment_ext
        SET zid = NEW.zid
          , patient_id = ext_patient_id(NEW.patient_id)
          , study_id = ext_study_id(NEW.study_id)
          , consent_date = NEW.consent_date
          , latest_consent_date = NEW.latest_consent_date
          , termination_date = NEW.termination_date
          , reference_number = NEW.reference_number
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS enrollment_mirror ON enrollment;


CREATE TRIGGER enrollment_mirror AFTER INSERT OR UPDATE OR DELETE ON enrollment
  FOR EACH ROW EXECUTE PROCEDURE enrollment_mirror();
