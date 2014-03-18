---
--- avrc_data/aliquottype -> pirc/aliquottype
---


CREATE FOREIGN TABLE aliquottype_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR
  , specimentype_id INTEGER
  , location_id     INTEGER

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'aliquottype');


CREATE OR REPLACE FUNCTION aliquottype_mirror() RETURNS TRIGGER AS $aliquottype_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO aliquottype_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM aliquottype_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE aliquottype_ext;
      WHEN 'UPDATE' THEN
        UPDATE aliquottype_ext
        SET id = NEW.id
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , specimentype_id = NEW.specimentype_id
          , location_id = NEW.location_id
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$aliquottype_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER aliquottype_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON aliquottype
  FOR EACH ROW EXECUTE PROCEDURE aliquottype_mirror();
