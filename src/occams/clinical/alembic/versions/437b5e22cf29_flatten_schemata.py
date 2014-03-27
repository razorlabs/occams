"""Flatten schemata

Moving forward 'fieldsets' are purely cosmetic and supported via the
section table

WARNING: this process will remove any orphaned subforms instances

Revision ID: 437b5e22cf29
Revises: 58d06f35c63f
Create Date: 2013-11-18 08:29:28.903745

"""

# revision identifiers, used by Alembic.
revision = '437b5e22cf29'
down_revision = '58d06f35c63f'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql

from occams.clinical.migrations import alter_enum, query_user_id


def upgrade():
    create_section_table()
    migrate_subobjects()
    migrate_subschemata()
    deprecate_subschemata()


def downgrade():
    pass


def create_section_table():
    """
    Installs new "section" table which will hold sub-form rendering settings
    """
    table_name = 'section'
    audit_name = table_name + '_audit'

    # create common attributes
    for name in (table_name, audit_name):
        op.create_table(name,
                        sa.Column('id', sa.Integer,
                                  primary_key=True, autoincrement=True, nullable=False),
                        sa.Column('schema_id', sa.Integer, nullable=False),
                        sa.Column('name', sa.Unicode, nullable=False),
                        sa.Column('title', sa.Unicode, nullable=False),
                        sa.Column('description', sa.Unicode),
                        sa.Column('order', sa.Integer, nullable=False),
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

    op.add_column(table_name, sa.Column('old_db', sa.Unicode, nullable=False))
    op.add_column(table_name, sa.Column('old_id', sa.Integer, nullable=False))
    op.create_unique_constraint('ck_section_old_id',
                                table_name,
                                ['old_db', 'old_id'])

    op.create_unique_constraint(
        'uq_{0}_name'.format(table_name), table_name, ['schema_id', 'name'])
    op.create_unique_constraint(
        'uq_{0}_order'.format(table_name), table_name, ['schema_id', 'order'])

    for local_col, remote, remote_col, ondelete in [
            ('schema_id', 'schema', 'id', 'CASCADE'),
            ('create_user_id', 'user', 'id', 'RESTRICT'),
            ('modify_user_id', 'user', 'id', 'RESTRICT')]:

        op.create_foreign_key(
            'fk_{0}_{1}'.format(table_name, local_col),
            table_name, remote, [local_col], [remote_col], ondelete=ondelete)

    op.create_table(
        'section_attribute',
        sa.Column('section_id',
                  sa.Integer,
                  sa.ForeignKey('section.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('attribute_id',
                  sa.Integer,
                  sa.ForeignKey('attribute.id', ondelete='CASCADE'),
                  nullable=False),
        sa.PrimaryKeyConstraint('section_id', 'attribute_id'),
        sa.UniqueConstraint('attribute_id', name='uq_section_attribute_attribute_id')
        )


def migrate_subobjects():
    """
    Move values to the parent entity
    """

    blame = op.get_context().opts['blame']

    object_table = sql.table(
        'object',
        sql.column('entity_id'),
        sql.column('value'))

    for typename in ('decimal', 'datetime', 'integer', 'string', 'text', 'blob', 'choice'):
        table = sql.table('value_' + typename,
                          sql.column('entity_id'),
                          sql.column('modify_user_id'),
                          sql.column('modify_date'))

        op.execute(
            table.update()
            .values(
                entity_id=object_table.c.entity_id,
                modify_user_id=query_user_id(blame),
                modify_date=sql.func.now())
            .where(table.c.entity_id == object_table.c.value))


def migrate_subschemata():
    """
    Move object attributes to sections
    """

    blame = op.get_context().opts['blame']

    section_table = sql.table('section',
                              sql.column('id'),
                              sql.column('schema_id'),
                              sql.column('name'),
                              sql.column('title'),
                              sql.column('description'),
                              sql.column('order'),
                              sql.column('create_user_id'),
                              sql.column('modify_user_id'),
                              sql.column('revision'),
                              sql.column('old_db'),
                              sql.column('old_id'))

    schema_table = sql.table('schema',
                             sql.column('id'),
                             sql.column('type'),
                             sql.column('is_inline'))

    attribute_table = sql.table('attribute',
                                sql.column('id'),
                                sql.column('schema_id'),
                                sql.column('name'),
                                sql.column('title'),
                                sql.column('description'),
                                sql.column('object_schema_id'),
                                sql.column('order'),
                                sql.column('type'),
                                sql.column('section_id'),
                                sql.column('modify_user_id'),
                                sql.column('modify_date'),
                                sql.column('old_db'),
                                sql.column('old_id'))

    attribute_audit_table = sql.table('attribute_audit',
                                      sql.column('type'))

    section_attribute_table = sql.table('section_attribute',
                                        sql.column('section_id'),
                                        sql.column('attribute_id'))

    # Move parent attributes to the section table
    sub_attribute_query = (
        sa.select([
            attribute_table.c.schema_id,
            attribute_table.c.name,
            attribute_table.c.title,
            attribute_table.c.description,
            attribute_table.c.order,
            query_user_id(blame).label('create_user_id'),
            query_user_id(blame).label('modify_user_id'),
            op.inline_literal(1).label('revision'),
            attribute_table.c.old_db,
            attribute_table.c.old_id])
        .where(attribute_table.c.type == op.inline_literal('object')))

    op.execute(
        section_table.insert()
        .from_select(sub_attribute_query.columns, sub_attribute_query))

    # Move the references to child attributes to the section_attribute table
    parent_attribute_table = sql.alias(attribute_table, name='parent')

    parent_attribute_query = (
        sa.select([
            sa.select([section_table.c.id.label('section_id')])
            .select_from(
                section_table
                .join(parent_attribute_table,
                      (section_table.c.old_db == parent_attribute_table.c.old_db) &
                      (section_table.c.old_id == parent_attribute_table.c.old_id)))
            .where(
                parent_attribute_table.c.object_schema_id == attribute_table.c.schema_id)
            .correlate(attribute_table)
            .as_scalar()
            .label('section_id'),
            attribute_table.c.id.label('attribute_id')])
        .select_from(
            attribute_table
            .join(parent_attribute_table,
                  (parent_attribute_table.c.object_schema_id == attribute_table.c.schema_id))))

    op.execute(
        section_attribute_table.insert()
        .from_select(parent_attribute_query.columns, parent_attribute_query))

    # Rename parent attribute before moving children to avoid name collisions
    op.execute(
        attribute_table.update()
        .values(
            name=op.inline_literal('__') + attribute_table.c.name,
            order=op.inline_literal(100000) + attribute_table.c.order)
        .where(attribute_table.c.type == op.inline_literal('object')))

    # Move all sub-attributes to the parent
    op.execute(
        attribute_table.update()
        .where(
            parent_attribute_table.c.object_schema_id == attribute_table.c.schema_id)
        .values(
            schema_id=parent_attribute_table.c.schema_id,
            # Mainintain distinct order as much as possible
            # to prevent constraint errors
            order=(parent_attribute_table.c.order * op.inline_literal(1000)) + attribute_table.c.order,
            modify_user_id=query_user_id(blame),
            modify_date=sql.func.now()))

    # Delete sub-schemata
    for table in (attribute_table, attribute_audit_table):
        op.execute(table.delete().where(table.c.type == op.inline_literal('object')))

    op.execute(schema_table.delete().where(schema_table.c.is_inline))


def deprecate_subschemata():

    # Disable because it gets in the way
    op.drop_constraint('ck_attribute_valid_object_bind', 'attribute')

    for name in ('schema', 'schema_audit'):
        op.drop_column(name, 'base_schema_id')
        op.drop_column(name, 'is_inline')

    for name in ('attribute', 'attribute_audit'):
        op.drop_column(name, 'object_schema_id')

    op.drop_table('object')
    op.drop_table('object_audit')

    types = [
        'blob',
        'boolean',
        'choice',
        'date',
        'datetime',
        'decimal',
        'integer',
        'string',
        'text']

    alter_enum('attribute_type', types,
               ['attribute.type', 'attribute_audit.type'])
