---
--- avrc_data/category -> pirc/category
---


CREATE FOREIGN TABLE category_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , attribute_id    INTEGER NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'category');


--
-- Helper function to find the schema id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_category_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "category_ext".id
      FROM "category_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION category_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO category_ext (
            name
          , title,
          , description,
          , schema_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision)
          , old_db
          , old_id
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , ext_schema_id(NEW.schema_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , SELECT current_database()
          , NEW.id
          )
      WHEN 'DELETE' THEN
        DELETE FROM category_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'TRUNCATE' THEN
        TRUNCATE category_ext;
      WHEN 'UPDATE' THEN
        UPDATE category_ext
        SET name = NEW.value
          , title = NEW.title
          , description = NEW.description
          , attribute_id = ext_schema_id(NEW.attribute_id)
          , "order" = NEW."order"
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER category_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON category
  FOR EACH ROW EXECUTE PROCEDURE category_mirror();
