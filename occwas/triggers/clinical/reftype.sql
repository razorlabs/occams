---
--- avrc_data/reftype -> pirc/patient
---


CREATE FOREIGN TABLE reftype_ext (
    id              SERIAL NOT NULL

  , name            INTEGER NOT NULL
  , title           INTEGER NOT NULL
  , description     VARCHAR

  , create_date     DATETIME NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     DATETIME NOT NULL
  , modify_user_id  INTEGER NOT NULL
  , revision        INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'reftype');


CREATE OR REPLACE FUNCTION ext_reftype_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
        SELECT "reftype_ext".id
        FROM "retype_ext"
        WHERE name = SELECT name FROM "reftype" WHERE id = $1;
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION reftype_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO reftype_ext (
            name
          , title
          , description
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , revision
        )
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , NEW.revision
        );
      WHEN 'DELETE' THEN
        DELETE FROM reftype_ext WHERE name = OLD.name;
      WHEN 'UPDATE' THEN
        UPDATE reftype_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , revision = NEW.revision
        WHERE name = OLD.name;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER reftype_mirror AFTER INSERT OR UPDATE OR DELETE ON patient
  FOR EACH ROW EXECUTE PROCEDURE reftype_mirror();
