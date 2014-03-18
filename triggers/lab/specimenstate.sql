---
--- avrc_data/specimenstate -> pirc/specimenstate
---


CREATE FOREIGN TABLE specimenstate_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimenstate');


CREATE OR REPLACE FUNCTION specimenstate_mirror() RETURNS TRIGGER AS $specimenstate_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimenstate_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM specimenstate_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE specimenstate_ext;
      WHEN 'UPDATE' THEN
        UPDATE specimenstate_ext
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
$specimenstate_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER specimenstate_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON specimenstate
  FOR EACH ROW EXECUTE PROCEDURE specimenstate_mirror();
