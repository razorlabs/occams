---
--- avrc_data/choice -> pirc/choice
--- TODO: Needs to figure out it's order...
---


CREATE FOREIGN TABLE choice_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , attribute_id    INTEGER NOT NULL
  , "order"         INTEGER NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'choice');


CREATE FOREIGN TABLE value_choice_ext (
    id              SERIAL NOT NULL

  , entity_id       INTEGER NOT NULL
  , attribute_id    INTEGER NOT NULL
  , value           INTEGER NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'value_choice');


--
-- Helper function to find the choice id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_choice_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "choice_ext".id
      FROM "choice_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION choice_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO choice_ext (
            name
          , title,
          , description,
          , schema_id
          , "order"
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            NEW.value
          , NEW.title
          , NEW.description
          , ext_schema_id(NEW.schema_id)
          , NEW."order"
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , SELECT current_database()
          , NEW.id
          );
      WHEN 'DELETE' THEN
        DELETE FROM choice_ext
        WHERE (old_db, old_id) = (SELECT current_database(), $1);
      WHEN 'TRUNCATE' THEN
        TRUNCATE choice_ext;
      WHEN 'UPDATE' THEN
        UPDATE choice_ext
        SET name = NEW.value
          , title = NEW.title
          , description = NEW.description
          , attribute_id = ext_attribute_id(NEW.attribute_id)
          , "order"  = NEW."order"
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , SELECT current_database()
          , NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), $1);

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER choice_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON choice
  FOR EACH ROW EXECUTE PROCEDURE choice_mirror();
