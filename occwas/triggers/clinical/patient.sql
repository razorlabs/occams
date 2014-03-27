---
--- avrc_data/patient -> pirc/patient
---


CREATE FOREIGN TABLE patient_ext (
    id              SERIAL NOT NULL

  , site_id         INTEGER NOT NULL
  , zid             INTEGER NOT NULL
  , nurse           VARCHAR
  , our             VARCHAR NOT NULL
  , legacy_number   VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'patient');


CREATE OR REPLACE FUNCTION ext_patient_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "patient_ext".id
        FROM "patient_ext"
        WHERE zid = SELECT zid FROM "patient" WHERE id = $1;
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION patient_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO patient_ext (
            site_id
          , zid
          , nurse
          , our
          , legacy_number
          , create_date
          , modify_date
          , create_user_id
          , revision
        )
        VALUES (
            ext_site_id(NEW.site_id)
          , NEW.zid
          , NEW.nurse
          , NEW.our
          , NEW.legacy_number
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          );
      WHEN 'DELETE' THEN
        DELETE FROM patient_ext WHERE zid = OLD.zid;
      WHEN 'UPDATE' THEN
        UPDATE patient_ext
        SET site_id = ext_site_id(NEW.site_id)
          , zid = NEW.zid
          , nurse = NEW.nurse
          , our = NEW.our
          , legacy_number = NEW.legacy_number
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


CREATE TRIGGER patient_mirror AFTER INSERT OR UPDATE OR DELETE ON patient
  FOR EACH ROW EXECUTE PROCEDURE patient_mirror();
