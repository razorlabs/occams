---
--- avrc_data/specimentype_study -> pirc/specimentype_study
---

DROP FOREIGN TABLE IF EXISTS specimentype_study_ext;


CREATE FOREIGN TABLE specimentype_study_ext (
    study_id        INTEGER NOT NULL
  , specimentype_id  INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimentype_study');


CREATE OR REPLACE FUNCTION specimentype_study_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimentype_study_ext (
            study_id
          , specimentype_id
        )
        VALUES (
            ext_study_id(NEW.study_id)
          , (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimentype_id))
        );
        RETURN NEW;
      WHEN 'DELETE' THEN
        DELETE FROM specimentype_study_ext
        WHERE study_id = (SELECT * FROM ext_study_id(OLD.study_id))
        AND   specimentype_id =  (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), OLD.specimentype_id));
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE specimentype_study_ext
        SET study_id = ext_study_id(NEW.study_id)
          , specimentype_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimentype_id))
        WHERE study_id = (SELECT * FROM ext_study_id(OLD.study_id))
        AND   specimentype_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), OLD.specimentype_id))
        ;
        RETURN NEW;

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS specimentype_study_mirror ON specimentype_study;


CREATE TRIGGER specimentype_study_mirror AFTER INSERT OR UPDATE OR DELETE ON specimentype_study
  FOR EACH ROW EXECUTE PROCEDURE specimentype_study_mirror();
