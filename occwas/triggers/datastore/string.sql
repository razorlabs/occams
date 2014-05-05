---
--- avrc_data/value_string -> pirc/value_string + pirc/value_choice
---

DROP FOREIGN TABLE IF EXISTS value_string_ext;


CREATE FOREIGN TABLE value_string_ext (
    id              INTEGER NOT NULL

  , entity_id       INTEGER NOT NULL
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
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NEW.value IS NOT NULL THEN
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
        END IF;

      WHEN 'DELETE' THEN
        IF OLD.choice_id IS NULL THEN
          DELETE FROM value_string_ext
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        ELSE
          DELETE FROM value_choice_ext
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        END IF;
      WHEN 'UPDATE' THEN

        IF NEW.value IS NOT NULL THEN
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
            WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
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
            WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
          END IF;
        END IF;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS value_string_mirror ON "string";


CREATE TRIGGER value_string_mirror AFTER INSERT OR UPDATE OR DELETE ON "string"
  FOR EACH ROW EXECUTE PROCEDURE value_string_mirror();
