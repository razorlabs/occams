---
--- avrc_data/specimentype -> pirc/specimentype
---

DROP FOREIGN TABLE IF EXISTS specimentype_ext;


CREATE FOREIGN TABLE specimentype_ext (
    id              INTEGER NOT NULL

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR
  , tube_type       VARCHAR
  , default_tubes   INTEGER

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL

  , old_db          VARCHAR NOT NULL
  , old_id          INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'specimentype');


CREATE OR REPLACE FUNCTION specimentype_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        PERFORM dblink_connect('trigger_target');
        INSERT INTO specimentype_ext (
            id
          , name
          , title
          , description
          , tube_type
          , default_tubes
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , old_db
          , old_id
        )
        VALUES (
            (SELECT val FROM dblink('SELECT nextval(''specimentype_id_seq'') AS val') AS sec(val int))
          , NEW.name
          , NEW.title
          , NEW.description
          , NEW.tube_type
          , NEW.default_tubes
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , (SELECT current_database())
          , NEW.id
        );
        PERFORM dblink_disconnect();
      WHEN 'DELETE' THEN
        DELETE FROM specimentype_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE specimentype_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , tube_type = NEW.tube_type
          , default_tubes = NEW.default_tubes
          , create_date = NEW.create_date
          , create_user_id = ext_user_id(NEW.create_user_id)
          , modify_date = NEW.modify_date
          , modify_user_id = ext_user_id(NEW.modify_user_id)
          , old_db = (SELECT current_database())
          , old_id = NEW.id
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS specimentype_mirror ON specimentype;


CREATE TRIGGER specimentype_mirror AFTER INSERT OR UPDATE OR DELETE ON specimentype
  FOR EACH ROW EXECUTE PROCEDURE specimentype_mirror();
