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
from sqlalchemy import sql

from occams.clinical.migrations import alter_enum, query_user_id


def upgrade():
    add_choice_type()
    create_choice_table()
    migrate_choice_values()
    drop_value_choice_id()
    normalize_order()
    set_name_as_code()
    force_numeric_name()


def downgrade():
    pass


def add_choice_type():
    # remove constraints reliant on the enum or else they are going to
    # interfere
    op.drop_constraint('ck_attribute_valid_object_bind', 'attribute')

    types = [
        'blob',
        'boolean',
        'choice',
        'date',
        'datetime',
        'decimal',
        'integer',
        'object',
        'string',
        'text']

    alter_enum('attribute_type', types,
               ['attribute.type', 'attribute_audit.type'])

    # reinstate the check constraint
    op.create_check_constraint('ck_attribute_valid_object_bind', 'attribute',
                               """
        CASE
        WHEN type = 'object'::attribute_type
        THEN object_schema_id IS NOT NULL
        ELSE object_schema_id IS NULL
        END
        """)


def create_choice_table():
    """
    Installs the new value choice tables
    """

    table_name = 'value_choice'
    audit_name = table_name + '_audit'

    # Create the common attributes
    for name in (table_name, audit_name):
        op.create_table(name,
                        sa.Column('id', sa.Integer,
                                  primary_key=True, autoincrement=True, nullable=False),
                        sa.Column('entity_id', sa.Integer, nullable=False),
                        sa.Column('attribute_id', sa.Integer, nullable=False),
                        sa.Column('value', sa.Integer, nullable=False),
                        sa.Column(
                            'create_user_id',
                            sa.Integer,
                            nullable=False),
                        sa.Column(
                            'modify_user_id',
                            sa.Integer,
                            nullable=False),
                        sa.Column('create_date', sa.DateTime,
                                  server_default=sql.func.now(
                                  ), nullable=False),
                        sa.Column('modify_date', sa.DateTime,
                                  server_default=sql.func.now(
                                  ), nullable=False),
                        sa.Column('revision', sa.Integer,
                                  primary_key=(
                                      'audit' in name), nullable=False),
                        sa.Index(
                            'ix_{0}_create_user_id'.format(name),
                            'create_user_id'),
                        sa.Index(
                            'ix_{0}_modify_user_id'.format(name),
                            'modify_user_id'),
                        # Both main/audit tables keep the same check constraint
                        # names
                        sa.CheckConstraint('create_date <= modify_date',
                                           name='ck_{0}_valid_timeline'.format(table_name)))

    for col in ('attribute_id', 'entity_id', 'value'):
        op.create_index(
            'ix_{0}_{1}'.format(table_name,
                                col),
            table_name,
            [col])

    for local_col, remote, remote_col, ondelete in [
            ('attribute_id', 'attribute', 'id', 'CASCADE'),
            ('entity_id', 'entity', 'id', 'CASCADE'),
            ('value', 'choice', 'id', 'RESTRICT'),
            ('create_user_id', 'user', 'id', 'RESTRICT'),
            ('modify_user_id', 'user', 'id', 'RESTRICT')]:

        op.create_foreign_key(
            'fk_{0}_{1}'.format(table_name, local_col),
            table_name, remote, [local_col], [remote_col], ondelete=ondelete)


def migrate_choice_values():
    """
    Imports all the choice_id references from the other value tables
    """

    # ad-hoc tables for querying
    value_choice_table = sql.table('value_choice',
                                   sql.column('entity_id'),
                                   sql.column('attribute_id'),
                                   sql.column('value'),
                                   sql.column('create_date'),
                                   sql.column('create_user_id'),
                                   sql.column('modify_date'),
                                   sql.column('modify_user_id'),
                                   sql.column('revision'))

    choice_table = sql.table('choice', sql.column('id'))

    value_selects = []

    # Migrade choice selections to the new table
    for type_name in ('decimal', 'integer', 'string', 'datetime'):
        value_table = sql.table('value_' + type_name,
                                sql.column('choice_id'),
                                sql.column('entity_id'),
                                sql.column('attribute_id'),
                                sql.column('value'),
                                sql.column('create_user_id'),
                                sql.column('modify_user_id'),
                                sql.column('create_date'),
                                sql.column('modify_date'),
                                sql.column('revision'))

        value_selects.append(
            sa.select([
                value_table.c.entity_id,
                value_table.c.attribute_id,
                choice_table.c.id.label('value'),
                value_table.c.create_date,
                value_table.c.create_user_id,
                value_table.c.modify_date,
                value_table.c.modify_user_id,
                value_table.c.revision])
            .select_from(
                value_table.join(
                    choice_table,
                    value_table.c.choice_id == choice_table.c.id)))

    all_choices_query = sa.union(*value_selects).alias().select()

    op.execute(
        value_choice_table.insert()
        .from_select(all_choices_query.columns, all_choices_query))


def drop_value_choice_id():
    """
    Removes the choice_id column from all the main/audit value tables.
    """

    choice_table = sql.table('choice', sql.column('attribute_id'))

    for type_name in ('decimal', 'integer', 'string', 'datetime', 'blob', 'text'):

        value_table = sql.table(
            'value_' + type_name,
            sql.column('attribute_id'))

        # Delete moved values
        op.execute(
            value_table.delete()
            .where(
                sa.exists(
                    choice_table.select()
                    .where(value_table.c.attribute_id == choice_table.c.attribute_id))))

        # drop the old columns
        op.drop_column('value_' + type_name, 'choice_id')
        op.drop_column('value_' + type_name + '_audit', 'choice_id')


def normalize_order():
    """
    Normalize choice ordering so that choices get a clean 1,2,3,4... value
    """
    choice_table = sql.table('choice', sql.column('order'))

    op.execute(
        choice_table.update()
        .values(order=op.inline_literal(1000000000) + choice_table.c.order))

    op.execute("""
        UPDATE choice
        SET "order" = "sorted"."new_order"
        FROM (

          SELECT id, row_number() OVER (
                PARTITION BY attribute_id
                ORDER BY "order"
                ) AS new_order
          FROM choice

        ) AS "sorted"
        WHERE "sorted".id = choice.id
    """)


def set_name_as_code():
    """
    The value column is now deprecated and we'll be using the name as the key code
    """

    # Ad-hoc tables from querying

    attribute_table = sql.table('attribute',
                                sql.column('id'),
                                sql.column('type'))

    choice_table = sql.table('choice',
                             sql.column('name'),
                             sql.column('attribute_id'),
                             sql.column('value'))

    choice_audit = sql.table('choice_audit',
                             sql.column('name'),
                             sql.column('value'))

    for table in (choice_table, choice_audit):
        op.execute(table.update().values(name=table.c.value))
        op.drop_column(table.name, 'value')

    # Update choice codes for booleans (which are Python booleans, not SQ)
    op.execute(
        choice_table.update()
        .values(name=sa.case(value=choice_table.c.name, whens=[
            (op.inline_literal('False'), op.inline_literal('0')),
            (op.inline_literal('True'), op.inline_literal('1'))]))
        .where(
            sa.exists(
                attribute_table.select()
                .where(
                    (attribute_table.c.id == choice_table.c.attribute_id)
                    & (attribute_table.c.type == op.inline_literal('boolean'))))))


def force_numeric_name():
    """
    Choice names can only be numeric (e.g. 123, 00345)
    """

    attribute_table = sql.table('attribute',
                                sql.column('id'),
                                sql.column('type'))

    choice_table = sql.table('choice',
                             sql.column('attribute_id'),
                             sql.column('name'),
                             sql.column('order'))

    choice_group = sa.alias(choice_table, name='choice_group')

    # update all string codes to use the order number
    # note that there are some numeric strings that we need to watch out for
    # (e.g. 00332, in this case leave those alone)
    # this is a raw statement because we need regular expressions
    op.execute(
        choice_table.update()
        .values(name=sa.cast(choice_table.c.order, sa.String))
        .where(
            sa.exists(
                attribute_table.select()
                .where(
                    (attribute_table.c.id == choice_table.c.attribute_id)
                    & (attribute_table.c.type == op.inline_literal('string')))
                .correlate(choice_table))
            & (~sa.select(
                [sql.func.every(choice_group.c.name.op('~')(op.inline_literal('^[0-9]+$')))])
                .where(choice_group.c.attribute_id == choice_table.c.attribute_id)
                .group_by(choice_group.c.attribute_id)
                .correlate(choice_table)
                .as_scalar())))

    # Switch the attribute with choices to type 'choice'
    op.execute(
        attribute_table.update()
        .values(type=op.inline_literal('choice'))
        .where(sa.exists(
            choice_table.select()
            .where(choice_table.c.attribute_id == attribute_table.c.id))))

    # Enforce numerical names
    op.create_check_constraint(
        'ck_numeric_choice',
        'choice',
        "name ~ '^[0-9]+$'")
