---
--- avrc_data/aliquottype -> pirc/aliquottype
---

DROP FOREIGN TABLE IF EXISTS aliquottype_ext;


CREATE FOREIGN TABLE aliquottype_ext (
    id              SERIAL NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR
  , specimentype_id INTEGER
  , location_id     INTEGER

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'aliquottype');


CREATE OR REPLACE FUNCTION aliquottype_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO aliquottype_ext (
            name
          , title
          , description
          , specimentype_id
          , location_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , NEW.specimentype_id
          , NEW.location_id
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM aliquottype_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE aliquottype_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , specimentype_id = NEW.specimentype_id
          , location_id = NEW.location_id
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


DROP TRIGGER IF EXISTS alquottype_mirror ON aliquottype;


CREATE TRIGGER aliquottype_mirror AFTER INSERT OR UPDATE OR DELETE ON aliquottype
  FOR EACH ROW EXECUTE PROCEDURE aliquottype_mirror();
