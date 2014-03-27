---
--- avrc_data/arm -> pirc/arm
---

DROP FOREIGN TABLE IF EXISTS arm_ext;


CREATE FOREIGN TABLE arm_ext (
    id              SERIAL NOT NULL

  , name            INTEGER NOT NULL
  , title           INTEGER NOT NULL
  , description     VARCHAR

  , study_id        INTEGER NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'arm');


CREATE OR REPLACE FUNCTION ext_arm_id(id integer) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "arm_ext".id
        FROM "arm_ext"
        WHERE (study_id, name) =
          (SELECT (ext_study_id(study_id), name) FROM "arm" WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION arm_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO arm_ext (
            name
          , title
          , description
          , study_id
          , create_date
          , modify_date
          , create_user_id
          , revision
        )
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , ext_study_id(NEW.study_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          );
      WHEN 'DELETE' THEN
        DELETE FROM arm_ext
        WHERE (study_id, name) = (ext_study_id(OLD.study_id), OLD.name);
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
        WHERE (study_id, name) = (ext_study_id(OLD.study_id), OLD.name);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS arm_mirror ON arm;


CREATE TRIGGER arm_mirror AFTER INSERT OR UPDATE OR DELETE ON arm
  FOR EACH ROW EXECUTE PROCEDURE arm_mirror();
