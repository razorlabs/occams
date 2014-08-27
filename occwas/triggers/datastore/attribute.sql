---
--- avrc_data/attribute -> pirc/attribute + pirc/section
---
--- Splits old attribute in to attribute/section
--- where section is populated with object-type attributes
---

DROP FOREIGN TABLE IF EXISTS attribute_ext;


DROP TYPE IF EXISTS attribute_type_ext;
CREATE TYPE attribute_type_ext AS ENUM('blob','boolean','choice','date','datetime','decimal','integer','string','text');

CREATE FOREIGN TABLE attribute_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , schema_id       INTEGER NOT NULL
  , type            attribute_type_ext
  , checksum        VARCHAR NOT NULL
  , is_collection   BOOLEAN NOT NULL
  , is_required     BOOLEAN NOT NULL
  , is_private      BOOLEAN NOT NULL
  , value_min       INTEGER
  , value_max       INTEGER
  , collection_min  INTEGER
  , collection_max  INTEGER
  , validator       VARCHAR
  , "order"         INTEGER NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'attribute');


DROP FOREIGN TABLE IF EXISTS section_ext;


CREATE FOREIGN TABLE section_ext (
    id              INTEGER NOT NULL

  , schema_id       INTEGER NOT NULL
  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT
  , "order"         INTEGER NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'section');


DROP FOREIGN TABLE IF EXISTS section_attribute_ext;


CREATE FOREIGN TABLE section_attribute_ext (
    section_id      INTEGER NOT NULL
  , attribute_id    INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'section_attribute');

DROP FUNCTION IF EXISTS ext_attribute_id(INTEGER);

--
-- Helper function to find the attribute id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_attribute_id(id INTEGER) RETURNS integer AS $$
  BEGIN
    RETURN (
        SELECT "attribute_ext".id
        FROM "attribute_ext"
        WHERE (old_db, old_id) = (SELECT current_database(), $1));
  END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS ext_section_id(INTEGER);

--
-- Helper function to find the section  id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_section_id(id INTEGER) RETURNS integer AS $$
  BEGIN
    RETURN (
        SELECT "section_ext".id
        FROM "section_ext"
        WHERE (old_db, old_id) = (SELECT current_database(), $1));
  END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION attribute_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NEW.object_schema_id IS NULL THEN
          PERFORM dblink_connect('trigger_target');
          INSERT INTO attribute_ext (
              id
            , name
            , title
            , description
            , schema_id
            , type
            , checksum
            , is_collection
            , is_required
            , is_private
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
            , revision
            , old_db
            , old_id
          )
          VALUES (
              (SELECT val FROM dblink('SELECT nextval(''attribute_id_seq'') AS val') AS sec(val int))
            , NEW.name
            , NEW.title
            , NEW.description
            , ext_schema_id(NEW.schema_id)
            -- We cannot set CHOICE type on insert because we have no way of knowing if the
            -- attribute will have choices that will reference it, we'll have to take care of
            -- this on the ``choice`` insert trigger.
            , NEW.type::text::attribute_type_ext
            , NEW.checksum
            , NEW.is_collection
            , NEW.is_required
            , ((SELECT current_database() LIKE '%phi%')
                OR NEW.name = 'sexpart_et_name')
            , NEW.value_min
            , NEW.value_max
            , NEW.collection_min
            , NEW.collection_max
            , NEW.validator
            -- sub-attribute orders are independent of of the parent schema
            -- in the old system
            , NEW."order" + COALESCE((SELECT ("order" + 1) * 1000 FROM attribute as parent WHERE parent.object_schema_id = NEW.schema_id), 0)
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            , (SELECT current_database())
            , NEW.id
          );
          PERFORM dblink_disconnect();

          -- Check if the attribute is supposed to be a sub-attribute
          IF EXISTS(SELECT 1 FROM "attribute" WHERE object_schema_id = NEW.schema_id) THEN
            INSERT INTO section_attribute_ext (
                section_id
              , attribute_id
              )
            VALUES (
                ext_section_id((SELECT id FROM attribute WHERE object_schema_id = NEW.schema_id))
              , ext_attribute_id(NEW.id)
            ) ;
          END IF;

        ELSE

          PERFORM dblink_connect('trigger_target');
          INSERT INTO section_ext (
              id
            , name
            , title
            , description
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
              (SELECT val FROM dblink('SELECT nextval(''section_id_seq'') AS val') AS sec(val int))
            , NEW.name
            , NEW.title
            , NEW.description
            , ext_schema_id(NEW.schema_id)
            , NEW."order"
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            , (SELECT current_database())
            , NEW.id
          );
          PERFORM dblink_disconnect();

        END IF;

        RETURN NEW;

      WHEN 'DELETE' THEN
        IF OLD.object_schema_id IS NULL THEN
          DELETE FROM attribute_ext
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        ELSE
          -- Delete sub-attributes
          DELETE FROM attribute_ext
          USING section_attribute_ext, section_ext
          WHERE section_attribute_ext.attribute_id = attribute_ext.id
          AND   section_attribute_ext.section_id = section_ext.id
          AND   (section_ext.old_db, section_ext.old_id) = (SELECT current_database(), OLD.id);
          -- Finally, delete the parent attribute
          DELETE FROM section_ext
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        END IF;
        RETURN OLD;
      WHEN 'UPDATE' THEN

        IF NEW.object_schema_id IS NULL THEN

          UPDATE attribute_ext
          SET name = NEW.name
            , title = NEW.title
            , description = NEW.description
            , schema_id = ext_schema_id(NEW.schema_id)
            , type = (CASE
                       WHEN EXISTS(SELECT 1 FROM choice WHERE choice.attribute_id = OLD.id) THEN 'choice'::text
                       ELSE NEW.type::text
                     END)::attribute_type_ext
            , checksum = NEW.checksum
            , is_collection = NEW.is_collection
            , is_required = NEW.is_required
            , is_private = ((SELECT current_database() LIKE '%phi%')
                OR NEW.name = 'sexpart_et_name')
            , value_min = NEW.value_min
            , value_max = NEW.value_max
            , collection_min = NEW.collection_min
            , collection_max = NEW.collection_max
            , validator = NEW.validator
            -- sub-attribute orders are independent of of the parent schema
            -- in the old system
            , "order" = NEW."order" + COALESCE((SELECT ("order" + 1) * 1000 FROM attribute as parent WHERE parent.object_schema_id = NEW.schema_id), 0)
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
            , old_db = (SELECT current_database())
            , old_id = NEW.id
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);

          -- Check if the attribute is supposed to be a sub-attribute
          IF EXISTS(SELECT 1 FROM "attribute" WHERE object_schema_id = NEW.schema_id) THEN

            UPDATE section_attribute_ext
            SET section_id = ext_section_id((SELECT id FROM attribute WHERE object_schema_id = NEW.schema_id))
              , attribute_id = ext_attribute_id(NEW.id)
            WHERE section_id = (SELECT * FROM ext_section_id((SELECT id FROM attribute WHERE object_schema_id = OLD.schema_id)))
            AND   attribute_id = (SELECT * FROM ext_attribute_id(OLD.id));

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
            , old_db = (SELECT current_database())
            , old_id = NEW.id
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);

          -- Ensure the sub-attributes get "moved" as well in the remote
          UPDATE attribute
          SET modify_date = NEW.modify_date
            , modify_user_id = NEW.modify_user_id
          WHERE schema_id = NEW.object_schema_id;

        END IF;
        RETURN NEW;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS attribute_mirror ON attribute;


CREATE TRIGGER attribute_mirror AFTER INSERT OR UPDATE OR DELETE ON attribute
  FOR EACH ROW EXECUTE PROCEDURE attribute_mirror();
