--
-- avrc_data/user -> pirc/user
--
-- Uses ``key`` to find the user in both databases since
-- the was reconciled from two data sources (phi/fia)
--


CREATE FOREIGN TABLE user_ext (
    id              SERIAL NOT NULL

  , key             VARCHAR
  , create_date     TIMESTAMP NOT NULL
  , modify_date     TIMESTAMP NOT NULL
)
SERVER trigger_target
OPTIONS (table_name 'user');


--
-- Helper function to find the user id in the new system using
-- the old system id number
--
CREATE OR REPLACE FUNCTION ext_user_id(id) RETURNS SETOF integer AS $$
  BEGIN
    RETURN QUERY
      SELECT "user_ext".id
      FROM "user_ext"
      WHERE key = (SELECT key FROM "user" WHERE id = $1);
  END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION user_mirror() RETURNS TRIGGER AS $$
  BEGIN
    CASE TG_OP
      WHEN 'INSERT' THEN
        INSERT INTO user_ext
          (key, create_date, modify_date)
        VALUES (NEW.key, NEW.create_date, NEW.modify_date);
      WHEN 'DELETE' THEN
        DELETE FROM user_ext WHERE key = OLD.key;
      WHEN 'TRUNCATE' THEN
        TRUNCATE user_ext;
      WHEN 'UPDATE' THEN
        UPDATE user_ext
        SET key = NEW.key
          , create_date = NEW.create_date
          , modify_date = NEW.modify_date
        WHERE key = OLD.key;
    END CASE;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_mirror AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON user
  FOR EACH ROW EXECUTE PROCEDURE user_mirror();

