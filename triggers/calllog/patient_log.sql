---
--- avrc_data/specimen -> pirc/specimen
---


CREATE FOREIGN TABLE specimen_ext (
    id                      INTEGER NOT NULL

  , specimen_id             INTEGER NOT NULL
  , aliquot_type_id         INTEGER NOT NULL
  , state_id                INTEGER NOT NULL
  , labbook                 VARCHAR
  , volume                  FLOAT
  , cell_amount             FLOAT
  , store_date              DATE
  , inventory_date          DATE
  , freezer                 VARCHAR
  , rack                    VARCHAR
  , box                     VARCHAR
  , location_id             INTEGER NOT NULL
  , thawed_num              INTEGER
  , sent_date               DATE
  , sent_name               VARCHAR
  , notes                   VARCHAR
  , special_instruction_id  INTEGER

  , create_date             DATETIME NOT NULL
  , create_user_id          INTEGER NOT NULL
  , modify_date             DATETIME NOT NULL
  , modify_user_id          INTEGER NOT NULL
  , revision                INTEGER NOT NULL
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
          , specimen_id = NEW.specimen_id
          , aliquot_type_id = NEW.aliquot_type_id
          , state_id = NEW.state_id
          , labbook = NEW.labbook
          , volume = NEW.volume
          , cell_amount = NEW.cell_amount
          , store_date = NEW.store_date
          , inventory_date = NEW.inventory_date
          , freezer = NEW.freezer
          , rack = NEW.rack
          , box = NEW.box
          , location_id = NEW.location_id
          , thawed_num = NEW.thawed_num
          , sent_date = NEW.sent_date
          , sent_name = NEW.sent_name
          , notes = NEW.notes
          , special_instruction_id
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$specimen_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER specimen_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON specimen
  FOR EACH ROW EXECUTE PROCEDURE specimen_mirror();
