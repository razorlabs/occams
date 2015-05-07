"""V3 changes

Revision ID: 2eb2629708b3
Revises: 60f4ba5ba66
Create Date: 2014-05-19 13:06:58.677357

"""

# revision identifiers, used by Alembic.
revision = '2eb2629708b3'
down_revision = '60f4ba5ba66'

from alembic import op, context
import sqlalchemy as sa
from six import string_types


def upgrade():
    remove_zid_oldid()
    cleanup_attribute()
    cleanup_reftype()
    cleanup_patient()
    cleanup_enrollment()
    cleanup_study()
    cleanup_cycle()
    cleanup_visit()
    cleanup_entity()
    cleanup_context()
    fix_numeric_choice_names()
    case_insensitive_names()
    merge_integer_decimal()
    merge_attribute_section()
    overhaul_attribute()
    cleanup_addis()
    cleanup_cctg()


def cleanup_study():
    for table_name in ['study', 'study_audit']:
        op.add_column(
            table_name,
            sa.Column('is_randomized', sa.Boolean(), server_default=sa.sql.false()))

        op.add_column(
            table_name,
            sa.Column('randomization_schema_id', sa.Integer()))

        op.add_column(
            table_name,
            sa.Column('termination_schema_id', sa.Integer()))

        op.add_column(
            table_name,
            sa.Column('is_locked', sa.Boolean(), server_default=sa.sql.false()))
        op.add_column(
            table_name,
            sa.Column('start_date', sa.Date()))
        op.add_column(
            table_name,
            sa.Column('end_date', sa.Date()))
        op.add_column(
            table_name,
            sa.Column('reference_pattern', sa.String(), nullable=True))
        op.add_column(
            table_name,
            sa.Column('reference_hint', sa.String(), nullable=True))

        # Select the earliest possible date for the start date
        op.execute(
            """
            UPDATE {table}
            SET start_date = LEAST(
                {table}.consent_date,
                (SELECT MIN(enrollment.consent_date)
                 FROM enrollment
                 WHERE study_id = {table}.id
                 LIMIT 1))
            """.format(table=table_name))

        # Set randomization schemata as explicit selections
        op.execute(
            """
            UPDATE {table}
            SET randomization_schema_id = (
                SELECT entity.schema_id
                FROM stratum
                JOIN context ON context.external = 'stratum' AND context.key = stratum.id
                JOIN entity on entity.id = context.entity_id
                WHERE stratum.study_id = {table}.id
                LIMIT 1)
            """.format(table=table_name))

        # Set the termination schema as explicit selection
        op.execute(
            """
            UPDATE {table}
            SET termination_schema_id = (
                SELECT id
                FROM schema
                WHERE name = 'Termination'
                AND publish_date IS NOT NULL
                ORDER BY publish_date DESC
                LIMIT 1)
            """.format(table=table_name))

        op.execute(
            """
            UPDATE {table}
            SET is_randomized = TRUE
            WHERE randomization_schema_id IS NOT NULL
            """.format(table=table_name))

    op.create_foreign_key(
        'fk_study_randomization_schema_id',
        'study',
        'schema',
        ['randomization_schema_id'],
        ['id'],
        ondelete='SET NULL')

    op.create_index('ix_study_randomization_id', 'study', ['randomization_schema_id'])

    op.create_foreign_key(
        'fk_study_termination_schema_id',
        'study',
        'schema',
        ['termination_schema_id'],
        ['id'],
        ondelete='SET NULL')

    op.create_index('ix_study_termination_id', 'study', ['termination_schema_id'])

    op.create_check_constraint(
        'ck_study_randomization_schema_id',
        'study',
        """
        (NOT is_randomized AND randomization_schema_id IS NULL)
        OR
        (is_randomized AND randomization_schema_id IS NOT NULL)
        """)

    op.create_check_constraint(
        'ck_study_lifespan',
        'study',
        """
        start_date <= consent_date
        AND (
            end_date IS NULL
            OR consent_date <= end_date)
        """)

    op.create_table(
        'study_schema',
        sa.Column(
            'study_id',
            sa.Integer(),
            sa.ForeignKey(
                'study.id',
                name='fk_study_schema_study_id',
                ondelete='CASCADE'),
            primary_key=True),
        sa.Column(
            'schema_id',
            sa.Integer(),
            sa.ForeignKey(
                'schema.id',
                name='fk_study_schema_schema_id',
                ondelete='CASCADE'),
            primary_key=True))

    op.create_table(
        'cycle_schema',
        sa.Column(
            'cycle_id',
            sa.Integer(),
            sa.ForeignKey(
                'cycle.id',
                name='fk_cycle_schema_cycle_id',
                ondelete='CASCADE'),
            primary_key=True),
        sa.Column(
            'schema_id',
            sa.Integer(),
            sa.ForeignKey(
                'schema.id',
                name='fk_cycle_schema_schema_id',
                ondelete='CASCADE'),
            primary_key=True))

    op.execute(
        """
        INSERT INTO study_schema (study_id, schema_id) (
            SELECT DISTINCT
                  study.id AS study_id
                , schema.id AS schema_id
            FROM study
            JOIN category ON study.category_id = category.id
            JOIN schema_category ON schema_category.category_id = category.id
            JOIN schema ON schema.id = schema_category.schema_id
            WHERE schema.publish_date IS NOT NULL

            UNION

            SELECT DISTINCT
                  study.id AS study_id
                , schema.id AS schema_id
            FROM study
            JOIN category ON study.log_category_id = category.id
            JOIN schema_category ON schema_category.category_id = category.id
            JOIN schema ON schema.id = schema_category.schema_id
            WHERE schema.publish_date IS NOT NULL
        )
        """)

    op.execute(
        """
        INSERT INTO cycle_schema (cycle_id, schema_id) (
            SELECT DISTINCT
                  cycle.id AS cycle_id
                , schema.id AS schema_id
            FROM cycle
            JOIN category ON cycle.category_id = category.id
            JOIN schema_category ON schema_category.category_id = category.id
            JOIN schema ON schema.id = schema_category.schema_id
            WHERE schema.publish_date IS NOT NULL
        )
        """)

    for table_name in ('study', 'study_audit'):
        op.drop_column(table_name, 'category_id')
        op.drop_column(table_name, 'log_category_id')

    for table_name in ('cycle', 'cycle_audit'):
        op.drop_column(table_name, 'category_id')

    op.execute('TRUNCATE category CASCADE')
    op.execute('TRUNCATE category_audit CASCADE')


def cleanup_cycle():
    for table_name in ['cycle', 'cycle_audit']:
        op.add_column(table_name, sa.Column('is_interim', sa.Boolean, server_default=sa.sql.false()))


def cleanup_attribute():
    op.drop_column('attribute', 'checksum')
    op.drop_column('attribute_audit', 'checksum')
    op.alter_column('attribute', 'is_required', server_default=sa.sql.false())
    op.alter_column('attribute', 'is_collection', server_default=sa.sql.false())
    op.alter_column('attribute', 'is_private', server_default=sa.sql.false())


def cleanup_reftype():
    op.rename_table('reftype', 'reference_type')
    op.drop_constraint('uq_reftype_name', 'reference_type')
    op.create_unique_constraint('uq_reference_type_name', 'reference_type', ['name'])
    op.add_column(
        'reference_type',
        sa.Column('reference_pattern', sa.String(), nullable=True))
    op.add_column(
        'reference_type',
        sa.Column('reference_hint', sa.String(), nullable=True))

    op.rename_table('patientreference', 'patient_reference')
    op.rename_table('patientreference_audit', 'patient_reference_audit')
    op.drop_constraint('fk_patientreference_patient_id', 'patient_reference')
    op.create_foreign_key(
        'fk_patient_reference_patient_id',
        'patient_reference',
        'patient',
        ['patient_id'],
        ['id'],
        ondelete='CASCADE')
    op.alter_column('patient_reference', 'reftype_id', new_column_name='reference_type_id')
    op.alter_column('patient_reference_audit', 'reftype_id', new_column_name='reference_type_id')
    op.drop_constraint('fk_patientreference_reftype_id', 'patient_reference')
    op.create_foreign_key(
        'fk_patient_reference_reference_type_id',
        'patient_reference',
        'reference_type',
        ['reference_type_id'],
        ['id'],
        ondelete='CASCADE')
    op.drop_index('ix_patientreference_patient_id', 'patient_reference')
    op.create_index('ix_patient_reference_patient_id', 'patient_reference', ['patient_id'])
    op.drop_index('ix_patientreference_reference_number', 'patient_reference')
    op.create_index('ix_patient_reference_reference_number', 'patient_reference', ['reference_number'])
    # Accomodate typo in later versions of occwas
    if any(weird in context.config.get_main_option('sqlalchemy.url') for weird in ['cctg', 'mhealth', 'addis']):
        op.drop_constraint('uq_%s_reference', 'patient_reference')
    else:
        op.drop_constraint('uq_patientreference_reference', 'patient_reference')
    op.create_unique_constraint('uq_patient_reference_reference', 'patient_reference', ['patient_id', 'reference_type_id', 'reference_number'])

    op.execute("""
        UPDATE reference_type
        SET reference_pattern = '^76(C|GH)\d{5}$'
          , reference_hint = '76C##### -or- 76GH#####'
        WHERE name IN ('lead-the-way', 'early-test')
        """)
    op.execute(
        """
        UPDATE reference_type
        SET reference_pattern = '^05-01-\d{4}-\d$'
          , reference_hint = '05-01-####-#'
        WHERE name IN ('aeh_num')
        """)


def cleanup_patient():
    blame = context.config.get_main_option('blame')
    op.alter_column('patient', 'our', new_column_name='pid')
    op.alter_column('patient_audit', 'our', new_column_name='pid')
    op.drop_constraint('uq_patient_our', 'patient')
    op.create_unique_constraint('uq_patient_pid', 'patient', ['pid'])

    # Move legacy_number to reference numbers, where it should have been in the first place
    if 'aeh' in context.config.get_main_option('sqlalchemy.url'):
        legacy_name = u'aeh_num'
        legacy_title = u'AEH Number'
    else:
        legacy_name = u'legacy_number'
        legacy_title = u'Legacy Number'
    # some instances had their primary id values manually set... need to fix this
    op.execute('SELECT setval(\'reftype_id_seq\', (SELECT MAX(id) + 1 FROM reference_type), FALSE)')
    op.execute("""
        INSERT INTO reference_type (name, title, create_user_id, create_date, modify_user_id, modify_date)
        VALUES (
              {}
            , {}
            , (SELECT "user".id FROM "user" WHERE key = {user})
            , CURRENT_TIMESTAMP
            , (SELECT "user".id FROM "user" WHERE key = {user})
            , CURRENT_TIMESTAMP
            )
    """.format(op.inline_literal(legacy_name), op.inline_literal(legacy_title), user=op.inline_literal(blame)))
    op.execute("""
        INSERT INTO patient_reference (patient_id, reference_type_id, reference_number, create_user_id, create_date, modify_user_id, modify_date, revision)
        SELECT patient.id
             , (SELECT "reference_type".id FROM reference_type WHERE "reference_type".name = {legacy_name})
             , legacy_number
             , (SELECT "user".id FROM "user" WHERE key = {user})
             , CURRENT_TIMESTAMP
             , (SELECT "user".id FROM "user" WHERE key = {user})
             , CURRENT_TIMESTAMP
             , 1
        FROM patient
        WHERE patient.legacy_number iS NOT NULL
    """.format(legacy_name=op.inline_literal(legacy_name), user=op.inline_literal(blame)))
    op.drop_column('patient', 'legacy_number')

    op.create_table(
        'patient_schema',
        sa.Column(
            'schema_id',
            sa.Integer(),
            sa.ForeignKey(
                'schema.id',
                name='fk_patient_schema_schema_id',
                ondelete='CASCADE'),
            primary_key=True))

    op.execute(
        """
        INSERT INTO patient_schema (schema_id) (
            SELECT DISTINCT id
            FROM schema
            WHERE name IN ('IBio', 'IContact'))
        """)

    if 'cctg' in context.config.get_main_option('sqlalchemy.url'):
        # CCTG has 3 IBio forms, two of which were almost never used,
        # so migrate them to conform to the one that is actually being used.

        op.execute(
            """
            DELETE FROM "patient_schema"
            USING schema
            WHERE schema.id = patient_schema.schema_id
            AND schema.name = 'IBio'
            AND schema.publish_date != '2013-02-26'
            """)

        op.excecute(
            """
            UPDATE entity
            SET schema_id = (
                SELECT id
                FROM schema
                WHERE name = 'IBio'
                AND publish_date = '2013-02-26')
            FROM schema
            WHERE schema.id = entity.schema_id
            AND schema.name = 'IBio'
            AND schema.publish_date != '2013-02-26'
            """)

        # Delete birth_date field data
        op.execute("""
            DELETE FROM value_datetime
            USING attribute, schema
            WHERE value_datetime.attribute_id = attribute.id
            AND attribute.schema_id = schema.id
            AND schema.name = 'IBio'
            """)

        # Move field data to the new main form
        op.execute("""
            UPDATE value_string
            SET attribute_id = (
                SELECT attribute.id
                FROM attribute
                JOIN schema ON schema.id = attribute.schema_id
                WHERE schema.name = 'IBio'
                AND schema.publish_date = '2013-02-26'
                AND attribute.name = og_attribute.name)
            FROM attribute AS og_attribute, schema as og_schema
            WHERE og_attribute.id = value_string.attribute_id
            AND og_schema.id = og_attribute.schema_id
            AND og_schema.name = 'IBio'
            AND og_schema.publish_date != '2013-02-26'
            """)


def cleanup_enrollment():
    # TODO follow up on the status of this, otherwise we'll have to cancel :(
    # For now just realign the dates
    op.execute(
        """
        UPDATE enrollment
        SET consent_date = LEAST(enrollment.consent_date, enrollment.latest_consent_date, enrollment.termination_date)
          , latest_consent_date = GREATEST(enrollment.consent_date, enrollment.latest_consent_date, enrollment.termination_date)
          , termination_date = CASE WHEN termination_date IS NULL THEN NULL ELSE GREATEST(enrollment.consent_date, enrollment.latest_consent_date, enrollment.termination_date) END
        WHERE NOT (
          enrollment.consent_date <= enrollment.latest_consent_date
          AND (enrollment.termination_date IS NULL
                OR enrollment.latest_consent_date <= enrollment.termination_date
                )
          )
        """)

    op.create_check_constraint(
        'ck_enrollment_lifespan',
        'enrollment',
        """
        consent_date <= latest_consent_date
        AND (
            termination_date IS NULL
            OR latest_consent_date <= termination_date)
        """)

    op.create_table(
        'termination_schema',
        sa.Column(
            'schema_id',
            sa.Integer(),
            sa.ForeignKey(
                'schema.id',
                name='fk_termination_schema_schema_id',
                ondelete='CASCADE'),
            primary_key=True))

    op.execute(
        """
        INSERT INTO termination_schema (schema_id) (
            SELECT DISTINCT id
            FROM schema
            WHERE name IN ('Termination'))
        """)


def cleanup_visit():
    blame = context.config.get_main_option('blame')
    # --- Make a master table of the visit records
    op.execute(
        """
        CREATE TEMPORARY TABLE main AS (
          SELECT MIN(id) AS visit_id, patient_id, visit_date
          FROM visit
          GROUP BY patient_id, visit_date
          HAVING COUNT(*) > 1
        )
        """)

    # -- Move forms to the designated "main" visit
    op.execute(
        """
        UPDATE ONLY context
        SET key = main.visit_id
          , modify_date = NOW()
          , modify_user_id = (SELECT id FROM "user" WHERE key = '{user}')
        FROM visit, main
        WHERE (context.external, context.key) = ('visit', visit.id)
        AND (visit.patient_id, visit.visit_date) = (main.patient_id, main.visit_date)
        AND visit.id != main.visit_id
        """.format(user=blame))

    # -- Move cycles to the designated "main" visit (if it does not already have them)
    op.execute(
        """
        UPDATE ONLY visit_cycle
        SET visit_id = main.visit_id
        FROM visit, main
        WHERE visit_cycle.visit_id = visit.id
        AND (visit.patient_id, visit.visit_date) = (main.patient_id, main.visit_date)
        AND visit.id != main.visit_id
        AND visit_cycle.cycle_id NOT IN (
          SELECT cycle_id
          FROM visit_cycle as othercycle
          WHERE othercycle.visit_id = main.visit_id
        )
        """)

    # -- Delete the duplicate visit
    op.execute(
        """
        DELETE FROM visit
        USING main
        WHERE (visit.patient_id, visit.visit_date) = (main.patient_id, main.visit_date)
        AND visit.id != main.visit_id
        """)

    op.create_unique_constraint(
        'uq_visit_patient_id_visit_date',
        'visit',
        ['patient_id', 'visit_date'])


def cleanup_entity():
    for table_name in ('entity', 'entity_audit'):
        op.drop_column(table_name, 'name')
        op.drop_column(table_name, 'title')
        op.drop_column(table_name, 'description')


def cleanup_context():
    op.create_index('ix_context_external_key', 'context', ['external', 'key'])


def alter_enum(name, new_values, cols, new_name=None):
    """
    Modification of ENUMs is not very well supported in PostgreSQL so we have
    to do a bit of hacking to get this to work properly: swap the old
    type with a newly-created type of the same name
    """

    new_name = new_name or name

    op.execute('ALTER TYPE "{0}" RENAME TO "{0}_old"'.format(name))

    sa.Enum(*new_values, name=new_name).create(op.get_bind(), checkfirst=False)

    if isinstance(cols, string_types):
        cols = [cols]

    for col in cols:
        table_name, col_name = col.split('.')

        op.execute("""
            ALTER TABLE {0}
            ALTER COLUMN "{1}" TYPE "{2}"
            USING "{1}"::text::"{2}"
            """.format(table_name, col_name, new_name))

    op.execute('DROP TYPE "{0}_old"'.format(name))


def remove_zid_oldid():
    for table in ['site', 'patient', 'partner',
                  'enrollment', 'visit', 'study', 'cycle']:
        op.drop_column(table, 'zid')
        op.drop_column(table + '_audit', 'zid')

    untrack = [
        'arm', 'cycle', 'enrollment', 'patientreference',
        'reftype', 'site', 'stratum', 'study', 'visit',
        'attribute', 'value_blob', 'category', 'choice',
        'value_datetime', 'value_decimal', 'entity', 'value_integer',
        'schema', 'value_string', 'value_text', 'value_choice',
        'context']

    url = context.config.get_main_option('sqlalchemy.url')

    if 'aeh' in url:
        untrack += ['partner']

    if 'cctg' in url:
        untrack += ['patient_log', 'patient_log_nonresponse_type']

    if 'aeh' in url or 'cctg' in url or 'mhealth' in url:
        untrack += [
            'aliquot', 'aliquotstate', 'aliquottype',
            'location', 'specialinstruction',
            'specimen', 'specimenstate', 'specimentype']

    for table in untrack:
        op.drop_column(table, 'old_db')
        op.drop_column(table, 'old_id')


def fix_numeric_choice_names():
    op.create_check_constraint(
        'ck_choice_numeric_name',
        'choice',
        sa.cast(sa.sql.column('name'), sa.Integer) != sa.null())


def case_insensitive_names():

    op.alter_column('attribute', 'name', type_=sa.String(20))
    op.alter_column('choice', 'name', type_=sa.String(8))

    op.drop_constraint('schema_name_key', 'schema')
    # PG only
    op.execute('CREATE UNIQUE INDEX uq_schema_version ON schema (LOWER(name), publish_date)')

    op.drop_constraint('uq_attribute_name', 'attribute')
    op.execute('CREATE UNIQUE INDEX uq_attribute_name ON attribute (schema_id, LOWER(name))')

    op.drop_constraint('uq_choice_name', 'choice')
    op.execute('CREATE UNIQUE INDEX uq_choice_name ON choice (attribute_id, LOWER(name))')


def merge_integer_decimal():

    op.execute("DELETE FROM attribute_audit WHERE type = 'boolean'");

    new_types = ['blob', 'choice', 'date', 'datetime', 'integer', 'decimal', 'number', 'string', 'text']
    alter_enum('attribute_type', new_types, ['attribute.type', 'attribute_audit.type'])

    for table_name in ['attribute', 'attribute_audit']:

        op.add_column(
            table_name,
            sa.Column('decimal_places', sa.Integer()))

        table = sa.sql.table(table_name,
                             sa.sql.column('type'),
                             sa.sql.column('decimal_places'))

        op.execute(
            table.update()
            .where(table.c.type == op.inline_literal('integer'))
            .values(
                type=op.inline_literal('number'),
                decimal_places=op.inline_literal('0')))

        op.execute(
            table.update()
            .where(table.c.type == op.inline_literal('decimal'))
            .values(
                type=op.inline_literal('number'),
                decimal_places=sa.sql.null()))

    new_types = ['blob', 'choice', 'date', 'datetime', 'number', 'string', 'text']
    alter_enum('attribute_type', new_types, ['attribute.type', 'attribute_audit.type'])

    op.rename_table('value_decimal', 'value_number')
    op.rename_table('value_decimal_audit', 'value_number_audit')

    number_table = sa.sql.table(
        'value_number',
        sa.sql.column('entity_id'),
        sa.sql.column('attribute_id'),
        sa.sql.column('value'),
        sa.sql.column('create_date'),
        sa.sql.column('create_user_id'),
        sa.sql.column('modify_date'),
        sa.sql.column('modify_user_id'),
        sa.sql.column('revision'))

    integer_table = sa.sql.table(
        'value_integer',
        sa.sql.column('entity_id'),
        sa.sql.column('attribute_id'),
        sa.sql.column('value'),
        sa.sql.column('create_date'),
        sa.sql.column('create_user_id'),
        sa.sql.column('modify_date'),
        sa.sql.column('modify_user_id'),
        sa.sql.column('revision'))

    op.execute(
        number_table.insert().from_select(
            [c.name for c in integer_table.c],
            integer_table.select()))

    op.drop_table('value_integer')
    op.drop_table('value_integer_audit')


def merge_attribute_section():
    new_types = ['blob', 'choice', 'date', 'datetime', 'number', 'section', 'string', 'text']
    alter_enum('attribute_type', new_types, ['attribute.type', 'attribute_audit.type'])

    op.add_column('attribute', sa.Column('parent_attribute_id', sa.Integer()))
    op.add_column('attribute_audit', sa.Column('parent_attribute_id', sa.Integer()))

    op.create_foreign_key(
        'fk_parent_attribute_id',
        'attribute',
        'attribute',
        ['parent_attribute_id'],
        ['id'],
        ondelete='CASCADE')

    attribute_table = sa.sql.table(
        'attribute',
        sa.sql.column('schema_id'),
        sa.sql.column('parent_attribute_id'),
        sa.sql.column('name'),
        sa.sql.column('title'),
        sa.sql.column('description'),
        sa.sql.column('type'),
        sa.sql.column('create_date'),
        sa.sql.column('create_user_id'),
        sa.sql.column('modify_date'),
        sa.sql.column('modify_user_id'),
        sa.sql.column('order'),
        sa.sql.column('revision'))

    section_table = sa.sql.table(
        'section',
        sa.sql.column('schema_id'),
        sa.sql.column('name'),
        sa.sql.column('title'),
        sa.sql.column('description'),
        sa.sql.column('create_date'),
        sa.sql.column('create_user_id'),
        sa.sql.column('modify_date'),
        sa.sql.column('modify_user_id'),
        sa.sql.column('order'),
        sa.sql.column('revision'))

    op.execute(
        section_table
        .update()
        .values(
            name=op.inline_literal('s_') + section_table.c.name,
            order=op.inline_literal(1000000000) + section_table.c.order))

    section_query = sa.select([
        section_table.c.schema_id,
        section_table.c.name,
        section_table.c.title,
        section_table.c.description,
        op.inline_literal('section').label('type'),
        section_table.c.create_date,
        section_table.c.create_user_id,
        section_table.c.modify_date,
        section_table.c.modify_user_id,
        section_table.c.order,
        section_table.c.revision])

    op.execute(
        attribute_table
        .insert()
        .from_select([c.name for c in section_query.c], section_query))

    # USE SQL, it's faster...
    op.execute("""
        UPDATE  attribute
        SET     parent_attribute_id = (
            SELECT  parent_attribute.id
            FROM    attribute AS parent_attribute
            JOIN    section ON (section.schema_id, section.name) = (parent_attribute.schema_id, parent_attribute.name)
            JOIN    section_attribute ON section_attribute.section_id = section.id
            WHERE   attribute.id = section_attribute.attribute_id)
        """)

    op.drop_table('section_attribute')
    op.drop_table('section')
    op.drop_table('section_audit')


def overhaul_attribute():

    if op.get_bind().dialect.name == 'postgresql':
        has_size_type = op.get_bind().execute(
            "select exists (select 1 from pg_type "
            "where typname='attribute_widget')").scalar()
        if not has_size_type:
            op.execute("CREATE TYPE attribute_widget AS ENUM ('checkbox', 'email', 'radio', 'select', 'phone')")

    for table_name in ['attribute', 'attribute_audit']:

        op.alter_column(table_name, 'validator', new_column_name='pattern')

        op.add_column(
            table_name,
            sa.Column(
                'is_system',
                sa.Boolean(),
                nullable=False,
                server_default=sa.sql.false()))

        op.add_column(
            table_name,
            sa.Column(
                'is_readonly',
                sa.Boolean(),
                nullable=False,
                server_default=sa.sql.false()))

        op.add_column(
            table_name,
            sa.Column(
                'is_shuffled',
                sa.Boolean(),
                nullable=False,
                server_default=sa.sql.false()))

        op.add_column(
            table_name,
            sa.Column('widget', sa.Enum('checkbox', 'email', 'radio', 'select', 'phone', name='attribute_widget')))

        op.add_column(table_name, sa.Column('constraint_logic', sa.Text()))
        op.add_column(table_name, sa.Column('skip_logic', sa.Text()))

    op.drop_constraint('uq_attribute_order', 'attribute')
    op.create_unique_constraint(
        'uq_attribute_order',
        'attribute',
        ['schema_id', 'order'],
        deferrable=True,
        initially='DEFERRED')

    op.create_check_constraint(
        'ck_number_decimal_places',
        'attribute',
        "CASE WHEN type != 'number' THEN decimal_places IS NULL END")

    op.create_check_constraint(
        'ck_type_widget',
        'attribute',
        """
        CASE
            WHEN widget IS NOT NULL THEN
                CASE type
                    WHEN 'string' THEN widget IN ('phone', 'email')
                    WHEN 'choice' THEN
                        CASE
                            WHEN is_collection THEN widget IN ('select', 'checkbox')
                            ELSE widget IN ('select', 'radio')
                        END
                END
        END
        """)

def cleanup_addis():
    if 'addis' not in context.config.get_main_option('sqlalchemy.url'):
        return

    op.execute("DELETE FROM schema WHERE name = 'IBio'")
