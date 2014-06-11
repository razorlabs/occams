---
--- avrc_data/schema_category -> pirc/schema_category
---

DROP FOREIGN TABLE IF EXISTS schema_category_ext;


CREATE FOREIGN TABLE schema_category_ext (
    schema_id INTEGER NOT NULL
  , category_id INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'schema_category');


CREATE OR REPLACE FUNCTION schema_category_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO schema_category_ext (
            schema_id
          , category_id
        )
        VALUES (
            ext_schema_id(NEW.schema_id)
          , ext_category_id(NEW.category_id)
        );
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM schema_category_ext
        WHERE schema_id = (SELECT * FROM ext_schema_id(OLD.schema_id))
          AND category_id = (SELECT * FROM ext_category_id(OLD.category_id))
        ;
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE schema_category_ext
        SET schema_id = ext_schema_id(NEW.schema_id)
          , category_id = ext_category_id(NEW.category_id)
        WHERE schema_id = (SELECT * FROM ext_schema_id(OLD.schema_id))
          AND category_id = (SELECT * FROM ext_category_id(OLD.category_id))
        ;
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS schema_category_mirror ON schema_category;


CREATE TRIGGER schema_category_mirror AFTER INSERT OR UPDATE OR DELETE ON schema_category
  FOR EACH ROW EXECUTE PROCEDURE schema_category_mirror();
