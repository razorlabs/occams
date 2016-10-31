CREATE OR REPLACE FUNCTION touch() RETURNS TRIGGER AS $$
DECLARE
		_user text;
		_timestamp timestamp;
BEGIN
		_user := (SELECT current_setting('application.user'));
		_timestamp := timeofday();

		IF _user = '' THEN
				RAISE EXCEPTION USING
						MESSAGE = '"application.user" value is not set in transaction',
						HINT = 'SET LOCAL "application.user" = ''username''';
		END IF;

		IF tg_op = 'INSERT' THEN
				NEW.created_by := lower(_user);
				NEW.created_at := _timestamp;
		END IF;

		NEW.modified_by := lower(_user);
		NEW.modified_at := _timestamp;

		RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION touch_table(target_table regclass)
		RETURNS void AS $$
BEGIN
		EXECUTE '
				DROP TRIGGER IF EXISTS touch_trigger ON ' || target_table || ';
				CREATE TRIGGER touch_trigger
				BEFORE INSERT OR UPDATE
				ON ' || target_table || '
				FOR EACH ROW EXECUTE PROCEDURE touch()';
END;
$$ LANGUAGE plpgsql;
