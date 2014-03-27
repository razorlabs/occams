---
--- avrc_data/patientreference -> pirc/patientreference
---


CREATE FOREIGN TABLE patientreference_ext (
    id                SERIAL NOT NULL

  , patient_id        INTEGER NOT NULL
  , reftype_id        INTEGER NOT NULL
  , reference_number  VARCHAR NOT NULL,

  , create_date       DATETIME NOT NULL
  , create_user_id    INTEGER NOT NULL
  , modify_date       DATETIME NOT NULL
  , modify_user_id    INTEGER NOT NULL
  , revision          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'patientreference');


CREATE OR REPLACE FUNCTION patientreference_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patientreference_ext (
          , patient_id
          , reftype_id
          , reference_number

          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
        )
        VALUES (
            ext_patient_id(NEW.patient_id)
          , ext_reftype_id(NEW.reftype_id)
          , NEW.reference_number
          , NEW.legacy_number
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        );
      WHEN 'DELETE' THEN
        DELETE FROM patientreference_ext
        WHERE (patient_id, reftype_id, reference_number) =
          (ext_patient_id(OLD.patient_id),
           ext_reftype_id(OLD.reftype_id),
           OLD.reference_number);
      WHEN 'UPDATE' THEN
        UPDATE patientreference_ext
        SET patient_id = ext_patient_id(NEW.patient_id)
          , reftype_id = ext_reftype_id(NEW.reftype_id)
          , reference_number = NEW.reference_number
          , legacy_number = NEW.legacy_number
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE (patient_id, reftype_id, reference_number) =
          (ext_patient_id(OLD.patient_id),
           ext_reftype_id(OLD.reftype_id),
           OLD.reference_number);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER patientreference_mirror AFTER INSERT OR UPDATE OR DELETE ON patientreference
  FOR EACH ROW EXECUTE PROCEDURE patientreference_mirror();
