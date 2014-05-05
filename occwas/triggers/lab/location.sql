---
--- avrc_data/location -> pirc/location
---

DROP FOREIGN TABLE IF EXISTS location_ext;


CREATE FOREIGN TABLE location_ext (
    id              INTEGER

  , name            VARCHAR NOT NULL
  , title           VARCHAR NOT NULL
  , description     VARCHAR

  , active         BOOLEAN
  , long_title1    VARCHAR
  , long_title2    VARCHAR
  , address_street VARCHAR
  , address_city   VARCHAR
  , address_state  VARCHAR
  , address_zip    VARCHAR
  , phone_number   VARCHAR
  , fax_number     VARCHAR

  , create_date     TIMESTAMP NOT NULL
  , create_user_id  INTEGER NOT NULL
  , modify_date     TIMESTAMP NOT NULL
  , modify_user_id  INTEGER NOT NULL

  , old_db                  VARCHAR NOT NULL
  , old_id                  INTEGER NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'location');


CREATE OR REPLACE FUNCTION location_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO location_ext (
            name
          , title
          , description
          , active
          , long_title1
          , long_title2
          , address_street
          , address_city
          , address_state
          , address_zip
          , phone_number
          , fax_number
          , create_date
          , create_user_id
          , modify_date
          , modify_user_id
          , old_db
          , old_id
        )
        VALUES (
            NEW.name
          , NEW.title
          , NEW.description
          , NEW.active
          , NEW.long_title1
          , NEW.long_title2
          , NEW.address_street
          , NEW.address_city
          , NEW.address_state
          , NEW.address_zip
          , NEW.phone_number
          , NEW.fax_number
          , NEW.create_date
          , ext_user_id(NEW.create_user_id)
          , NEW.modify_date
          , ext_user_id(NEW.modify_user_id)
          , (SELECT current_database())
          , NEW.id
        );
      WHEN 'DELETE' THEN
        DELETE FROM location_ext
        WHERE (old_db, old_id) = (SELECT current_database(), OLD.id);
      WHEN 'UPDATE' THEN
        UPDATE location_ext
        SET name = NEW.name
          , title = NEW.title
          , description = NEW.description
          , active = NEW.active
          , long_title1 = NEW.long_title1
          , long_title2 = NEW.long_title2
          , address_street = NEW.address_street
          , address_city = NEW.address_city
          , address_state = NEW.address_state
          , address_zip = NEW.address_zip
          , phone_number = NEW.phone_number
          , fax_number = NEW.fax_number
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


DROP TRIGGER IF EXISTS location_mirror ON location;


CREATE TRIGGER location_mirror AFTER INSERT OR UPDATE OR DELETE ON location
  FOR EACH ROW EXECUTE PROCEDURE location_mirror();
