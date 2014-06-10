---
--- avrc_data/entity -> pirc/entity + pirc/state
---
--- Updates only entities that are not sub-objects,
--- all others are ignored
---

DROP FOREIGN TABLE IF EXISTS entity_ext;


CREATE FOREIGN TABLE entity_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , schema_id       INTEGER NOT NULL
  , state_id        INTEGER
  , collect_date    DATE NOT NULL
  , is_null         BOOLEAN NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'entity');


DROP FOREIGN TABLE IF EXISTS state_ext;


CREATE FOREIGN TABLE state_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'state');


DROP FUNCTION IF EXISTS ext_entity_id(INTEGER);

--
-- Helper function to find the entity id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_entity_id(id INTEGER) RETURNS integer AS $$
  BEGIN
    RETURN (
      -- Check if it's a sub-object first
      SELECT "entity_ext".id
      FROM "entity_ext"
      WHERE (old_db, old_id) = (  (SELECT current_database())
                                , COALESCE((SELECT "object"."entity_id"
                                           FROM "object"
                                           WHERE "object"."value" = $1)
                                          ,$1)))
      ;
  END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS ext_state_id(entity_state);

CREATE OR REPLACE FUNCTION ext_state_id(state entity_state) RETURNS integer AS $$
  DECLARE
    state_str varchar;
  BEGIN

    state_str := $1::varchar;

    IF state_str = 'not-done' THEN
      RETURN NULL;
    END IF;

    IF NOT EXISTS(SELECT 1 FROM "state_ext" WHERE name = state_str) THEN
      RAISE EXCEPTION 'state ''%'' not found in external', state_str;
    END IF;

    RETURN (
      SELECT "state_ext".id
      FROM "state_ext"
      WHERE name = state_str
      );
  END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION entity_mirror() RETURNS TRIGGER AS $$
  DECLARE
    v_state_id int;
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NOT EXISTS(SELECT 1 FROM schema where id = NEW.schema_id AND is_inline) THEN

          -- Get the state before trying anything so we don't waste ids
          v_state_id := ext_state_id(NEW.state);

          PERFORM dblink_connect('trigger_target');
          INSERT INTO entity_ext (
              id
            , name
            , title
            , description
            , schema_id
            , collect_date
            , state_id
            , is_null
            , create_date
            , create_user_id
            , modify_date
            , modify_user_id
            , revision
            , old_db
            , old_id
          )
          VALUES (
              (SELECT val FROM dblink('SELECT nextval(''entity_id_seq'') AS val') AS sec(val int))
            , NEW.name
            , NEW.title
            , NEW.description
            , ext_schema_id(NEW.schema_id)
            , NEW.collect_date
            -- don't worry about mapping since old states are a subset of the new states
            , v_state_id
            , (NEW.state::varchar = 'not-done')
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
        END IF;

      WHEN 'DELETE' THEN
        DELETE FROM entity_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN OLD;
      WHEN 'UPDATE' THEN

        v_state_id := ext_state_id(NEW.state);

        UPDATE entity_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , schema_id = ext_schema_id(NEW.schema_id)
          , collect_date = NEW.collect_date
          , state_id = v_state_id
          , is_null = (NEW.state::varchar = 'not-done')
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);

        RETURN NEW;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS entity_mirror ON entity;


CREATE TRIGGER entity_mirror AFTER INSERT OR UPDATE OR DELETE ON entity
  FOR EACH ROW EXECUTE PROCEDURE entity_mirror();
