---
--- avrc_data/attribute -> pirc/attribute + pirc/section
---
--- Does not handle ``is_private`` since there's not way to do this in the old system
--  ``order`` might also be a problem...
---


CREATE FOREIGN TABLE attribute_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , schema_id       INTEGER NOT NULL
  , type            VARCHAR NOT NULL
  , checksum        VARCHAR NOT NULL
  , is_collection   BOOLEAN NOT NULL
  , is_required     BOOLEAN NOT NULL
  , is_private      BOOLEAN NOT NULL
  , value_min       INTEGER
  , value_max       INTEGER
  , collection_min  INTEGER
  , collection_max  INTEGER
  , validator       VARCHAR
  , "order"

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'attribute');


CREATE FOREIGN TABLE section_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT
  , "order"         INTEGER

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'attribute');


CREATE FOREIGN TABLE section_attribute_ext (
    section_id      INTEGER NOT NULL
    attribute_id    INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'section_attribute');


--
-- Helper function to find the attribute id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_attribute_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "attribute_ext".id
        FROM "attribute_ext"
        WHERE (schema_id, name) = (SELECT ext_schema_id(schema_id), name FROM "attribute" WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;

--
-- Helper function to find the section  id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_attribute_id(attribute_id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "section_ext".id
        FROM "section_ext"
        WHERE (schema_id, name) = (SELECT schema_id, name FROM "attribute" WHERE id = $1 AND type = 'object');
  END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION attribute_mirror() RETURNS TRIGGER AS $attribute_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NEW.object_schema_id IS NULL THEN

          INSERT INTO attribute_ext (
              name
            , title,
            , description,
            , schema_id
            , type
            , checksum
            , is_collection
            , is_required
            , value_min
            , value_max
            , collection_min
            , collection_max
            , validator
            , "order"
            , create_date
            , create_user_id
            , modify_date
            , modify_user_id
            , revision)
          VALUES (
              NEW.name
            , NEW.title
            , NEW.description
            , ext_schema_id(NEW.schema_id)
            , NEW.type -- No object or choice...
            , NEW.checksum
            , NEW.is_collection
            , NEW.is_required
            , NEW.value_min
            , NEW.value_max
            , NEW.collection_min
            , NEW.collection_max
            , NEW.validator
            , NEW."order"
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            )

          -- Check if the attribute is supposed to be a sub-attribute
          IF EXISTS(SELECT 1 FROM "attribute" WHERE object_schema_id = NEW.schema_id) THEN
            INSERT INTO section_attribute_ext (
                section_id
              , attribute_id
              )
            VALUES (
              ext_section_id(NEW.attribute_id)
              ext_attribute_id(NEW.attribute_id)
          END IF;

        ELSE

          INSERT INTO section_ext (
              name
            , title,
            , description,
            , schema_id
            , "order"
            , create_date
            , create_user_id
            , modify_date
            , modify_user_id
            , revision)
          VALUES (
              NEW.name
            , NEW.title
            , NEW.description
            , ext_schema_id(NEW.schema_id)
            , NEW."order"
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            )


        END IF;

      WHEN 'DELETE' THEN
        IF OLD.object_schema_id IS NULL THEN
          DELETE FROM attribute_ext WHERE id = ext_attribute_id(OLD.id)
        ELSE
          DELETE FROM section_ext WHERE id = ext_section_id(OLD.id)
        END IF;
      WHEN 'TRUNCATE' THEN
        TRUNCATE attribute_ext;
        TRUNCATE section_ext;
      WHEN 'UPDATE' THEN

        IF NEW.object_schema_id IS NULL THEN

          UPDATE attribute_ext
          SET name = NEW.name
            , title = NEW.title
            , description = NEW.description
            , schema_id = ext_schema_id(NEW.schema_id)
            , type = NEW.type
            , checksum = NEW.checksum
            , is_collection = NEW.is_collection
            , is_required = NEW.is_required
            , value_min = NEW.value_min
            , value_max = NEW.value_max
            , collection_min = NEW.collection_min
            , collection_max = NEW.collection_max
            , validator = NEW.validator
            , "order" = NEW."order"
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
          WHERE id = ext_attribute__id(OLD.id)

          -- Check if the attribute is supposed to be a sub-attribute
          IF EXISTS(SELECT 1 FROM "attribute" WHERE object_schema_id = NEW.schema_id) THEN

            UPDATE section_attribute_ext
            SET section_id = ext_section_id(NEW.attribute_id)
              , attribute_id = ext_attribute_id(NEW.attribute_id)
            WHERE section_id = ext_section_id(OLD.attribute_id)
                , attribute_id = ext_attribute_id(OLD.attribute_id)

          END IF;

        ELSE

          UPDATE section_ext
          SET name = NEW.name
            , title = NEW.title
            , description = NEW.description
            , schema_id = ext_schema_id(NEW.schema_id)
            , "order" = NEW."order"
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
          WHERE id = ext_section_id(OLD.id)

        END IF;

    END CASE;
    RETURN NULL;
  END;
$attribute_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER attribute_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON attribute
  FOR EACH ROW EXECUTE PROCEDURE attribute_mirror();
