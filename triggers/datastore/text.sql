---
--- avrc_data/value_text -> pirc/value_text
--- Note: text value types do not support collections or choices, assume single value
---


CREATE FOREIGN TABLE value_text_ext (
    id              SERIAL NOT NULL

  , entity_id       INTEGER NOT NULL
  , attribute_id    INTEGER NOT NULL
  , value           TEXT NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'value_text');


--
-- Helper function to find the value_text id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_value_text_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT id
        FROM "value_text_ext"
        -- Asumming single value...
        WHERE (entity_id, attribute_id) = (
          SELECT ext_entity_id(entity_id)
                ,ext_attribute_id(attribute_id)
          FROM "text"
          WHERE id = $1)
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION value_text_mirror() RETURNS TRIGGER AS $value_text_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN

        IF NEW.value IS NOT NULL THEN
          INSERT INTO value_text_ext (
              entity_id
            , attribute_id
            , value
            , create_date
            , create_user_id
            , modify_date
            , modify_user_id
            , revision)
          VALUES (
              ext_user_id(NEW.entity_id)
            , ext_attribute_id(NEW.attribute_id)
            , NEW.value
            , NEW.create_date
            , ext_user_id(NEW.create_user_id)
            , NEW.modify_date
            , ext_user_id(NEW.modify_user_id)
            , NEW.revision
            );
        END IF;

      WHEN 'DELETE' THEN
        DELETE FROM value_text_ext WHERE id = ext_value_text_id(OLD.id);
      WHEN 'TRUNCATE' THEN
        TRUNCATE value_text_ext;
      WHEN 'UPDATE' THEN

        IF NEW.value IS NOT NULL THEN
          UPDATE value_text_ext
          SET entity_id = ext_entity_id(NEW.entity_id)
            , attribute_id = ext_attribute_id(NEW.attribute_id)
            , value = NEW.value
            , create_date = NEW.create_date
            , create_user_id = ext_user_id(NEW.create_user_id)
            , modify_date = NEW.modify_date
            , modify_user_id = ext_user_id(NEW.modify_user_id)
            , revision = NEW.revision
          WHERE id = ext_value_text_id(OLD.id)
        END IF;

    END CASE;
    RETURN NULL;
  END;
$value_text_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER value_text_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON value_text
  FOR EACH ROW EXECUTE PROCEDURE value_text_mirror();
