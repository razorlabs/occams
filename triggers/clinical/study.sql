---
--- avrc_data/study -> pirc/study
---


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

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'study');


CREATE OR REPLACE FUNCTION study_mirror() RETURNS TRIGGER AS $study_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO study_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM study_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE study_ext;
      WHEN 'UPDATE' THEN
        UPDATE study_ext
        SET id = NEW.id
          , zid = NEW.zid
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , short_title = NEW.short_title
          , code = NEW.code
          , consent_date = NEW.cosent_date
          , is_blinded = NEW.is_blinded
          , category_id = NEW.category_id
          , log_category_id = NEW.log_category_id
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$study_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER study_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON study
  kFOR EACH ROW EXECUTE PROCEDURE study_mirror();
