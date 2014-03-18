---
--- avrc_data/cycle -> pirc/cycle
---


CREATE FOREIGN TABLE cycle_ext (
    id              SERIAL NOT NULL

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


CREATE OR REPLACE FUNCTION ext_cycle_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "cycle_ext".id
        FROM "cycle_ext"
        WHERE zid = SELECT zid FROM "cycle" where id = $1;
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION cycle_mirror() RETURNS TRIGGER AS $cycle_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO cycle_ext (
            zid
          , study_id
          , name
          , title
          , description
          , week
          , threshold
          , category_id
          , create_date
          , modify_date
          , create_user_id
          , revision
        )
        VALUES (
            NEW.zid
          , ext_study_id(NEW.study_id)
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.week
          , NEW.threshold
          , ext_category_id(NEW.category_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          );
      WHEN 'DELETE' THEN
        DELETE FROM cycle_ext WHERE zid = OLD.zid;
      WHEN 'TRUNCATE' THEN
        TRUNCATE cycle_ext;
      WHEN 'UPDATE' THEN
        UPDATE cycle_ext
        SET zid = NEW.zid
          , study_id = ext_study_id(NEW.study_id)
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , week = NEW.week
          , threshold = NEW.threshold
          , category_id = NEW.category_id
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE zid = OLD.zid;
    END CASE;
    RETURN NULL;
  END;
$cycle_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER cycle_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON cycle
  FOR EACH ROW EXECUTE PROCEDURE cycle_mirror();
