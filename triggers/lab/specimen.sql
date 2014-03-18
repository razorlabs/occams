---
--- avrc_data/specimen -> pirc/specimen
---


CREATE FOREIGN TABLE specimen_ext (
    id                SERIAL NOT NULL

  , specimen_type_id  INTEGER NOT NULL
  , patient_id        INTEGER NOT NULL
  , cycle_id          INTEGER
  , state_id          INTEGER NOT NULL
  , collect_date      DATE
  , collect_time      TIME
  , location_id       INTEGER
  , tubes             INTEGER
  , notes             VARCAHR
  , study_cycle_label VARCHAR

  , create_date       DATETIME NOT NULL
  , create_user_id    INTEGER NOT NULL
  , modify_date       DATETIME NOT NULL
  , modify_user_id    INTEGER NOT NULL
  , revision          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimen');


CREATE OR REPLACE FUNCTION specimen_mirror() RETURNS TRIGGER AS $specimen_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimen_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM specimen_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE specimen_ext;
      WHEN 'UPDATE' THEN
        UPDATE specimen_ext
        SET id = NEW.id
          , specimen_type_id = NEW.specimen_type_id
          , patient_id = NEW.patient_id
          , cycle_id = NEW.cycle_id
          , state_id = NEW.state_id
          , collect_date = NEW.collect_date
          , collect_time = NEW.collect_time
          , location_id = NEW.location_id
          , tubes = NEW.tubes
          , notes = NEW.notes
          , study_cycle_label = NEW.study_cycle_label
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$specimen_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER specimen_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON specimen
  FOR EACH ROW EXECUTE PROCEDURE specimen_mirror();
