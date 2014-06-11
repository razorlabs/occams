---
--- avrc_data/arm -> pirc/arm
---

DROP FOREIGN TABLE IF EXISTS arm_ext;


CREATE FOREIGN TABLE arm_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR

  , study_id        INTEGER NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'arm');

DROP FUNCTION IF EXISTS ext_arm_id(INTEGER);

CREATE OR REPLACE FUNCTION ext_arm_id(id integer) RETURNS integer AS $$
  BEGIN
    RETURN (
      SELECT "arm_ext".id
      FROM "arm_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1));
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION arm_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO arm_ext (
            id
          , name
          , title
          , description
          , study_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            (SELECT val FROM dblink('SELECT nextval(''arm_id_seq'') AS val') AS sec(val int))
          , NEW.name
          , NEW.title
          , NEW.description
          , ext_study_id(NEW.study_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
          );
        PERFORM dblink_disconnect();
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM arm_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE arm_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , study_id = ext_study_id(NEW.study_id)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS arm_mirror ON arm;


CREATE TRIGGER arm_mirror AFTER INSERT OR UPDATE OR DELETE ON arm
  FOR EACH ROW EXECUTE PROCEDURE arm_mirror();
