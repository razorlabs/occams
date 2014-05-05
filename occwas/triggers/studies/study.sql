---
--- avrc_data/study -> pirc/study
---


DROP FOREIGN TABLE IF EXISTS study_ext;


CREATE FOREIGN TABLE study_ext (
    id              INTEGER NOT NULL

  , zid             INTEGER NOT NULL
  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR
  , short_title     VARCHAR NOT NULL
  , code            VARCHAR NOT NULL
  , consent_date    VARCHAR NOT NULL
  , is_blinded      BOOLEAN NOT NULL
  , category_id     INTEGER
  , log_category_id INTEGER

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'study');


CREATE OR REPLACE FUNCTION ext_study_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "study_ext".id
      FROM "study_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION study_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO study_ext (
            zid
          , name
          , title
          , description
          , short_title
          , code
          , consent_date
          , is_blinded
          , category_id
          , log_category_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            NEW.zid
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.short_title
          , NEW.code
          , NEW.consent_date
          , NEW.is_blinded
          , ext_category_id(NEW.category_id)
          , ext_category_id(NEW.log_category_id)
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM study_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE study_ext
        SET zid = NEW.zid
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , short_title = NEW.short_title
          , code = NEW.code
          , consent_date = NEW.consent_date
          , is_blinded = NEW.is_blinded
          , category_id = ext_category_id(NEW.category_id)
          , log_category_id = ext_category_id(NEW.log_category_id)
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS study_mirror ON study;


CREATE TRIGGER study_mirror AFTER INSERT OR UPDATE OR DELETE ON study
  FOR EACH ROW EXECUTE PROCEDURE study_mirror();
