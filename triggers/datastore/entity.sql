---
--- avrc_data/entity -> pirc/entity + pirc/state
---
--- Updates only entities that are not sub-objects,
--- all others are ignored
---


CREATE FOREIGN TABLE entity_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , schema_id       INTEGER NOT NULL
  , state_id        INTEGER NOT NULL
  , collect_date    DATE NOT NULL
  , is_null         BOOLEAN NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'entity');


CREATE FOREIGN TABLE state_ext (
    id              SERIAL NOT NULL

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
OPTIONS (table_name 'entity');


--
-- Helper function to find the entity id in the new system using
-- the old system id number
-- TODO: NEEDS TO CONSIDER IF IT'S IN A SUBOBJECT!!!
--
CREATE OR REPLACE FUNCTION ext_entity_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "entity_ext".id
        FROM "entity_ext"
        WHERE (schema_id, name) = (SELECT ext_schema_id(schema_id), name FROM "entity" WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;

--
-- Helper function to find the state id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_state_id(name) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "state_ext".id
        FROM "section_ext"
        WHERE name = $1;
  END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION entity_mirror() RETURNS TRIGGER AS $entity_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NOT EXISTS(SELECT 1 FROM schema where id = NEW.schema_id AND is_inline) THEN

          INSERT INTO entity_ext (
              name
            , title,
            , description,
            , schema_id
            , collect_date
            , state_id
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
            , collect_date = NEW.collect_date
            , ext_state_id(NEW.state)
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            );

        END IF;

      WHEN 'DELETE' THEN
        DELETE FROM entity_ext WHERE id = ext_entity_id(OLD.id)
      WHEN 'TRUNCATE' THEN
        TRUNCATE entity_ext;
      WHEN 'UPDATE' THEN

        UPDATE entity_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , schema_id = ext_schema_id(NEW.schema_id)
          , collect_date = NEW.collect_date
          , state = ext_state_id(NEW.state)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = ext_entity_id(OLD.id)

    END CASE;
    RETURN NULL;
  END;
$entity_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER entity_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON entity
  FOR EACH ROW EXECUTE PROCEDURE entity_mirror();
