---
--- avrc_data/schema -> pirc/schema
---


CREATE FOREIGN TABLE schema_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT
  , storage         VARCHAR NOT NULL
  , publish_date    DATE NOT NULL
  , retract_date    DATE
  , is_association  BOOLEAN NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'schema');


--
-- Helper function to find the schema id in the new system using
-- the old system id number
--
-- TODO: NEEDS PUBLISH_DATE!!!
--
CREATE OR REPLACE FUNCTION ext_schema_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "schema_ext".id FROM "schema_ext" WHERE name = COALESCE(
          -- Check if it's a sub-attribute first...
          SELECT name FROM "schema" JOIN "attribute" ON "id" = "attribute"."schema_id" WHERE "attribute"."object_schema_id" = $1,
          -- Not a sub attribute, use schema id directly
          SELECT name FROM "schema" WHERE id = $1
          )
  END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION schema_mirror() RETURNS TRIGGER AS $schema_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO schema_ext (
            name
          , title,
          , description,
          , storage
          , publish_date
          , retract_date
          , is_association
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision)
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , NEW.storage
          , NEW.publish_date
          , CASE NEW.state WHEN 'retracted' THEN NEW.modify_date ELSE NULL END
          , NEW.is_association
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          )
      WHEN 'DELETE' THEN
        DELETE FROM schema_ext WHERE name = OLD.name;
      WHEN 'TRUNCATE' THEN
        TRUNCATE schema_ext;
      WHEN 'UPDATE' THEN
        -- Don't need to update subschemata as they don't exist in the new system
        IF NOT NEW.is_inline THEN
          UPDATE schema_ext
          SET name = NEW.name
            , title = NEW.title
            , description = NEW.description
            , storage = NEW.storage
            , publish_date = NEW.publish_date
            , retract_date = CASE NEW.state WHEN 'retracted' THEN NEW.modify_date ELSE NULL END
            , is_association = NEW.is_association

            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
          WHERE name = NEW.name;
        END IF;

    END CASE;
    RETURN NULL;
  END;
$schema_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER schema_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON schema
  FOR EACH ROW EXECUTE PROCEDURE schema_mirror();
