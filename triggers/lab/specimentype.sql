---
--- avrc_data/specimentype -> pirc/specimentype
---


CREATE FOREIGN TABLE specimentype_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR
  , type_type       VARCHAR
  , default_tubes   INTEGER
  , location_id     INTEGER

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimentype');


CREATE OR REPLACE FUNCTION specimentype_mirror() RETURNS TRIGGER AS $specimentype_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimentype_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM specimentype_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE specimentype_ext;
      WHEN 'UPDATE' THEN
        UPDATE specimentype_ext
        SET id = NEW.id
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , type_type = NEW.type_type
          , default_tubes = NEW.default_tubes
          , location_id = NEW.location_id
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$specimentype_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER specimentype_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON specimentype
  FOR EACH ROW EXECUTE PROCEDURE specimentype_mirror();
