"""Add choice value type

Revision ID: 58d06f35c63f
Revises: de16a2b0367
Create Date: 2013-11-18 08:29:12.888287

"""

# revision identifiers, used by Alembic.
revision = '58d06f35c63f'
down_revision = 'de16a2b0367'

from alembic import op
import sqlalchemy as sa


def upgrade():

    for tablename in ('value_choice', 'value_choice_audit'):
        op.create_table(tablename,
            sa.Column('id', sa.Integer, autoincrement=True, nullable=False),
            sa.Column('entity_id', sa.Integer, nullable=False),
            sa.Column('attribute_id', sa.Integer, nullable=False),
            sa.Column('value', sa.Integer, nullable=False),
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column('create_date', sa.DateTime, nullable=False),
            sa.Column('modify_date', sa.DateTime, nullable=False),
            sa.Column('revision', sa.Integer, nullable=False))

        op.create_check_constraint('ck_{0}_valid_timeline'.format(tablename), tablename,
            'create_date <= modify_date')

#CREATE SEQUENCE value_choice_audit_id_seq
    #START WITH 1
    #INCREMENT BY 1
    #NO MAXVALUE
    #NO MINVALUE
    #CACHE 1;

#ALTER SEQUENCE value_choice_audit_id_seq OWNED BY value_choice_audit.id;

#CREATE SEQUENCE value_choice_id_seq
    #START WITH 1
    #INCREMENT BY 1
    #NO MAXVALUE
    #NO MINVALUE
    #CACHE 1;

#ALTER SEQUENCE value_choice_id_seq OWNED BY "value_choice".id;

#ALTER TABLE ONLY "value_choice" ALTER COLUMN id SET DEFAULT nextval('value_choice_id_seq'::regclass);

#ALTER TABLE ONLY value_choice_audit ALTER COLUMN id SET DEFAULT nextval('value_choice_audit_id_seq'::regclass);

#ALTER TABLE ONLY value_choice_audit
    #ADD CONSTRAINT value_choice_audit_pkey PRIMARY KEY (id, revision);

#ALTER TABLE ONLY "value_choice"
    #ADD CONSTRAINT value_choice_pkey PRIMARY KEY (id);

#CREATE INDEX ix_value_choice_attribute_id ON "value_choice" USING btree (attribute_id);

#CREATE INDEX ix_value_choice_audit_create_user_id ON value_choice_audit USING btree (create_user_id);

#CREATE INDEX ix_value_choice_audit_modify_user_id ON value_choice_audit USING btree (modify_user_id);

#CREATE INDEX ix_value_choice_create_user_id ON "value_choice" USING btree (create_user_id);

#CREATE INDEX ix_value_choice_entity_id ON "value_choice" USING btree (entity_id);

#CREATE INDEX ix_value_choice_modify_user_id ON "value_choice" USING btree (modify_user_id);

#CREATE INDEX ix_value_choice_value ON "value_choice" USING btree (value);

#ALTER TABLE ONLY "value_choice"
    #ADD CONSTRAINT fk_value_choice_attribute_id FOREIGN KEY (attribute_id) REFERENCES attribute(id) ON DELETE CASCADE;

#ALTER TABLE ONLY "value_choice"
    #ADD CONSTRAINT fk_value_choice_value FOREIGN KEY (value) REFERENCES choice(id) ON DELETE CASCADE;

#ALTER TABLE ONLY "value_choice"
    #ADD CONSTRAINT fk_value_choice_create_user_id FOREIGN KEY (create_user_id) REFERENCES "user"(id) ON DELETE RESTRICT;

#ALTER TABLE ONLY "value_choice"
    #ADD CONSTRAINT fk_value_choice_entity_id FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE;

#ALTER TABLE ONLY "value_choice"
    #ADD CONSTRAINT fk_value_choice_modify_user_id FOREIGN KEY (modify_user_id) REFERENCES "user"(id) ON DELETE RESTRICT;

#--
#-- Migrate all the choice selections to the new table
#--

#INSERT INTO "value_choice" (entity_id, attribute_id, value, create_date, create_user_id, modify_date, modify_user_id, revision)
  #SELECT
    #value.entity_id
    #,value.attribute_id
    #,choice.id AS choice_id
    #,value.create_date
    #,value.create_user_id
    #,value.modify_date
    #,value.modify_user_id
    #,value.revision
  #FROM "value_decimal" AS "value"
  #JOIN "choice"
    #ON "choice"."attribute_id" = "value"."attribute_id"
    #AND "value"."value"::text = choice.value
  #UNION
  #SELECT
    #value.entity_id
    #,value.attribute_id
    #,choice.id AS choice_id
    #,value.create_date
    #,value.create_user_id
    #,value.modify_date
    #,value.modify_user_id
    #,value.revision
  #FROM "value_integer" AS "value"
   #JOIN "choice"
    #ON "choice"."attribute_id" = "value"."attribute_id"
    #AND "value"."value"::text = choice.value
  #UNION
  #SELECT
    #value.entity_id
    #,value.attribute_id
    #,choice.id AS choice_id
    #,value.create_date
    #,value.create_user_id
    #,value.modify_date
    #,value.modify_user_id
    #,value.revision
  #FROM "value_string" AS "value"
  #JOIN "choice"
    #ON "choice"."attribute_id" = "value"."attribute_id"
    #AND "value"."value"::text = choice.value
  #UNION
  #SELECT
    #value.entity_id
    #,value.attribute_id
    #,choice.id AS choice_id
    #,value.create_date
    #,value.create_user_id
    #,value.modify_date
    #,value.modify_user_id
    #,value.revision
  #FROM "value_datetime" AS "value"
  #JOIN "choice"
    #ON "choice"."attribute_id" = "value"."attribute_id"
    #AND "value"."value"::text = choice.value
#;

#--
#-- Delete the moved values
#--

#DELETE FROM "value_decimal" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
#DELETE FROM "value_integer" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
#DELETE FROM "value_string" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
#DELETE FROM "value_datetime" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
#DELETE FROM "value_blob" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;
#DELETE FROM "value_text" AS value USING choice AS choice WHERE value.attribute_id = choice.attribute_id;;

    for type in ('decimal', 'datetime', 'integer', 'string', 'text', 'blob'):
        # drop the old columns
        op.drop_column('value_' + type, 'choice_id')
        op.drop_column('value_' + type + '_audit', 'choice_id')

#--
#-- Use the choice name as the code value
#--


#UPDATE "choice" SET "name" = "value";
#UPDATE "choice_audit" SET "name" = "value";

#--
#-- drop the cold column
#--


#ALTER TABLE "choice" DROP COLUMN "value";
#ALTER TABLE "choice_audit" DROP COLUMN "value";

#--
#-- update choice codes for booleans
#--

#UPDATE "choice" SET
  #"name" = CASE "name" WHEN 'False' THEN '0' WHEN 'True' THEN '1' END
#WHERE EXISTS(
  #SELECT 1
  #FROM "attribute"
  #WHERE "attribute"."id" = "choice"."attribute_id"
  #AND "attribute"."type" = 'boolean')
#;

#-- update all string codes to use the order number
#-- note that there are some numeric strings that we need to watch out for
#-- (e.g. 00332, in this case leave those alone)
#UPDATE "choice" SET
  #"name" = CAST("order" AS VARCHAR)
#WHERE EXISTS(
  #SELECT 1
  #FROM "attribute"
  #WHERE "attribute"."id" = "choice"."attribute_id"
  #AND "attribute"."type" = 'string')
#AND EXISTS(
  #SELECT 1
  #FROM "choice" as "group"
  #WHERE "group"."attribute_id" = "choice"."attribute_id"
  #AND "name" ~ '[^0-9]')
#;

#UPDATE "attribute" SET
  #-- map numeric string to auto_choice=False
  #"type" =
    #CASE
      #WHEN EXISTS(SELECT 1 FROM "choice" WHERE "choice"."attribute_id" = "attribute"."id") THEN 'choice'
      #ELSE "type"
      #END
#;


def downgrade():
    pass

