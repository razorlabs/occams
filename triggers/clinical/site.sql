---
--- avrc_data/site -> pirc/site
---


CREATE FOREIGN TABLE site_ext (
    id              INTEGER NOT NULL

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


CREATE OR REPLACE FUNCTION site_mirror() RETURNS TRIGGER AS $site_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO site_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM site_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE site_ext;
      WHEN 'UPDATE' THEN
        UPDATE site_ext
        SET id = NEW.id
          , zid = NEW.zid
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$site_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER site_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON site
  FOR EACH ROW EXECUTE PROCEDURE site_mirror();
