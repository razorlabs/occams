---
--- avrc_data/aliquot -> pirc/aliquot
---


CREATE FOREIGN TABLE aliquot_ext (
    id                      INTEGER NOT NULL

  , specimen_id             INTEGER NOT NULL
  , aliquot_type_id         INTEGER NOT NULL
  , state_id                INTEGER NOT NULL
  , labbook                 VARCHAR
  , volume                  FLOAT
  , cell_amount             FLOAT
  , store_date              DATE
  , freezer                 VARCHAR
  , rack                    VARCHAR
  , box                     VARCHAR
  , location_id             INTEGER
  , thawed_num              INTEGER
  , inventory_date          DATE
  , sent_date               DATE
  , sent_name               VARCHAR
  , sent_notes              VARCHAR
  , notes                   VARCHAR
  , special_instruction_id  INTEGER
  , previous_location_id    INTEGER

  , create_date             DATETIME NOT NULL
  , create_user_id          INTEGER NOT NULL
  , modify_date             DATETIME NOT NULL
  , modify_user_id          INTEGER NOT NULL
  , revision                INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'aliquot');


CREATE OR REPLACE FUNCTION aliquot_mirror() RETURNS TRIGGER AS $aliquot_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO aliquot_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM aliquot_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE aliquot_ext;
      WHEN 'UPDATE' THEN
        UPDATE aliquot_ext
        SET id = NEW.id
          , specimen_id = NEW.specimen_id
          , aliquot_type_id = NEW.aliquot_type_id
          , state_id = NEW.state_id
          , labbook = NEW.labbook
          , volume = NEW.volume
          , cell_amount = NEW.cell_amount
          , store_date = NEW.store_date
          , freezer = NEW.freezer
          , rack = NEW.rack
          , box = NEW.box
          , location_id = NEW.location_id
          , thawed_num = NEW.thawed_num
          , inventory_date = NEW.inventory_date
          , sent_date = NEW.sent_date
          , sent_name = NEW.sent_name
          , sent_notes = NEW.sent_notes
          , notes = NEW.notes
          , special_instruction_id = NEW.special_instruction_id
          , previous_location_id = NEW.previous_location_id
          , create_date = NEW.create_date = NEW.create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$aliquot_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER aliquot_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON aliquot
  FOR EACH ROW EXECUTE PROCEDURE aliquot_mirror();
