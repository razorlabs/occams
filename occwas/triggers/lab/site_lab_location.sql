---
--- avrc_data/site_lab_location -> pirc/site_lab_location
---

DROP FOREIGN TABLE IF EXISTS site_lab_location_ext;


CREATE FOREIGN TABLE site_lab_location_ext (
    site_id     INTEGER NOT NULL
  , location_id INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'site_lab_location');


CREATE OR REPLACE FUNCTION site_lab_location_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO site_lab_location_ext (
            site_id
          , location_id
        )
        VALUES (
            (SELECT id FROM site_ext WHERE zid = (SELECT zid FROM site WHERE id = NEW.site_id))
          , (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.location_id))
        );
      WHEN 'DELETE' THEN
        DELETE FROM site_lab_location_ext
        WHERE site_id = (SELECT id FROM site_ext WHERE zid = (SELECT zid FROM site WHERE id = OLD.site_id))
        AND   location_id = (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), OLD.location_id))
        ;
      WHEN 'UPDATE' THEN
        UPDATE site_lab_location_ext
        SET site_id = (SELECT id FROM site_ext WHERE zid = (SELECT zid FROM site WHERE id = NEW.site_id))
          , location_id = (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.location_id))
        WHERE site_id = (SELECT id FROM site_ext WHERE zid = (SELECT zid FROM site WHERE id = OLD.site_id))
        AND   location_id = (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), OLD.location_id))
        ;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS site_lab_location_mirror ON site_lab_location;


CREATE TRIGGER site_lab_location_mirror AFTER INSERT OR UPDATE OR DELETE ON site_lab_location
  FOR EACH ROW EXECUTE PROCEDURE site_lab_location_mirror();
