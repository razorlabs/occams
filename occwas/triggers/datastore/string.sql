---
--- avrc_data/value_string -> pirc/value_string + pirc/value_choice
---

DROP FOREIGN TABLE IF EXISTS value_string_ext;


CREATE FOREIGN TABLE value_string_ext (
    -- id              INTEGER NOT NULL

  -- , entity_id       INTEGER NOT NULL
    entity_id       INTEGER NOT NULL
  , attribute_id    INTEGER NOT NULL
  , value           VARCHAR NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'value_string');


CREATE OR REPLACE FUNCTION value_string_mirror() RETURNS TRIGGER AS $$
  BEGIN

    -- Only insert not-null values
    -- Also, if updating a previously null value, we need to insert since null
    -- values are not allowed in the external table
    IF     (TG_OP = 'INSERT' AND NEW.value IS NOT NULL)
        OR (TG_OP = 'UPDATE'
              AND OLD.value IS NULL
              AND NEW.value IS NOT NULL
              AND (NEW.choice_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM value_choice_ext WHERE old_db = (SELECT current_database()) AND old_id = OLD.id)
                   OR (NEW.choice_id IS NULL AND NOT EXISTS(SELECT 1 FROM value_string_ext WHERE old_db = (SELECT current_database()) AND old_id = OLD.id))))
        THEN

      -- Determine destination (choice or string)
      IF NEW.choice_id IS NULL THEN
        INSERT INTO value_string_ext (
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
      ELSE
        INSERT INTO value_choice_ext (
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
          , ext_choice_id(NEW.choice_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
          );
      END IF;

    -- Remove null values from new database
    ELSIF  (TG_OP = 'DELETE')
        OR (TG_OP = 'UPDATE' AND NEW.value IS NULL)
        THEN

      -- Delete from both since we can't reliably tell if it was previously
      -- a choice (because of null values)
      DELETE FROM value_string_ext WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;
      DELETE FROM value_choice_ext WHERE old_db = (SELECT current_database()) AND old_id = OLD.id;

    -- Update existing values
    ELSIF (TG_OP = 'UPDATE' AND OLD.value IS NOT NULL AND NEW.value IS NOT NULL) THEN

      -- Determine destination
      IF NEW.choice_id IS NULL THEN
        UPDATE value_string_ext
        SET entity_id = ext_entity_id(NEW.entity_id)
          , attribute_id = ext_attribute_id(NEW.attribute_id)
          , value = NEW.value
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE old_db = (SELECT current_database()) AND old_id = NEW.id;
      ELSE
        UPDATE value_choice_ext
        SET entity_id = ext_entity_id(NEW.entity_id)
          , attribute_id = ext_attribute_id(NEW.attribute_id)
          , value = ext_choice_id(NEW.choice_id)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE old_db = (SELECT current_database()) AND old_id = NEW.id;
      END IF;

    ELSE

      RAISE WARNING 'COULD NOT DETERMINE APPROPRIATE ACTION!!!';

    END IF;

    RETURN NULL;

  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS value_string_mirror ON "string";


CREATE TRIGGER value_string_mirror AFTER INSERT OR UPDATE OR DELETE ON "string"
  FOR EACH ROW EXECUTE PROCEDURE value_string_mirror();
