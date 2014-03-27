---
--- avrc_data/patient_log -> pirc/patient_log
---


CREATE FOREIGN TABLE patient_log_ext (
    id                      SERIAL NOT NULL

  , patient_id              INTEGER NOT NULL
  , patient_contact_date    TIMESTAMP  NOT NULL
  , last_text_date          DATE
  , contact_reason          VARCHAR NOT NULL
  , contact_type            VARCHAR NOT NULL
  , non_response_other      VARCHAR
  , message_left            BOOLEAN
  , comments                VARCHAR

  , create_date             TIMESTAMP  NOT NULL
  , create_user_id          INTEGER NOT NULL
  , modify_date             TIMESTAMP  NOT NULL
  , modify_user_id          INTEGER NOT NULL
  , revision                INTEGER NOT NULL

  , old_db                  VARCHAR NOT NULL
  , old_id                  INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'patient_log');


--
-- Helper function to find the attribute id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_patient_log_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "patient_log_ext".id
        FROM "patient_log_ext"
        WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION patient_log_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patient_log_ext (
          , patient_id
          , patient_contact_date
          , last_text_date
          , contact_reason
          , contact_type
          , non_response_other
          , message_left
          , comments
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            NEW.id
          , ext_patient_id(patient_id)
          , NEW.patient_contact_date
          , NEW.last_text_date
          , NEW.contact_reason
          , NEW.contact_type
          , NEW.non_response_other
          , NEW.message_left
          , NEW.comments
          , NEW.create_date
          , ext_user_id(create_user_id)
          , NEW.modify_date
          , ext_user_id(modify_user_id)
          , NEW.revision
          , SELECT current_database()
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM patient_log_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
          UPDATE patient_log_ext
          SET
            , patient_id = ext_patient_id(NEW.patient_id)
            , patient_contact_date = NEW.patient_contact_date
            , last_text_date = NEW.last_text_date
            , contact_reason = NEW.contact_reason
            , contact_type = NEW.contact_type
            , non_response_other = NEW.non_response_other
            , message_left = NEW.message_left
            , comments = NEW.comments
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
            , old_db = SELECT current_database()
            , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER patient_log_mirror AFTER INSERT OR UPDATE OR DELETE ON patient_log
  FOR EACH ROW EXECUTE PROCEDURE patient_log_mirror();
