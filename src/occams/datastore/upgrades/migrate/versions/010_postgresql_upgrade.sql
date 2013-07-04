--
-- Flattens entities by removing sub-objects
-- Moving forward 'fieldsets' are purely cosmetic and supported via the
-- section table
-- WARNING: this process will remove any orphaned subforms instances
--
BEGIN;

--
-- Add the new section table
--

CREATE TABLE section (
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description VARCHAR,
    schema_id INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    create_user_id INTEGER NOT NULL,
    modify_user_id INTEGER NOT NULL,
    modify_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    create_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    revision INTEGER NOT NULL,
    CONSTRAINT ck_section_valid_timeline CHECK ((create_date <= modify_date))
);

CREATE TABLE section_audit (
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description VARCHAR,
    schema_id INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    create_user_id INTEGER NOT NULL,
    modify_user_id INTEGER NOT NULL,
    modify_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    create_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    revision INTEGER NOT NULL,
    CONSTRAINT ck_section_valid_timeline CHECK ((create_date <= modify_date))
);

CREATE SEQUENCE section_audit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

ALTER SEQUENCE section_audit_id_seq OWNED BY section_audit.id;

CREATE SEQUENCE section_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

ALTER SEQUENCE section_id_seq OWNED BY section.id;

ALTER TABLE ONLY section ALTER COLUMN id SET DEFAULT nextval('section_id_seq'::regclass);

ALTER TABLE ONLY section_audit ALTER COLUMN id SET DEFAULT nextval('section_audit_id_seq'::regclass);

ALTER TABLE ONLY section_audit
    ADD CONSTRAINT section_audit_pkey PRIMARY KEY (id, revision);

ALTER TABLE ONLY section
    ADD CONSTRAINT section_pkey PRIMARY KEY (id);

ALTER TABLE ONLY section
    ADD CONSTRAINT uq_section_name UNIQUE (schema_id, name);

ALTER TABLE ONLY section
    ADD CONSTRAINT uq_section_order UNIQUE (schema_id, "order");

CREATE INDEX ix_section_audit_create_user_id ON section_audit USING btree (create_user_id);

CREATE INDEX ix_section_audit_modify_user_id ON section_audit USING btree (modify_user_id);

CREATE INDEX ix_section_create_user_id ON section USING btree (create_user_id);

CREATE INDEX ix_section_modify_user_id ON section USING btree (modify_user_id);

ALTER TABLE ONLY section
    ADD CONSTRAINT fk_section_schema_id FOREIGN KEY (schema_id) REFERENCES schema(id) ON DELETE CASCADE;

ALTER TABLE ONLY section
    ADD CONSTRAINT fk_section_create_user_id FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT;

ALTER TABLE ONLY section
    ADD CONSTRAINT fk_section_modify_user_id FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT;

--
-- Add a reference to the setion table in attribute
--

ALTER TABLE attribute
  ADD COLUMN section_id INTEGER
  ,DROP CONSTRAINT uq_attribute_order
  ,ADD CONSTRAINT uq_attribute_order UNIQUE (section_id, "order")
;
ALTER TABLE attribute_audit ADD COLUMN section_id INTEGER;

CREATE INDEX ix_attribute_section_id ON attribute(section_id);

ALTER TABLE attribute
  ADD CONSTRAINT fk_attribute_section_id FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE CASCADE;

--
-- Move object attributes to sections
--

-- Schemata with sub objects
INSERT INTO section (schema_id, name, title, description, "order", create_user_id, modify_user_id, revision)
  SELECT
    schema_id
    ,name
    ,title
    ,description
    -- avoid collisions by using a larger order number
    ,100 + "order"
    ,(SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
    ,(SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
    ,1
  FROM attribute
  WHERE type = 'object'
;

-- Move all sub-attributes to the parent, prepending the parent's name
UPDATE attribute
SET
  schema_id = parent.schema_id
  ,name = parent.name || '_' || attribute.name
  ,section_id = section.id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM
  attribute AS parent
  ,section
WHERE
  parent.object_schema_id = attribute.schema_id
  AND parent.schema_id = section.schema_id
  AND parent.name = section.name
  ;

---- Create a default section for any top-level non-object attributes
---- NOTE: that some schemata contain a combination of both,
INSERT INTO section (schema_id, name, title, "order", create_user_id, modify_user_id, revision)
  SELECT DISTINCT
    schema_id
    ,'default'
    ,'Default'
    ,0
    ,(SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
    ,(SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
    ,1
  FROM
    attribute
    , schema
  WHERE
    schema.id = attribute.schema_id
    AND NOT schema.is_inline
    AND section_id IS NULL
    AND "type" != 'object'
;

-- Finally, attach the non-sectioned scalars
UPDATE attribute
SET
  section_id = section.id
FROM
  section
WHERE
  section.schema_id = attribute.schema_id
  AND section.name = 'default'
  AND section_id IS NULL
  AND "type" != 'object'
;

--
-- Move entity instances
--

UPDATE "value_decimal" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

UPDATE "value_datetime" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

UPDATE "value_integer" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

UPDATE "value_string" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

UPDATE "value_text" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

UPDATE "value_blob" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

UPDATE "value_choice" AS "value"
SET
  entity_id = object.entity_id
  ,modify_user_id = (SELECT id FROM "user" WHERE key = 'bitcore@ucsd.edu')
  ,modify_date = NOW()
FROM object
WHERE value.entity_id = object.value
;

-- Disable because it gets in the way
ALTER TABLE attribute DROP CONSTRAINT "ck_attribute_valid_object_bind";

-- Delete sub-schemata
DELETE
FROM schema
USING attribute
WHERE schema.id = attribute.object_schema_id
OR schema.is_inline
;

-- Delete all object-atributes
DELETE FROM attribute WHERE type = 'object';
DELETE FROM attribute_audit WHERE type = 'object';

DROP TABLE object;
DROP TABLE object_audit;

--
-- Lock the section_id column
--

-- Delete unmatched attributes, these are likely orphans
-- (sub attrinbtes with no parent attribtues
DELETE FROM attribute WHERE section_id IS NULL;

-- Finally lock it
ALTER TABLE attribute ALTER COLUMN section_id SET NOT NULL
;

--
-- No longer support sub objects
--

ALTER TABLE schema
  DROP COLUMN base_schema_id
  ,DROP COLUMN is_inline
  ;

ALTER TABLE schema_audit
  DROP COLUMN base_schema_id
  ,DROP COLUMN is_inline
  ;

ALTER TABLE "attribute" DROP COLUMN "object_schema_id";
ALTER TABLE "attribute_audit" DROP COLUMN "object_schema_id";

--
-- Remove "object" as a selectable type
--

-- Backup the old ENUM
ALTER TYPE "attribute_type" RENAME TO "attribute_type_old";

-- Declare the new ENUM
CREATE TYPE "attribute_type" AS ENUM ( 'blob', 'boolean', 'choice', 'date', 'datetime', 'decimal', 'integer', 'string', 'text');

-- Drop references to the ENUM
ALTER TABLE "attribute"
  ALTER COLUMN "type" TYPE "attribute_type" USING "type"::text::"attribute_type";
;

-- Replace the type (also in the audit table)
ALTER TABLE "attribute_audit"
  ALTER COLUMN "type" TYPE "attribute_type" USING "type"::text::"attribute_type"
;

-- Delete the old ENUM
DROP TYPE "attribute_type_old";

COMMIT;
