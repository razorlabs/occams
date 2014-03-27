---
--- avrc_data/context -> pirc/context
---

DROP FOREIGN TABLE IF EXISTS context_ext;


CREATE FOREIGN TABLE context_ext (
    id              SERIAL NOT NULL

  , entity_id       INTEGER NOT NULL
  , external        VARCHAR
  , key             INTEGER

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'context');


--
-- Helper function to find the context id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_context_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "context_ext".id
        FROM "context_ext"
        WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION context_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        INSERT INTO context_ext (
            entity_id
          , external
          , key
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            ext_entity_id(NEW.entity_id)
          , NEW.external
          , CASE
              WHEN NEW.external = 'patient' THEN ext_patient_id(NEW.key)
              WHEN NEW.external = 'enrollment' THEN ext_enrollment_id(NEW.key)
              WHEN NEW.external = 'visit' THEN ext_enrollment_id(NEW.key)
              WHEN NEW.external = 'stratum' THEN ext_stratum_id(NEW.key)
            END
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
          );

      WHEN 'DELETE' THEN
        DELETE FROM context_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN

        UPDATE context_ext
        SET entity_id = ext_entity_id(NEW.entity_id)
          , external = NEW.external
          , key = CASE
                    WHEN NEW.external = 'patient' THEN ext_patient_id(NEW.key)
                    WHEN NEW.external = 'enrollment' THEN ext_enrollment_id(NEW.key)
                    WHEN NEW.external = 'visit' THEN ext_enrollment_id(NEW.key)
                    WHEN NEW.external = 'stratum' THEN ext_stratum_id(NEW.key)
                  END
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


DROP TRIGGER IF EXISTS context_mirror ON context;


CREATE TRIGGER context_mirror AFTER INSERT OR UPDATE OR DELETE ON context
  FOR EACH ROW EXECUTE PROCEDURE context_mirror();
