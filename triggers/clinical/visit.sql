---
--- avrc_data/visit -> pirc/visit
---


CREATE FOREIGN TABLE visit_ext (
    id              INTEGER NOT NULL

  , zid             INTEGER NOT NULL
  , patient_id      INTEGER NOT NULL
  , visit_date      DATE NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'visit');


CREATE OR REPLACE FUNCTION visit_mirror() RETURNS TRIGGER AS $visit_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO visit_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM visit_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE visit_ext;
      WHEN 'UPDATE' THEN
        UPDATE visit_ext
        SET id = NEW.id
          , zid = NEW.zid
          , patient_id = NEW.patient_id
          , visit_date = NEW.visit_date
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$visit_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER visit_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON visit
  FOR EACH ROW EXECUTE PROCEDURE visit_mirror();
