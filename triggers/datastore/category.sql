---
--- avrc_data/category -> pirc/category
---


CREATE FOREIGN TABLE category_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
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
      WHERE name = (SELECT name FROM "category" WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION category_mirror() RETURNS TRIGGER AS $category_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO category_ext (
            name
          , title,
          , description,
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision)
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          )
      WHEN 'DELETE' THEN
        DELETE FROM category_ext WHERE name = OLD.name;
      WHEN 'TRUNCATE' THEN
        TRUNCATE category_ext;
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
        WHERE name = OLD.name;
    END CASE;
    RETURN NULL;
  END;
$category_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER category_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON category
  FOR EACH ROW EXECUTE PROCEDURE category_mirror();
