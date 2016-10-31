--
-- Missing hstore-equivanentJSON operators
--
-- Code orginally from the following blog post:
--
--    http://schinckel.net/2014/09/29/adding-json%28b%29-operators-to-postgresql/
--

--
-- Implments "JSONB - keys[]", returns a JSONB document with the keys removed
--
-- param 0: JSONB, source JSONB document to remove keys from
-- param 1: text[], keys to remove from the JSONB document
--
CREATE OR REPLACE FUNCTION "jsonb_minus"(
  "json" jsonb,
  "keys" TEXT[]
)
  RETURNS jsonb
  LANGUAGE sql
  IMMUTABLE
  STRICT
AS $function$
  SELECT
    -- Only executes opration if the JSON document has the keys
    CASE WHEN "json" ?| "keys"
      THEN COALESCE(
          (SELECT ('{' || string_agg(to_json("key")::text || ':' || "value", ',') || '}')
           FROM jsonb_each("json")
           WHERE "key" <> ALL ("keys")),
          '{}'
        )::jsonb
      ELSE "json"
    END
$function$;

CREATE OPERATOR - (
  LEFTARG = jsonb,
  RIGHTARG = text[],
  PROCEDURE = jsonb_minus
);

--
-- Implments "JSONB - JSONB", returns a recursive diff of the JSON documents
--
-- http://coussej.github.io/2016/05/24/A-Minus-Operator-For-PostgreSQLs-JSONB/
--
-- param 0: JSONB, primary JSONB source document to compare
-- param 1: JSONB, secondary JSONB source document to compare
--
CREATE OR REPLACE FUNCTION jsonb_minus ( arg1 jsonb, arg2 jsonb )
RETURNS jsonb
AS $$

	SELECT
			COALESCE(
				json_object_agg(
					key,
					CASE
							-- if the value is an object and the value of the second argument is
							-- not null, we do a recursion
							WHEN jsonb_typeof(value) = 'object' AND arg2 -> key IS NOT NULL
							THEN jsonb_minus(value, arg2 -> key)
							-- for all the other types, we just return the value
							ELSE value
					END
				),
        '{}'
      )::jsonb
	FROM
			jsonb_each(arg1)
	WHERE
			arg1 -> key <> arg2 -> key
			OR arg2 -> key IS NULL

$$ LANGUAGE SQL;


CREATE OPERATOR - (
  LEFTARG = jsonb,
  RIGHTARG = jsonb,
  PROCEDURE = jsonb_minus
);
