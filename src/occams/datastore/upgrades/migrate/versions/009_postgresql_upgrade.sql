--
-- Creates a new choice value table AND migrate all the data
--
BEGIN;

CREATE TABLE "value_choice" (
    id integer NOT NULL,
    entity_id integer NOT NULL,
    value integer NOT NULL,
    attribute_id integer NOT NULL,
    create_user_id integer NOT NULL,
    modify_user_id integer NOT NULL,
    modify_date timestamp without time zone DEFAULT now() NOT NULL,
    create_date timestamp without time zone DEFAULT now() NOT NULL,
    revision integer NOT NULL,
    CONSTRAINT ck_value_choice_valid_timeline CHECK ((create_date <= modify_date))
);


CREATE TABLE value_choice_audit (
    id integer NOT NULL,
    entity_id integer NOT NULL,
    value integer NOT NULL,
    attribute_id integer NOT NULL,
    create_user_id integer NOT NULL,
    modify_user_id integer NOT NULL,
    modify_date timestamp without time zone DEFAULT now() NOT NULL,
    create_date timestamp without time zone DEFAULT now() NOT NULL,
    revision integer NOT NULL,
    CONSTRAINT ck_value_choice_valid_timeline CHECK ((create_date <= modify_date))
);

CREATE SEQUENCE value_choice_audit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

ALTER SEQUENCE value_choice_audit_id_seq OWNED BY value_choice_audit.id;

CREATE SEQUENCE value_choice_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

ALTER SEQUENCE value_choice_id_seq OWNED BY "value_choice".id;

ALTER TABLE ONLY "value_choice" ALTER COLUMN id SET DEFAULT nextval('value_choice_id_seq'::regclass);

ALTER TABLE ONLY value_choice_audit ALTER COLUMN id SET DEFAULT nextval('value_choice_audit_id_seq'::regclass);

ALTER TABLE ONLY value_choice_audit
    ADD CONSTRAINT value_choice_audit_pkey PRIMARY KEY (id, revision);

ALTER TABLE ONLY "value_choice"
    ADD CONSTRAINT value_choice_pkey PRIMARY KEY (id);

CREATE INDEX ix_value_choice_attribute_id ON "value_choice" USING btree (attribute_id);

CREATE INDEX ix_value_choice_audit_create_user_id ON value_choice_audit USING btree (create_user_id);

CREATE INDEX ix_value_choice_audit_modify_user_id ON value_choice_audit USING btree (modify_user_id);

CREATE INDEX ix_value_choice_create_user_id ON "value_choice" USING btree (create_user_id);

CREATE INDEX ix_value_choice_entity_id ON "value_choice" USING btree (entity_id);

CREATE INDEX ix_value_choice_modify_user_id ON "value_choice" USING btree (modify_user_id);

CREATE INDEX ix_value_choice_value ON "value_choice" USING btree (value);

ALTER TABLE ONLY "value_choice"
    ADD CONSTRAINT fk_value_choice_attribute_id FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE;

ALTER TABLE ONLY "value_choice"
    ADD CONSTRAINT fk_value_choice_value FOREIGN KEY (value) REFERENCES choice(id) ON DELETE CASCADE;

ALTER TABLE ONLY "value_choice"
    ADD CONSTRAINT fk_value_choice_create_user_id FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT;

ALTER TABLE ONLY "value_choice"
    ADD CONSTRAINT fk_value_choice_entity_id FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE;

ALTER TABLE ONLY "value_choice"
    ADD CONSTRAINT fk_value_choice_modify_user_id FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT;


-- Migrate all the choice selections to the new table


INSERT INTO "value_choice" (entity_id, attribute_id, value, create_date, create_user_id, modify_date, modify_user_id, revision)
  SELECT
    value.entity_id
    ,value.attribute_id
    ,choice.id AS choice_id
    ,value.create_date
    ,value.create_user_id
    ,value.modify_date
    ,value.modify_user_id
    ,value.revision
  FROM "value_decimal" AS "value"
  JOIN "choice"
    ON "choice"."attribute_id" = "value"."attribute_id"
    AND "value"."value"::text = choice.value
  UNION
  SELECT
    value.entity_id
    ,value.attribute_id
    ,choice.id AS choice_id
    ,value.create_date
    ,value.create_user_id
    ,value.modify_date
    ,value.modify_user_id
    ,value.revision
  FROM "value_integer" AS "value"
   JOIN "choice"
    ON "choice"."attribute_id" = "value"."attribute_id"
    AND "value"."value"::text = choice.value
  UNION
  SELECT
    value.entity_id
    ,value.attribute_id
    ,choice.id AS choice_id
    ,value.create_date
    ,value.create_user_id
    ,value.modify_date
    ,value.modify_user_id
    ,value.revision
  FROM "value_string" AS "value"
  JOIN "choice"
    ON "choice"."attribute_id" = "value"."attribute_id"
    AND "value"."value"::text = choice.value
  UNION
  SELECT
    value.entity_id
    ,value.attribute_id
    ,choice.id AS choice_id
    ,value.create_date
    ,value.create_user_id
    ,value.modify_date
    ,value.modify_user_id
    ,value.revision
  FROM "value_datetime" AS "value"
  JOIN "choice"
    ON "choice"."attribute_id" = "value"."attribute_id"
    AND "value"."value"::text = choice.value
;


-- Delete the moved values


DELETE FROM "value_decimal" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_integer" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_string" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_datetime" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_blob" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_text" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;


-- delete the audit values
-- data loss, unfortunately...
-- reason: there will be entries from records that were deleted on the live
-- tables that will be unable to be mapped, rather than retrofitting audit
-- data it's simpler to just purge this set since we don't have a view
-- for it anyway.
DELETE FROM "value_decimal_audit" AS value USING choice_audit AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_integer_audit" AS value USING choice_audit AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_string_audit" AS value USING choice_audit AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_datetime_audit" AS value USING choice_audit AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_blob_audit" AS value USING choice_audit AS choice WHERE value.attribute_id = choice.attribute_id;;
DELETE FROM "value_text_audit" AS value USING choice_audit AS choice WHERE value.attribute_id = choice.attribute_id;;


-- drop the old columns


ALTER TABLE "value_decimal" DROP COLUMN "choice_id";
ALTER TABLE "value_datetime" DROP COLUMN "choice_id";
ALTER TABLE "value_integer" DROP COLUMN "choice_id";
ALTER TABLE "value_string" DROP COLUMN "choice_id";
ALTER TABLE "value_text" DROP COLUMN "choice_id";
ALTER TABLE "value_blob" DROP COLUMN "choice_id";

ALTER TABLE "value_decimal_audit" DROP COLUMN "choice_id";
ALTER TABLE "value_datetime_audit" DROP COLUMN "choice_id";
ALTER TABLE "value_integer_audit" DROP COLUMN "choice_id";
ALTER TABLE "value_string_audit" DROP COLUMN "choice_id";
ALTER TABLE "value_text_audit" DROP COLUMN "choice_id";
ALTER TABLE "value_blob_audit" DROP COLUMN "choice_id";

COMMIT;
