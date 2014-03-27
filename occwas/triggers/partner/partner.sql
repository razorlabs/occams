---
--- avrc_data/partner -> pirc/partner
---


CREATE FOREIGN TABLE partner_ext (
    id                  SERIAL NOT NULL

  , zid                 INTEGER NOT NULL
  , patient_id          INTEGER NOT NULL
  , enrolled_patient_id INTEGER

  , create_date         DATETIME NOT NULL
  , create_user_id      INTEGER NOT NULL
  , modify_date         DATETIME NOT NULL
  , modify_user_id      INTEGER NOT NULL
  , revision            INTEGER NOT NULL
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
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
        )
        VALUES (
            NEW.zid
          , ext_patient_id(NEW.patient_id)
          , ext_patient_id(NEW.enrolled_patient_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
        );
      WHEN 'DELETE' THEN
        DELETE FROM partner_ext WHERE zid = OLD.zid;
      WHEN 'UPDATE' THEN
        UPDATE partner_ext
        SET zid = NEW.zid
          , patient_id = ext_patient_id(NEW.patient_id)
          , enrolled_patient_id = ext_patient_id(NEW.enrolled_patient_id)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE zid = OLD.zid;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER partner_mirror AFTER INSERT OR UPDATE OR DELETE ON partner
  FOR EACH ROW EXECUTE PROCEDURE partner_mirror();
