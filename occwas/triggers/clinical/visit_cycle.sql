---
--- avrc_data/visit_cycle -> pirc/visit_cycle
---


CREATE FOREIGN TABLE visit_cycle_ext (
    visit_id        INTEGER NOT NULL
  , cycle_id        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'visit_cycle');


CREATE OR REPLACE FUNCTION visit_cycle_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO visit_cycle_ext VALUES (
            ext_visit_id(NEW.visit_id)
          , ext_cycle_id(NEW.cycle_id)
          );
      WHEN 'DELETE' THEN
        DELETE
        FROM visit_cycle_ext
        WHERE visit_id = ext_visit_id(OLD.visit_id)
          AND cycle_id = ext_cycle_id(OLD.cycle_id);
      WHEN 'TRUNCATE' THEN
        TRUNCATE visit_cycle_ext;
      WHEN 'UPDATE' THEN
        UPDATE visit_cycle_ext
        SET visit_id = ext_visit_id(NEW.visit_id)
          , cycle_id = ext_cycle_id(NEW.cycle_id)
        WHERE visit_id = ext_visit_id(OLD.visit_id)
          AND cycle_id = ext_cycle_id(OLD.cycle_id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER visit_cycle_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON visit_cycle
  FOR EACH ROW EXECUTE PROCEDURE visit_cycle_mirror();
