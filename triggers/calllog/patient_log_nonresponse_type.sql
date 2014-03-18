---
--- avrc_data/patient_log_nonresponse_type -> pirc/patient_log_nonresponse_type
---


CREATE FOREIGN TABLE patient_log_nonresponse_type_ext (
    id              SERIAL NOT NULL

  , value           VARCHAR NOT NULL
  , order           INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'patient_log_nonresponse_type');


CREATE OR REPLACE FUNCTION patient_log_nonresponse_type_mirror() RETURNS TRIGGER AS $patient_log_nonresponse_type_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patient_log_nonresponse_type_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM patient_log_nonresponse_type_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE patient_log_nonresponse_type_ext;
      WHEN 'UPDATE' THEN
        UPDATE patient_log_nonresponse_type_ext
        SET id = NEW.id
          , value = NEW.value
          , order = NEW.order
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$patient_log_nonresponse_type_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER patient_log_nonresponse_type_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON patient_log_nonresponse_type
  FOR EACH ROW EXECUTE PROCEDURE patient_log_nonresponse_type_mirror();
