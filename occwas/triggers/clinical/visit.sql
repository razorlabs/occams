---
--- avrc_data/visit -> pirc/visit
---


CREATE FOREIGN TABLE visit_ext (
    id              INTEGER NOT NULL

  , zid             INTEGER NOT NULL
  , patient_id      INTEGER NOT NULL
  , visit_date      DATE NOT NULL

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'visit');


CREATE OR REPLACE FUNCTION ext_visit_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "visit_ext".id
        FROM "visit_ext"
        WHERE zid = SELECT zid FROM "visit" WHERE id = $1;
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION visit_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO visit (
            zid
          , patient_id
          , visit_date
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
        )
        VALUES (
            NEW.zid
          , ext_patient_id(NEW.patient_id)
          , NEW.visit_date
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
        );
      WHEN 'DELETE' THEN
        DELETE FROM visit_ext WHERE zid = OLD.zid;
      WHEN 'UPDATE' THEN
        UPDATE visit_ext
        SET zid = NEW.zid
          , patient_id = ext_patient_id(NEW.patient_id)
          , visit_date = NEW.visit_date
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


CREATE TRIGGER visit_mirror AFTER INSERT OR UPDATE OR DELETE ON visit
  FOR EACH ROW EXECUTE PROCEDURE visit_mirror();
