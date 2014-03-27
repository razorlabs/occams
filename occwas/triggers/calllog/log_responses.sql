---
--- avrc_data/log_responses -> pirc/log_responses
---

DROP FOREIGN TABLE IF EXISTS log_responses_ext;


CREATE FOREIGN TABLE log_responses_ext (
    patient_log_id                  INTEGER NOT NULL
  , patient_log_nonresponse_type_id INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'log_responses');


CREATE OR REPLACE FUNCTION log_responses_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO log_responses_ext (
            patient_log_id
          , patient_log_nonresponse_type_id
        )
        VALUES (
            ext_patient_log_id(NEW.patient_log_id)
          , ext_patient_log_nonresponse_type_id(NEW.patient_log_nonresponse_type_id)
        );
      WHEN 'DELETE' THEN
        DELETE FROM log_responses_ext
        WHERE patient_log_id = ext_patient_log_id(OLD.patient_log_id)
        AND   patient_log_nonresponse_type_id = ext_patient_log_nonresponse_type_id(OLD.patient_log_nonresponse_type_id)
        ;
      WHEN 'UPDATE' THEN
        UPDATE log_responses_ext
        SET patient_log_id = ext_patient_log_id(NEW.patient_log_id)
          , patient_log_nonresponse_type_id = ext_patient_log_nonresponse_type_id(NEW.patient_log_nonresponse_type_id)
        WHERE patient_log_id = ext_patient_log_id(OLD.patient_log_id)
        AND   patient_log_nonresponse_type_id = ext_patient_log_nonresponse_type_id(OLD.patient_log_nonresponse_type_id)
        ;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS log_responses_mirror ON log_responses;


CREATE TRIGGER log_responses_mirror AFTER INSERT OR UPDATE OR DELETE ON log_responses
  FOR EACH ROW EXECUTE PROCEDURE log_responses_mirror();
