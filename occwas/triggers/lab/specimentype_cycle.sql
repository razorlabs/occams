---
--- avrc_data/specimentype_cycle -> pirc/specimentype_cycle
---


CREATE FOREIGN TABLE specimentype_cycle_ext (
    cycle_id        INTEGER NOT NULL
  , specimentype_id  INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimentype_cycle');


CREATE OR REPLACE FUNCTION specimentype_cycle_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO specimentype_cycle_ext (
            cycle_id
          , specimentype_id
        )
        VALUES (
            ext_cycle_id(NEW.cycle_id)
          , SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimentype_id)
        );

      WHEN 'DELETE' THEN
        DELETE FROM specimentype_cycle_ext
        WHERE cycle_id = ext_cycle_id(OLD.cycle_id)
            , specimentype_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), OLD.specimentype_id))
      WHEN 'TRUNCATE' THEN
        TRUNCATE specimentype_cycle_ext;
      WHEN 'UPDATE' THEN
        UPDATE specimentype_cycle_ext
        SET cycle_id = ext_cycle_id(NEW.cycle_id)
          , specimentype_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimentype_id))
        WHERE cycle_id = ext_cycle_id(OLD.cycle_id)
            , specimentype_id = (SELECT id FROM specimentype_ext WHERE (old_db, old_id) = (SELECT current_database(), OLD.specimentype_id))

    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER specimentype_cycle_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON specimentype_cycle
  FOR EACH ROW EXECUTE PROCEDURE specimentype_cycle_mirror();
