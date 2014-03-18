---
--- avrc_data/stratum -> pirc/stratum
---


CREATE FOREIGN TABLE stratum_ext (
    id                SERIAL NOT NULL

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
        INSERT INTO stratum_ext (
            study_id
          , arm_id
          , label
          , block_number
          , reference_number
          , patient_id

          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
        )
        VALUES (
            ext_study_id(NEW.study_id)
          , ext_arm_id(NEW.arm_id)
          , label
          , block_number
          , reference_number
          , ext_patient_id(NEW.patient_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
        );
      WHEN 'DELETE' THEN
        DELETE FROM stratum_ext
        WHERE (study_id, reference_number) =
          (ext_study_id(OLD.study_id), OLD.reference_number);
      WHEN 'TRUNCATE' THEN
        TRUNCATE stratum_ext;
      WHEN 'UPDATE' THEN
        UPDATE stratum_ext
        SET study_id = ext_study_id(NEW.study_id)
          , arm_id = ext_arm_id(NEW.arm_id)
          , label = NEW.label
          , block_number = NEW.block_number
          , reference_number = NEW.reference_number
          , patient_id = ext_patient_id(NEW.patient_id)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE (study_id, reference_number) =
          (ext_study_id(OLD.study_id), OLD.reference_number);
    END CASE;
    RETURN NULL;
  END;
$stratum_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER stratum_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON stratum
  FOR EACH ROW EXECUTE PROCEDURE stratum_mirror();
