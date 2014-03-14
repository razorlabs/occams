---
--- avrc_data/reftype -> pirc/patient
---


CREATE FOREIGN TABLE reftype_ext (
    id              INTEGER PRIMARY KEY NOT NULL

  , name            INTEGER NOT NULL
  , title           INTEGER NOT NULL
  , description     VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'reftype');


CREATE OR REPLACE FUNCTION reftype_mirror() RETURNS TRIGGER AS $patient_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO reftype_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM reftype_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE reftype_ext;
      WHEN 'UPDATE' THEN
        UPDATE reftype_ext
        SET id = NEW.id
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$reftype_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER reftype_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON patient
  FOR EACH ROW EXECUTE PROCEDURE reftype_mirror();
