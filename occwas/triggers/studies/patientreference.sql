---
--- avrc_data/patientreference -> pirc/patientreference
---

DROP FOREIGN TABLE IF EXISTS patientreference_ext;


CREATE FOREIGN TABLE patientreference_ext (
    id                INTEGER NOT NULL

  , patient_id        INTEGER NOT NULL
  , reftype_id        INTEGER NOT NULL
  , reference_number  VARCHAR NOT NULL

  , create_date       TIMESTAMP NOT NULL
  , create_user_id    INTEGER NOT NULL
  , modify_date       TIMESTAMP NOT NULL
  , modify_user_id    INTEGER NOT NULL
  , revision          INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'patientreference');


CREATE OR REPLACE FUNCTION patientreference_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO patientreference_ext (
            id
          , patient_id
          , reftype_id
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
            (SELECT val FROM dblink('SELECT nextval(''patientreference_id_seq'') AS val') AS sec(val int))
          , ext_patient_id(NEW.patient_id)
          , ext_reftype_id(NEW.reftype_id)
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
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM patientreference_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE patientreference_ext
        SET patient_id = ext_patient_id(NEW.patient_id)
          , reftype_id = ext_reftype_id(NEW.reftype_id)
          , reference_number = NEW.reference_number
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS patientreference_mirror ON patientreference;


CREATE TRIGGER patientreference_mirror AFTER INSERT OR UPDATE OR DELETE ON patientreference
  FOR EACH ROW EXECUTE PROCEDURE patientreference_mirror();
