--
-- Renames value tables to make them easier to locate
--
BEGIN;


-- Remove nulled entries


DELETE FROM "decimal" AS v WHERE v.value IS NULL;
DELETE FROM "integer" AS v WHERE v.value IS NULL;
DELETE FROM "string" AS v WHERE v.value IS NULL;
DELETE FROM "datetime" AS v WHERE v.value IS NULL;
DELETE FROM "text" AS v WHERE v.value IS NULL;
DELETE FROM "blob" AS v WHERE v.value IS NULL;

DELETE FROM "decimal_audit" AS v WHERE v.value IS NULL;
DELETE FROM "integer_audit" AS v WHERE v.value IS NULL;
DELETE FROM "string_audit" AS v WHERE v.value IS NULL;
DELETE FROM "datetime_audit" AS v WHERE v.value IS NULL;
DELETE FROM "text_audit" AS v WHERE v.value IS NULL;
DELETE FROM "blob_audit" AS v WHERE v.value IS NULL;


ALTER TABLE "decimal" RENAME TO "value_decimal";
ALTER TABLE "value_decimal"
  DROP CONSTRAINT "fk_decimal_entity_id"
  ,DROP CONSTRAINT "fk_decimal_attribute_id"
  ,DROP CONSTRAINT "fk_decimal_choice_id"
  ,DROP CONSTRAINT "fk_decimal_create_user_id"
  ,DROP CONSTRAINT "fk_decimal_modify_user_id"
  ,DROP CONSTRAINT "ck_decimal_valid_timeline"
  ,ADD CONSTRAINT "fk_value_decimal_entity_id" FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_decimal_attribute_id" FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_decimal_choice_id" FOREIGN KEY (choice_id) REFERENCES choice(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_decimal_create_user_id" FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "fk_value_decimal_modify_user_id" FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "ck_value_decimal_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "decimal_id_seq"  RENAME TO "value_decimal_id_seq";
ALTER INDEX "ix_decimal_entity_id" RENAME TO "ix_value_decimal_entity_id";
ALTER INDEX "ix_decimal_attribute_id" RENAME TO "ix_value_decimal_attribute_id";
ALTER INDEX "ix_decimal_choice_id" RENAME TO "ix_value_decimal_choice_id";
ALTER INDEX "ix_decimal_value" RENAME TO "ix_value_decimal_value";
ALTER INDEX "ix_decimal_create_user_id" RENAME TO "ix_value_decimal_create_user_id";
ALTER INDEX "ix_decimal_modify_user_id" RENAME TO "ix_value_decimal_modify_user_id";


ALTER TABLE "decimal_audit" RENAME TO "value_decimal_audit";
ALTER TABLE "value_decimal_audit"
  DROP CONSTRAINT "ck_decimal_valid_timeline"
  ,ADD CONSTRAINT "ck_value_decimal_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "decimal_audit_id_seq"  RENAME TO "value_decimal_audit_id_seq";
ALTER INDEX "ix_decimal_audit_create_user_id" RENAME TO "ix_value_decimal_audit_create_user_id";
ALTER INDEX "ix_decimal_audit_modify_user_id" RENAME TO "ix_value_decimal_audit_modify_user_id";


ALTER TABLE "datetime" RENAME TO "value_datetime";
ALTER TABLE "value_datetime"
  DROP CONSTRAINT "fk_datetime_entity_id"
  ,DROP CONSTRAINT "fk_datetime_attribute_id"
  ,DROP CONSTRAINT "fk_datetime_choice_id"
  ,DROP CONSTRAINT "fk_datetime_create_user_id"
  ,DROP CONSTRAINT "fk_datetime_modify_user_id"
  ,DROP CONSTRAINT "ck_datetime_valid_timeline"
  ,ADD CONSTRAINT "fk_value_datetime_entity_id" FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_datetime_attribute_id" FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_datetime_choice_id" FOREIGN KEY (choice_id) REFERENCES choice(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_datetime_create_user_id" FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "fk_value_datetime_modify_user_id" FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "ck_value_datetime_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "datetime_id_seq"  RENAME TO "value_datetime_id_seq";
ALTER INDEX "ix_datetime_entity_id" RENAME TO "ix_value_datetime_entity_id";
ALTER INDEX "ix_datetime_attribute_id" RENAME TO "ix_value_datetime_attribute_id";
ALTER INDEX "ix_datetime_choice_id" RENAME TO "ix_value_datetime_choice_id";
ALTER INDEX "ix_datetime_value" RENAME TO "ix_value_datetime_value";
ALTER INDEX "ix_datetime_create_user_id" RENAME TO "ix_value_datetime_create_user_id";
ALTER INDEX "ix_datetime_modify_user_id" RENAME TO "ix_value_datetime_modify_user_id";


ALTER TABLE "datetime_audit" RENAME TO "value_datetime_audit";
ALTER TABLE "value_datetime_audit"
  DROP CONSTRAINT "ck_datetime_valid_timeline"
  ,ADD CONSTRAINT "ck_value_datetime_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "datetime_audit_id_seq"  RENAME TO "value_datetime_audit_id_seq";
ALTER INDEX "ix_datetime_audit_create_user_id" RENAME TO "ix_value_datetime_audit_create_user_id";
ALTER INDEX "ix_datetime_audit_modify_user_id" RENAME TO "ix_value_datetime_audit_modify_user_id";


ALTER TABLE "integer" RENAME TO "value_integer";
ALTER TABLE "value_integer"
  DROP CONSTRAINT "fk_integer_entity_id"
  ,DROP CONSTRAINT "fk_integer_attribute_id"
  ,DROP CONSTRAINT "fk_integer_choice_id"
  ,DROP CONSTRAINT "fk_integer_create_user_id"
  ,DROP CONSTRAINT "fk_integer_modify_user_id"
  ,DROP CONSTRAINT "ck_integer_valid_timeline"
  ,ADD CONSTRAINT "fk_value_integer_entity_id" FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_integer_attribute_id" FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_integer_choice_id" FOREIGN KEY (choice_id) REFERENCES choice(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_integer_create_user_id" FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "fk_value_integer_modify_user_id" FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "ck_value_integer_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "integer_id_seq"  RENAME TO "value_integer_id_seq";
ALTER INDEX "ix_integer_entity_id" RENAME TO "ix_value_integer_entity_id";
ALTER INDEX "ix_integer_attribute_id" RENAME TO "ix_value_integer_attribute_id";
ALTER INDEX "ix_integer_choice_id" RENAME TO "ix_value_integer_choice_id";
ALTER INDEX "ix_integer_value" RENAME TO "ix_value_integer_value";
ALTER INDEX "ix_integer_create_user_id" RENAME TO "ix_value_integer_create_user_id";
ALTER INDEX "ix_integer_modify_user_id" RENAME TO "ix_value_integer_modify_user_id";


ALTER TABLE "integer_audit" RENAME TO "value_integer_audit";
ALTER TABLE "value_integer_audit"
  DROP CONSTRAINT "ck_integer_valid_timeline"
  ,ADD CONSTRAINT "ck_value_integer_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "integer_audit_id_seq"  RENAME TO "value_integer_audit_id_seq";
ALTER INDEX "ix_integer_audit_create_user_id" RENAME TO "ix_value_integer_audit_create_user_id";
ALTER INDEX "ix_integer_audit_modify_user_id" RENAME TO "ix_value_integer_audit_modify_user_id";


ALTER TABLE "string" RENAME TO "value_string";
ALTER TABLE "value_string"
  DROP CONSTRAINT "fk_string_entity_id"
  ,DROP CONSTRAINT "fk_string_attribute_id"
  ,DROP CONSTRAINT "fk_string_choice_id"
  ,DROP CONSTRAINT "fk_string_create_user_id"
  ,DROP CONSTRAINT "fk_string_modify_user_id"
  ,DROP CONSTRAINT "ck_string_valid_timeline"
  ,ADD CONSTRAINT "fk_value_string_entity_id" FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_string_attribute_id" FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_string_choice_id" FOREIGN KEY (choice_id) REFERENCES choice(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_string_create_user_id" FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "fk_value_string_modify_user_id" FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "ck_value_string_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "string_id_seq"  RENAME TO "value_string_id_seq";
ALTER INDEX "ix_string_entity_id" RENAME TO "ix_value_string_entity_id";
ALTER INDEX "ix_string_attribute_id" RENAME TO "ix_value_string_attribute_id";
ALTER INDEX "ix_string_choice_id" RENAME TO "ix_value_string_choice_id";
ALTER INDEX "ix_string_value" RENAME TO "ix_value_string_value";
ALTER INDEX "ix_string_create_user_id" RENAME TO "ix_value_string_create_user_id";
ALTER INDEX "ix_string_modify_user_id" RENAME TO "ix_value_string_modify_user_id";


ALTER TABLE "string_audit" RENAME TO "value_string_audit";
ALTER TABLE "value_string_audit"
  DROP CONSTRAINT "ck_string_valid_timeline"
  ,ADD CONSTRAINT "ck_value_string_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "string_audit_id_seq"  RENAME TO "value_string_audit_id_seq";
ALTER INDEX "ix_string_audit_create_user_id" RENAME TO "ix_value_string_audit_create_user_id";
ALTER INDEX "ix_string_audit_modify_user_id" RENAME TO "ix_value_string_audit_modify_user_id";


ALTER TABLE "blob" RENAME TO "value_blob";
ALTER TABLE "value_blob"
  DROP CONSTRAINT "fk_blob_entity_id"
  ,DROP CONSTRAINT "fk_blob_attribute_id"
  ,DROP CONSTRAINT "fk_blob_choice_id"
  ,DROP CONSTRAINT "fk_blob_create_user_id"
  ,DROP CONSTRAINT "fk_blob_modify_user_id"
  ,DROP CONSTRAINT "ck_blob_valid_timeline"
  ,ADD CONSTRAINT "fk_value_blob_entity_id" FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_blob_attribute_id" FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_blob_choice_id" FOREIGN KEY (choice_id) REFERENCES choice(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_blob_create_user_id" FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "fk_value_blob_modify_user_id" FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "ck_value_blob_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "blob_id_seq"  RENAME TO "value_blob_id_seq";
ALTER INDEX "ix_blob_entity_id" RENAME TO "ix_value_blob_entity_id";
ALTER INDEX "ix_blob_attribute_id" RENAME TO "ix_value_blob_attribute_id";
ALTER INDEX "ix_blob_choice_id" RENAME TO "ix_value_blob_choice_id";
--ALTER INDEX "ix_blob_value" RENAME TO "ix_value_blob_value";
ALTER INDEX "ix_blob_create_user_id" RENAME TO "ix_value_blob_create_user_id";
ALTER INDEX "ix_blob_modify_user_id" RENAME TO "ix_value_blob_modify_user_id";


ALTER TABLE "blob_audit" RENAME TO "value_blob_audit";
ALTER TABLE "value_blob_audit"
  DROP CONSTRAINT "ck_blob_audit_valid_timeline"
  ,ADD CONSTRAINT "ck_value_blob_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "blob_audit_id_seq"  RENAME TO "value_blob_audit_id_seq";
ALTER INDEX "ix_blob_audit_create_user_id" RENAME TO "ix_value_blob_audit_create_user_id";
ALTER INDEX "ix_blob_audit_modify_user_id" RENAME TO "ix_value_blob_audit_modify_user_id";


ALTER TABLE "text" RENAME TO "value_text";
ALTER TABLE "value_text"
  DROP CONSTRAINT "fk_text_entity_id"
  ,DROP CONSTRAINT "fk_text_attribute_id"
  ,DROP CONSTRAINT "fk_text_choice_id"
  ,DROP CONSTRAINT "fk_text_create_user_id"
  ,DROP CONSTRAINT "fk_text_modify_user_id"
  ,DROP CONSTRAINT "ck_text_valid_timeline"
  ,ADD CONSTRAINT "fk_value_text_entity_id" FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_text_attribute_id" FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_text_choice_id" FOREIGN KEY (choice_id) REFERENCES choice(id) ON DELETE CASCADE
  ,ADD CONSTRAINT "fk_value_text_create_user_id" FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "fk_value_text_modify_user_id" FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT
  ,ADD CONSTRAINT "ck_value_text_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "text_id_seq"  RENAME TO "value_text_id_seq";
ALTER INDEX "ix_text_entity_id" RENAME TO "ix_value_text_entity_id";
ALTER INDEX "ix_text_attribute_id" RENAME TO "ix_value_text_attribute_id";
ALTER INDEX "ix_text_choice_id" RENAME TO "ix_value_text_choice_id";
--ALTER INDEX "ix_text_value" RENAME TO "ix_value_text_value";
ALTER INDEX "ix_text_create_user_id" RENAME TO "ix_value_text_create_user_id";
ALTER INDEX "ix_text_modify_user_id" RENAME TO "ix_value_text_modify_user_id";


ALTER TABLE "text_audit" RENAME TO "value_text_audit";
ALTER TABLE "value_text_audit"
  -- keep things consistent with the values
  DROP CONSTRAINT "ck_text_audit_valid_timeline"
  ,ADD CONSTRAINT "ck_value_text_valid_timeline" CHECK (create_date <= modify_date)
  ,ALTER COLUMN "value" SET NOT NULL
;
ALTER SEQUENCE "text_audit_id_seq"  RENAME TO "value_text_audit_id_seq";
ALTER INDEX "ix_text_audit_create_user_id" RENAME TO "ix_value_text_audit_create_user_id";
ALTER INDEX "ix_text_audit_modify_user_id" RENAME TO "ix_value_text_audit_modify_user_id";

COMMIT;

