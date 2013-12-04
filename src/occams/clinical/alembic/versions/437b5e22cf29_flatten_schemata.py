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
    create_section_references()
    migrate_subschemata()
    migrate_subobjects()
    finalize_section()
    remove_object_type()


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
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column('create_date', sa.DateTime,
                server_default=sql.func.now(), nullable=False),
            sa.Column('modify_date', sa.DateTime,
                server_default=sql.func.now(), nullable=False),
            sa.Column('revision', sa.Integer,
                primary_key=('audit' in name), nullable=False),
            sa.Index('ix_{0}_create_user_id'.format(name), 'create_user_id'),
            sa.Index('ix_{0}_modify_user_id'.format(name), 'modify_user_id'),
            # Both main/audit tables keep the same check constraint names
            sa.CheckConstraint('create_date <= modify_date',
                name='ck_{0}_valid_timeline'.format(table_name)))

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


def create_section_references():
    """
    Adds references to section in attribute
    """

    op.add_column('attribute', sa.Column('section_id', sa.Integer))
    op.add_column('attribute_audit', sa.Column('section_id', sa.Integer))

    op.create_foreign_key(
        'fk_attribute_section_id',
        'attribute', 'section', ['section_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_attribute_section_id', 'attribute', ['section_id'])


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
        sql.column('revision'))

    schema_table = sql.table('schema',
        sql.column('id'),
        sql.column('name'),
        sql.column('title'),
        sql.column('description'),
        sql.column('is_inline'))

    attribute_table = sql.table('attribute',
        sql.column('schema_id'),
        sql.column('name'),
        sql.column('title'),
        sql.column('description'),
        sql.column('object_schema_id'),
        sql.column('order'),
        sql.column('type'),
        sql.column('section_id'),
        sql.column('modify_user_id'),
        sql.column('modify_date'))

    sub_attribute_query = (
        sa.select([
            attribute_table.c.schema_id,
            attribute_table.c.name,
            attribute_table.c.title,
            attribute_table.c.description,
            # avoid collisions by using a larger order number
            (op.inline_literal(1000) + attribute_table.c.order).label('order'),
            query_user_id(blame).label('create_user_id'),
            query_user_id(blame).label('modify_user_id'),
            op.inline_literal(1).label('revision')])
        .where(attribute_table.c.type == op.inline_literal('object')))

    op.execute(
        section_table.insert()
        .from_select(sub_attribute_query.columns,  sub_attribute_query))

    parent_attribute_table = sql.alias(attribute_table, name='parent')

    # Move all sub-attributes to the parent, prepending the parent's name
    op.execute(
        attribute_table.update()
        .where(
            (parent_attribute_table.c.object_schema_id == attribute_table.c.schema_id)
            & (parent_attribute_table.c.schema_id == section_table.c.schema_id)
            & (parent_attribute_table.c.name == section_table.c.name))
        .values(
            schema_id=parent_attribute_table.c.schema_id,
            name=parent_attribute_table.c.name + op.inline_literal('_') + attribute_table.c.name,
            section_id=section_table.c.id,
            # Mainintain distinct order as much as possible
            # to prevent constraint errors
            order=(section_table.c.id * op.inline_literal(1000)) + attribute_table.c.order,
            modify_user_id=query_user_id(blame),
            modify_date=sql.func.now()))

    # Create a default section for any top-level non-object attributes
    # NOTE: that some schemata contain a combination of both,
    default_section_query = (
        sa.select([
            attribute_table.c.schema_id,
            schema_table.c.name,
            schema_table.c.title,
            op.inline_literal(0).label('order'),
            query_user_id(blame).label('create_user_id'),
            query_user_id(blame).label('modify_user_id'),
            op.inline_literal(1).label('revision')])
        .distinct()
        .where(
            (schema_table.c.id == attribute_table.c.schema_id)
            & (~schema_table.c.is_inline)
            & (attribute_table.c.section_id == op.inline_literal(None))
            & (attribute_table.c.type != op.inline_literal('object'))))

    op.execute(
        section_table.insert()
        .from_select(default_section_query.columns, default_section_query))

    # Finally, attach the non-sectioned scalars to the first section in the
    # form (it *should* be the default section...)
    op.execute(
        attribute_table.update()
        .values(section_id=section_table.c.id)
        .where(
            (section_table.c.schema_id == attribute_table.c.schema_id)
            & (section_table.c.order == op.inline_literal(0))
            & (attribute_table.c.section_id == op.inline_literal(None))
            & (attribute_table.c.type != op.inline_literal('object'))))


def migrate_subobjects():
    """
    Move entity instances
    """

    blame = op.get_context().opts['blame']

    schema_table = sql.table('schema', sql.column('id'), sql.column('type'), sql.column('is_inline'))
    attribute_table = sql.table('attribute', sql.column('object_schema_id'))
    object_table = sql.table('object', sql.column('entity_id'), sql.column('value'))

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

    # Disable because it gets in the way
    op.drop_constraint('ck_attribute_valid_object_bind', 'attribute')

    # Delete sub-schemata
    op.execute(
        schema_table.delete()
        .where(
            schema_table.c.is_inline
            & schema_table.c.id.in_(
                sa.select([attribute_table.c.object_schema_id])
                .where(schema_table.c.id == attribute_table.c.object_schema_id)
                .correlate(schema_table))))

    # Delete all object-atributes
    for name in ('attribute', 'attribute_audit'):
        table = sql.table(name, sql.column('type'))
        op.execute(table.delete().where(table.c.type == op.inline_literal('object')))

    op.drop_table('object')
    op.drop_table('object_audit')


def finalize_section():
    """
    Lock the section_id column
    """

    attribute_table = sql.table('attribute', sql.column('section_id'))

    # Delete unmatched attributes, these are likely orphans
    # (sub attrinbtes with no parent attribtues
    op.execute(attribute_table.delete().where(attribute_table.c.section_id == sa.sql.null()))

    # Finally lock it
    op.alter_column('attribute', 'section_id', nullable=False)


def deprecate_subschemata():

    for name in ('schema', 'schema_audit'):
        op.drop_column(name, 'base_schema_id')
        op.drop_column(name, 'is_inline')

    for name in ('atttribute', 'attribute_audit'):
        op.drop_column(name, 'object_schema_id')


def remove_object_type():

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

