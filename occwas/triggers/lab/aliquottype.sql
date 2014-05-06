---
--- avrc_data/aliquottype -> pirc/aliquottype
---

DROP FOREIGN TABLE IF EXISTS aliquottype_ext;


CREATE FOREIGN TABLE aliquottype_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR
  , specimen_type_id INTEGER

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL

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
          , specimen_type_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , old_db
          , old_id
        )
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimen_type_id))
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
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
          , specimen_type_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimen_type_id))
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS aliquottype_mirror ON aliquottype;


CREATE TRIGGER aliquottype_mirror AFTER INSERT OR UPDATE OR DELETE ON aliquottype
  FOR EACH ROW EXECUTE PROCEDURE aliquottype_mirror();
