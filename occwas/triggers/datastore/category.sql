---
--- avrc_data/category -> pirc/category
---

DROP FOREIGN TABLE IF EXISTS category_ext;


CREATE FOREIGN TABLE category_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'category');


DROP FUNCTION IF EXISTS ext_category_id(INTEGER);

--
-- Helper function to find the schema id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_category_id(id INTEGER) RETURNS integer AS $$
  BEGIN
    RETURN (
      SELECT "category_ext".id
      FROM "category_ext"
      WHERE old_db = (SELECT current_database()) AND old_id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION category_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO category_ext (
            id
          , name
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
            (SELECT val FROM dblink('SELECT nextval(''category_id_seq'') AS val') AS sec(val int))
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
          );
        PERFORM dblink_disconnect();
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM category_ext
        WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE category_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS category_mirror ON category;


CREATE TRIGGER category_mirror AFTER INSERT OR UPDATE OR DELETE ON category
  FOR EACH ROW EXECUTE PROCEDURE category_mirror();
