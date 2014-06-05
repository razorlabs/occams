---
--- avrc_data/value_blob -> pirc/value_blob
--- Note: blobs do not support choices
---

DROP FOREIGN TABLE IF EXISTS value_blob_ext;


CREATE FOREIGN TABLE value_blob_ext (
    -- id              INTEGER NOT NULL

  -- , entity_id       INTEGER NOT NULL
    entity_id       INTEGER NOT NULL
  , attribute_id    INTEGER NOT NULL
  , value           BYTEA NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'value_blob');


CREATE OR REPLACE FUNCTION value_blob_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        IF NEW.value IS NOT NULL THEN
          INSERT INTO value_blob_ext (
              entity_id
            , attribute_id
            , value
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
            , ext_attribute_id(NEW.attribute_id)
            , NEW.value
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            , (SELECT current_database())
            , NEW.id
            );
          RETURN NEW;
        END IF;
      WHEN 'DELETE' THEN
        DELETE FROM value_blob_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN OLD;
      WHEN 'UPDATE' THEN

        IF NEW.value IS NOT NULL THEN
          UPDATE value_blob_ext
          SET entity_id = ext_entity_id(NEW.entity_id)
            , attribute_id = ext_attribute_id(NEW.attribute_id)
            , value = NEW.value
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
            , old_db = (SELECT current_database())
            , old_id = NEW.id
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
          RETURN NEW;
        END IF;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS value_blob_mirror ON "blob";


CREATE TRIGGER value_blob_mirror AFTER INSERT OR UPDATE OR DELETE ON blob
  FOR EACH ROW EXECUTE PROCEDURE value_blob_mirror();
