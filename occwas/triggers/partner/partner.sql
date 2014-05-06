---
--- avrc_data/partner -> pirc/partner
---

DROP FOREIGN TABLE IF EXISTS partner_ext;


CREATE FOREIGN TABLE partner_ext (
    id                  SERIAL NOT NULL

  , zid                 INTEGER NOT NULL
  , patient_id          INTEGER NOT NULL
  , enrolled_patient_id INTEGER
  , report_date         DATE NOT NULL

  , create_date         TIMESTAMP NOT NULL
  , create_user_id      INTEGER NOT NULL
  , modify_date         TIMESTAMP NOT NULL
  , modify_user_id      INTEGER NOT NULL
  , revision            INTEGER NOT NULL
  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'partner');


CREATE OR REPLACE FUNCTION partner_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO partner_ext (
            zid
          , patient_id
          , enrolled_patient_id
          , report_date
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            NEW.zid
          , ext_patient_id(NEW.patient_id)
          , ext_patient_id(NEW.enrolled_patient_id)
          , NEW.report_date
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM partner_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE partner_ext
        SET zid = NEW.zid
          , patient_id = ext_patient_id(NEW.patient_id)
          , enrolled_patient_id = ext_patient_id(NEW.enrolled_patient_id)
          , report_date = NEW.report_date
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


DROP TRIGGER IF EXISTS partner_mirror ON partner;


CREATE TRIGGER partner_mirror AFTER INSERT OR UPDATE OR DELETE ON partner
  FOR EACH ROW EXECUTE PROCEDURE partner_mirror();
