---
--- avrc_data/aliquot -> pirc/aliquot
---

DROP FOREIGN TABLE IF EXISTS aliquot_ext;


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

  , create_date             TIMESTAMP NOT NULL
  , create_user_id          INTEGER NOT NULL
  , modify_date             TIMESTAMP NOT NULL
  , modify_user_id          INTEGER NOT NULL
  , revision                INTEGER NOT NULL

  , old_db                  VARCHAR NOT NULL
  , old_id                  INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'aliquot');


CREATE OR REPLACE FUNCTION aliquot_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO aliquot_ext (
            specimen_id
          , aliquot_type_id
          , state_id
          , labbook
          , volume
          , cell_amount
          , store_date
          , freezer
          , rack
          , box
          , location_id
          , thawed_num
          , inventory_date
          , sent_date
          , sent_name
          , sent_notes
          , notes
          , special_instruction_id
          , previous_location_id
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
          , old_db
          , old_id
        )
        VALUES (
            (SELECT id FROM specimen_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimen_id))
          , (SELECT id FROM aliquottype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.aliquot_type_id))
          , (SELECT id FROM aliquotstate_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.state_id))
          , NEW.labbook
          , NEW.volume
          , NEW.cell_amount
          , NEW.store_date
          , NEW.freezer
          , NEW.rack
          , NEW.box
          , (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.location_id))
          , NEW.thawed_num
          , NEW.inventory_date
          , NEW.sent_date
          , NEW.sent_name
          , NEW.sent_notes
          , NEW.notes
          , (SELECT id FROM specialinstruction_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.special_instruction_id))
          , (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.previous_location_id))
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
          , (SELECT current_database())
          , NEW.id
        );

      WHEN 'DELETE' THEN
        DELETE FROM aliquot_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE aliquot_ext
        SET specimen_id = (SELECT id FROM specimen_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.specimen_id))
          , aliquot_type_id = (SELECT id FROM aliquottype_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.aliquot_type_id))
          , state_id = (SELECT id FROM aliquotstate_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.state_id))
          , labbook = NEW.labbook
          , volume = NEW.volume
          , cell_amount = NEW.cell_amount
          , store_date = NEW.store_date
          , freezer = NEW.freezer
          , rack = NEW.rack
          , box = NEW.box
          , location_id = (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.location_id))
          , thawed_num = NEW.thawed_num
          , inventory_date = NEW.inventory_date
          , sent_date = NEW.sent_date
          , sent_name = NEW.sent_name
          , sent_notes = NEW.sent_notes
          , notes = NEW.notes
          , special_instruction_id = (SELECT id FROM specialinstruction_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.special_instruction_id))
          , previous_location_id = (SELECT id FROM location_ext WHERE (old_db, old_id) = (SELECT current_database(), NEW.previous_location_id))
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


DROP TRIGGER IF EXISTS aliquot_mirror ON aliquot;


CREATE TRIGGER aliquot_mirror AFTER INSERT OR UPDATE OR DELETE ON aliquot
  FOR EACH ROW EXECUTE PROCEDURE aliquot_mirror();
