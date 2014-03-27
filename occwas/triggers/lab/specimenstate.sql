---
--- avrc_data/specimenstate -> pirc/specimenstate
---


CREATE FOREIGN TABLE specimenstate_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimenstate');


CREATE OR REPLACE FUNCTION specimenstate_mirror() RETURNS TRIGGER AS $specimenstate_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimenstate_ext (
            name
          , title
          , description
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , SELECT current_database()
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM specimenstate_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE specimenstate_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
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
$specimenstate_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER specimenstate_mirror AFTER INSERT OR UPDATE OR DELETE ON specimenstate
  FOR EACH ROW EXECUTE PROCEDURE specimenstate_mirror();
