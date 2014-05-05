---
--- avrc_data/stratum -> pirc/stratum
---

DROP FOREIGN TABLE IF EXISTS stratum_ext;


CREATE FOREIGN TABLE stratum_ext (
    id                INTEGER

  , study_id          INTEGER NOT NULL
  , arm_id            INTEGER NOT NULL
  , label             VARCHAR
  , block_number      INTEGER NOT NULL
  , reference_number  VARCHAR NOT NULL
  , patient_id        INTEGER

  , create_date       TIMESTAMP NOT NULL
  , create_user_id    INTEGER NOT NULL
  , modify_date       TIMESTAMP NOT NULL
  , modify_user_id    INTEGER NOT NULL
  , revision          INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'stratum');

--
-- Helper function to find the site id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_stratum_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "stratum_ext".id
      FROM "stratum_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION stratum_mirror() RETURNS TRIGGER AS $$
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
          , old_db
          , old_id
        )
        VALUES (
            ext_study_id(NEW.study_id)
          , ext_arm_id(NEW.arm_id)
          , NEW.label
          , NEW.block_number
          , NEW.reference_number
          , ext_patient_id(NEW.patient_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM stratum_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
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
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS stratum_mirror ON stratum;


CREATE TRIGGER stratum_mirror AFTER INSERT OR UPDATE OR DELETE ON stratum
  FOR EACH ROW EXECUTE PROCEDURE stratum_mirror();
