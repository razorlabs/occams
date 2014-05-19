---
--- avrc_data/visit -> pirc/visit
---

DROP FOREIGN TABLE IF EXISTS visit_ext;


CREATE FOREIGN TABLE visit_ext (
    id              INTEGER NOT NULL

  , zid             INTEGER NOT NULL
  , patient_id      INTEGER NOT NULL
  , visit_date      DATE NOT NULL

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'visit');


CREATE OR REPLACE FUNCTION ext_visit_id(id INTEGER) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "visit_ext".id
      FROM "visit_ext"
      WHERE (old_db, old_id) = (SELECT current_database(), $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION visit_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO visit_ext (
            id
          , zid
          , patient_id
          , visit_date
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            (SELECT val FROM dblink('SELECT nextval(''visit_id_seq'') AS val') AS sec(val int))
          , NEW.zid
          , ext_patient_id(NEW.patient_id)
          , NEW.visit_date
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );
        PERFORM dblink_disconnect();
      WHEN 'DELETE' THEN
        DELETE FROM visit_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
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
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS visit_mirror ON visit;


CREATE TRIGGER visit_mirror AFTER INSERT OR UPDATE OR DELETE ON visit
  FOR EACH ROW EXECUTE PROCEDURE visit_mirror();
