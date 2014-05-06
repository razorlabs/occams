---
--- avrc_data/schema -> pirc/schema
---
--- Not that this trigger can only update/modify published_schemata
---

DROP FOREIGN TABLE IF EXISTS schema_ext;


CREATE FOREIGN TABLE schema_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT
  , storage         VARCHAR NOT NULL
  , publish_date    DATE NOT NULL
  , retract_date    DATE
  , is_association  BOOLEAN NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'schema');


--
-- Helper function to find the schema id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_schema_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      -- Always return the root schema,
      -- since schemata are flattened in the new database
      SELECT "schema_ext".id FROM "schema_ext"
      WHERE (old_db, old_id) = (  (SELECT current_database())
                                , COALESCE((SELECT schema_id
                                           FROM "attribute"
                                           WHERE object_schema_id = $1)
                                         , $1))
      ;
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION schema_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        IF NOT NEW.is_inline THEN
          PERFORM dblink_connect('trigger_target');
          INSERT INTO schema_ext (
              id
            , name
            , title
            , description
            , storage
            , publish_date
            , retract_date
            , is_association
            , create_date
            , create_user_id
            , modify_date
            , modify_user_id
            , revision
            , old_db
            , old_id
          )
          VALUES (
              (SELECT val FROM dblink('SELECT nextval(''schema_id_seq'') AS val') AS sec(val int))
            , NEW.name
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
            , (SELECT current_database())
            , NEW.id
          );
          PERFORM dblink_disconnect();
        END IF;
      WHEN 'DELETE' THEN
        DELETE FROM schema_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
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
            , old_db = (SELECT current_database())
            , old_id = NEW.id
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        END IF;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS schema_mirror ON schema;


CREATE TRIGGER schema_mirror AFTER INSERT OR UPDATE OR DELETE ON schema
  FOR EACH ROW EXECUTE PROCEDURE schema_mirror();
