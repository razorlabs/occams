---
--- avrc_data/value_decimal -> pirc/value_decimal
--- Note: decimals do not support choices
---


CREATE FOREIGN TABLE value_decimal_ext (
    id              SERIAL NOT NULL

  , entity_id       INTEGER NOT NULL
  , attribute_id    INTEGER NOT NULL
  , value           NUMERIC NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'value_decimal');


CREATE OR REPLACE FUNCTION value_decimal_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NEW.value IS NOT NULL THEN
          INSERT INTO value_decimal_ext (
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
              ext_user_id(NEW.entity_id)
            , ext_attribute_id(NEW.attribute_id)
            , NEW.value
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            , SELECT current_database()
            , NEW.id
            );
        END IF;

      WHEN 'DELETE' THEN
        DELETE FROM value_decimal_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'TRUNCATE' THEN
        TRUNCATE value_decimal_ext;
      WHEN 'UPDATE' THEN

        IF NEW.value IS NOT NULL THEN
          UPDATE value_decimal_ext
          SET entity_id = ext_entity_id(NEW.entity_id)
            , attribute_id = ext_attribute_id(NEW.attribute_id)
            , value = NEW.value
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
            , old_db = SELECT current_database()
            , old_id = NEW.id
          WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        END IF;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER value_decimal_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON decimal
  FOR EACH ROW EXECUTE PROCEDURE value_decimal_mirror();
