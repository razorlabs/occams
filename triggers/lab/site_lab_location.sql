---
--- avrc_data/site_lab_location -> pirc/site_lab_location
---


CREATE FOREIGN TABLE site_lab_location_ext (
  site_id     INTEGER NOT NULL
  location_id INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'site_lab_location');


CREATE OR REPLACE FUNCTION site_lab_location_mirror() RETURNS TRIGGER AS $site_lab_location_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO site_lab_location_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM site_lab_location_ext
        WHERE site_id = OLD.site_id
            , location_id = OLD.location_id
      WHEN 'TRUNCATE' THEN
        TRUNCATE site_lab_location_ext;
      WHEN 'UPDATE' THEN
        UPDATE site_lab_location_ext
        SET site_id = NEW.site_id
          , location_id = NEW.location_id
        WHERE site_id = OLD.site_id
            , location_id = OLD.location_id
    END CASE;
    RETURN NULL;
  END;
$site_lab_location_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER site_lab_location_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON site_lab_location
  FOR EACH ROW EXECUTE PROCEDURE site_lab_location_mirror();
