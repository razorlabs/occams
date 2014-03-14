---
--- avrc_data/partner -> pirc/partner
---


CREATE FOREIGN TABLE partner_ext (
    id                  INTEGER PRIMARY KEY NOT NULL

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


CREATE OR REPLACE FUNCTION partner_mirror() RETURNS TRIGGER AS $partner_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO partner_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM partner_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE partner_ext;
      WHEN 'UPDATE' THEN
        UPDATE partner_ext
        SET id = NEW.id
          , patient_id = NEW.patient_id
          , enrolled_patient_id = NEW.enrolled_patient_id
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$partner_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER partner_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON partner
  FOR EACH ROW EXECUTE PROCEDURE partner_mirror();
