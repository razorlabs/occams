---
--- avrc_data/context -> pirc/context
---


CREATE FOREIGN TABLE context_ext (
    id              INTEGER NOT NULL

  , entity_id       INTEGER NOT NULL
  , external        VARCHAR
  , key             INTEGER

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'context');


--
-- Helper function to find the context id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_context_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "context_ext".id
        FROM "context_ext"
        WHERE (entity_id, external, key) =
          (SELECT ext_entity_id(entity_id)
                , external
                , key
           FROM "context"
           WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION context_mirror() RETURNS TRIGGER AS $context_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        INSERT INTO context_ext (
          , entity_id
          , external
          , key
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision)
        VALUES (
            ext_entity_id(NEW.entity_id)
          , NEW.external
          , NEW.key
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          );

      WHEN 'DELETE' THEN
        DELETE FROM context_ext WHERE id = ext_context_id(OLD.id)
      WHEN 'TRUNCATE' THEN
        TRUNCATE context_ext;
      WHEN 'UPDATE' THEN

        UPDATE context_ext
        SET entity_id = ext_entity_id(NEW.entity_id)
          , external = NEW.external
          , key = NEW.key
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = ext_context_id(OLD.id)

    END CASE;
    RETURN NULL;
  END;
$context_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER context_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON context
  FOR EACH ROW EXECUTE PROCEDURE context_mirror();
