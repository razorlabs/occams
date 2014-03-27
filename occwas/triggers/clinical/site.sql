---
--- avrc_data/site -> pirc/site
---

DROP FOREIGN TABLE IF EXISTS site_ext;


CREATE FOREIGN TABLE site_ext (
    id              SERIAL NOT NULL

  , zid             INTEGER NOT NULL
  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'site');


--
-- Helper function to find the site id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_site_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "site_ext".id
        FROM "site_ext"
        WHERE zid = (SELECT zid FROM "site" WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION site_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patient_ext (
            zid
          , name
          , title
          , description
          , create_date
          , modify_date
          , create_user_id
          , revision)
        VALUES (
            NEW.zid
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
        );
      WHEN 'DELETE' THEN
        DELETE FROM site_ext WHERE zid = OLD.zid;
      WHEN 'UPDATE' THEN
        UPDATE site_ext
        SET zid = NEW.zid
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE zid = OLD.zid;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS site_mirror ON site;


CREATE TRIGGER site_mirror AFTER INSERT OR UPDATE OR DELETE ON site
  FOR EACH ROW EXECUTE PROCEDURE site_mirror();
