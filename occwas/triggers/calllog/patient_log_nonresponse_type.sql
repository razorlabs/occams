---
--- avrc_data/patient_log_nonresponse_type -> pirc/patient_log_nonresponse_type
---

DROP FOREIGN TABLE IF EXISTS patient_log_nonresponse_type_ext;


CREATE FOREIGN TABLE patient_log_nonresponse_type_ext (
    "order"         INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL

)
SERVER trigger_target
OPTIONS (table_name 'patient_log_nonresponse_type');

DROP FUNCTION IF EXISTS ext_patient_log_nonresponse_type_id(INTEGER);

--
-- Helper function to find the attribute id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_patient_log_nonresponse_type_id(id INTEGER) RETURNS INTEGER AS $$
  BEGIN
    RETURN (
        SELECT "patient_log_nonresponse_type_ext".id
        FROM "patient_log_nonresponse_type_ext"
        WHERE (old_db, old_id) = (SELECT current_database(), $1));
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION patient_log_nonresponse_type_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patient_log_nonresponse_type_ext (
            value
          , "order"
          , old_db
          , old_id
        )
        VALUES (
            NEW.value
          , NEW.order
          , (SELECT current_database())
          , NEW.id
        );
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM patient_log_nonresponse_type_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE patient_log_nonresponse_type_ext
        SET value = NEW.value
          , "order" = NEW.order
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS patient_log_nonresponse_type_mirror ON patient_log_nonresponse_type;


CREATE TRIGGER patient_log_nonresponse_type_mirror AFTER INSERT OR UPDATE OR DELETE ON patient_log_nonresponse_type
  FOR EACH ROW EXECUTE PROCEDURE patient_log_nonresponse_type_mirror();
