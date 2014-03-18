---
--- avrc_data/cycle -> pirc/cycle
---


CREATE FOREIGN TABLE cycle_ext (
    id              INTEGER NOT NULL

  , zid             INTEGER NOT NULL
  , study_id        INTEGER NOT NULL
  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     TEXT
  , week            TINYINT
  , threshold       TINYINT
  , category_id     INT

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'cycle');


CREATE OR REPLACE FUNCTION cycle_mirror() RETURNS TRIGGER AS $cycle_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO cycle_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM cycle_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE cycle_ext;
      WHEN 'UPDATE' THEN
        UPDATE cycle_ext
        SET id = NEW.id
          , zid = NEW.zid
          , study_id = NEW.study_id
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , week = NEW.week
          , threshold = NEW.threshold
          , category_id = NEW.category_id
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$cycle_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER cycle_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON cycle
  FOR EACH ROW EXECUTE PROCEDURE cycle_mirror();
