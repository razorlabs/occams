---
--- avrc_data/specimen -> pirc/specimen
---

DROP FOREIGN TABLE IF EXISTS specimen_ext;


CREATE FOREIGN TABLE specimen_ext (
    id                INTEGER NOT NULL

  , specimen_type_id  INTEGER NOT NULL
  , patient_id        INTEGER NOT NULL
  , cycle_id          INTEGER
  , state_id          INTEGER NOT NULL
  , collect_date      DATE
  , collect_time      TIME
  , location_id       INTEGER
  , tubes             INTEGER
  , notes             VARCHAR

  , create_date       TIMESTAMP NOT NULL
  , create_user_id    INTEGER NOT NULL
  , modify_date       TIMESTAMP NOT NULL
  , modify_user_id    INTEGER NOT NULL
  , revision          INTEGER NOT NULL

  , old_db            VARCHAR NOT NULL
  , old_id            INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimen');


CREATE OR REPLACE FUNCTION specimen_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO specimen_ext (
            id
          , specimen_type_id
          , patient_id
          , cycle_id
          , state_id
          , collect_date
          , collect_time
          , location_id
          , tubes
          , notes
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            (SELECT val FROM dblink('SELECT nextval(''specimen_id_seq'') AS val') AS sec(val int))
          , (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimen_type_id))
          , ext_patient_id(NEW.patient_id)
          , ext_cycle_id(NEW.cycle_id)
          , (SELECT id FROM specimenstate_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.state_id))
          , NEW.collect_date
          , NEW.collect_time
          , (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.location_id))
          , NEW.tubes
          , NEW.notes
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
        DELETE FROM specimen_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN OLD;
      WHEN 'UPDATE' THEN
        UPDATE specimen_ext
        SET specimen_type_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimen_type_id))
          , patient_id = ext_patient_id(NEW.patient_id)
          , cycle_id = ext_cycle_id(NEW.cycle_id)
          , state_id = (SELECT id FROM specimenstate_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.state_id))
          , collect_date = NEW.collect_date
          , collect_time = NEW.collect_time
          , location_id = (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.location_id))
          , tubes = NEW.tubes
          , notes = NEW.notes
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
        RETURN NEW;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS specimen_mirror ON specimen;


CREATE TRIGGER specimen_mirror AFTER INSERT OR UPDATE OR DELETE ON specimen
  FOR EACH ROW EXECUTE PROCEDURE specimen_mirror();
