---
--- avrc_data/specimentype_study -> pirc/specimentype_study
---


CREATE FOREIGN TABLE specimentype_study_ext (
    study_id        INTEGER NOT NULL
  , specimentype_id  INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimentype_study');


CREATE OR REPLACE FUNCTION specimentype_study_mirror() RETURNS TRIGGER AS $specimentype_study_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimentype_study_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM specimentype_study_ext
        WHERE study_id = OLD.study_id
            , specimentype_id = OLD.specimentype_id
      WHEN 'TRUNCATE' THEN
        TRUNCATE specimentype_study_ext;
      WHEN 'UPDATE' THEN
        UPDATE specimentype_study_ext
        SET study_id = NEW.study_id
          , specimentype_id = NEW.specimentype_id
        WHERE study_id = OLD.study_id
            , specimentype_id = OLD.specimentype_id

    END CASE;
    RETURN NULL;
  END;
$specimentype_study_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER specimentype_study_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON specimentype_study
  FOR EACH ROW EXECUTE PROCEDURE specimentype_study_mirror();
