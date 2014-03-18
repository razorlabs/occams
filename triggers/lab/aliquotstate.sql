---
--- avrc_data/aliquotstate -> pirc/aliquotstate
---


CREATE FOREIGN TABLE aliquotstate_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'aliquotstate');


CREATE OR REPLACE FUNCTION aliquotstate_mirror() RETURNS TRIGGER AS $aliquotstate_mirror$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO aliquotstate_ext SELECT NEW.*;
      WHEN 'DELETE' THEN
        DELETE FROM aliquotstate_ext WHERE id = OLD.id;
      WHEN 'TRUNCATE' THEN
        TRUNCATE aliquotstate_ext;
      WHEN 'UPDATE' THEN
        UPDATE aliquotstate_ext
        SET id = NEW.id
          , name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = NEW.create_user_id
          , modify_date = NEW.modify_date
          , modify_user_id = NEW.modify_user_id
          , revision = NEW.revision
        WHERE id = OLD.id;
    END CASE;
    RETURN NULL;
  END;
$aliquotstate_mirror$ LANGUAGE plpgsql;


CREATE TRIGGER aliquotstate_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON aliquotstate
  FOR EACH ROW EXECUTE PROCEDURE aliquotstate_mirror();
