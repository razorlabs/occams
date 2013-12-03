"""Flatten schemata

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


def upgrade():
    """
    Flattens entities by removing sub-objects
    Moving forward 'fieldsets' are purely cosmetic and supported via the
    section table
    WARNING: this process will remove any orphaned subforms instances
    """

    blame = op.get_context().opts['blame']

    tablename = 'section'
    auditname = tablename + '_audit'

    # create common attributes
    for name in (tablename, auditname):
        op.create_table(name,
            sa.Column('id', sa.Integer, sa.Sequence('{0}_id_seq'.format(name)), autoincrement=True, nullable=False),
            sa.Column('name', sa.Unicode, nullable=False),
            sa.Column('title', sa.Unicode, nullable=False),
            sa.Column('description', sa.Unicode, nullable=False),
            sa.Column('schema_id', sa.Integer, nullable=False),
            sa.Column('order', sa.Integer, nullable=False),
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column('create_date', sa.DateTime, server_default=sa.text('NOW'), nullable=False),
            sa.Column('modify_date', sa.DateTime, server_default=sa.text('NOW'), nullable=False),
            sa.Column('revision', sa.Integer, nullable=False),
            sa.Index('ix_{0}_create_user_id'.format(name), 'create_user_id'),
            sa.Index('ix_{0}_modify_user_id'.format(name), 'modify_user_id'),
            sa.CheckConstraint('create_date <= modify_date',
                name='ck_{0}_valid_timeline'.format(name)))

    op.create_primary_key(tablename + '_pkey', tablename, ['id'])
    op.create_primary_key(auditname + '_pkey', auditname, ['id', 'revision'])

    op.create_unique_constraint('uq_{0}_name'.format(tablename), tablename, ['schema_id', 'name'])
    op.create_unique_constraint('uq_{0}_order'.format(tablename), tablename, ['schema_id', 'order'])

    for local_col, remote, remote_col, ondelete in [
            ('schema_id', 'schema', 'id', 'CASCADE'),
            ('create_user_id', 'user', 'id', 'RESTRICT'),
            ('modify_user_id', 'user', 'id', 'RESTRICT')]:

        op.create_foreign_key('fk_{0}_{1}'.format(tablename, local_col), tablename, remote, [local_col], [remote_col], ondelete=ondelete)

    # Add a reference to the setion table in attribute
    op.add_column('attribute', sa.Column('section_id', sa.Integer))
    op.add_column('attribute_audit', sa.Column('section_id', sa.Integer))
    op.drop_constraint('uq_attribute_order', tablename)
    op.create_unique_constraint('uq_attribute_order', tablename, ['section_id', 'order'])
    op.create_index('ix_attribute_section_id', 'attribute', ['section_id'])
    op.create_foreign_key('fk_attribute_section_id', 'attribute', 'section', ['section_id'], ['id'], ondelete='CASCADE')

    #
    # Move object attributes to sections
    #

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

    user_table = sql.table('user',
        sql.column('id'),
        sql.column('key'))

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
            (sa.text('100') + attribute_table.c.order).label('order'),
            sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar().label('create_user_id'),
            sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar().label('modify_user_id'),
            op.inline_literal(1).label('revision')])
        .where(attribute_table.c.type == op.inline_literal('object')))

    op.execute(
        section_table.insert()
        .from_select([c for c in  sub_attribute_query.columns],  sub_attribute_query))

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
            name=sql.func.concat(parent_attribute_table.c.name, op.inline_literal('_'), attribute_table.c.name),
            section_id=section_table.c.id,
            modify_user_id=sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar(),
            modify_date=sa.text('NOW')))

    # Create a default section for any top-level non-object attributes
    # NOTE: that some schemata contain a combination of both,
    default_section_query = (
        sa.select([
            attribute_table.c.schema_id,
            schema_table.c.name,
            schema_table.c.title,
            op.inline_literal(0).label('order'),
            sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar().label('create_user_id'),
            sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar().label('modify_user_id'),
            op.inline_literal(1).label('revision')])
        .distinct()
        .where(
            (schema_table.c.id == attribute_table.c.schema_id)
            & (~schema_table.c.is_inline)
            & (attribute_table.c.section_id == op.inline_literal(None))
            & (attribute_table.c.type != op.inline_literal('object'))))

    op.execute(
        section_table.insert()
        .from_select([c for c in default_section_query.columns], default_section_query))

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

    #
    # Move entity instances
    #

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
                modify_user_id=sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar(),
                modify_date=sql.text('NOW'))
            .where(table.c.entity_id == object_table.c.value))

    # Disable because it gets in the way
    op.drop_constraint('ck_attribute_valid_object_bind', 'attribute')

    # Delete sub-schemata
    op.execute(
        schema_table.delete()
        .where(
            (schema_table.c.id == attribute_table.c.object_schema_id)
            | (schema_table.c.is_inline)))

    # Delete all object-atributes
    for name in ('attribute', 'attribute_audit'):
        table = sql.table(name, sql.column('type'))
        op.execute(table.delete().where(table.c.type == op.inline_literal('object')))

    op.drop_table('object')
    op.drop_table('object_audit')

    #
    # Lock the section_id column
    #

    # Delete unmatched attributes, these are likely orphans
    # (sub attrinbtes with no parent attribtues
    op.execute(attribute_table.delete().where(attribute_table.c.section_id == op.inline_literal(None)))

    # Finally lock it
    op.alter_column('attribute', 'section_id', nullable=False)

    #
    # No longer support sub objects
    #

    for name in ('schema', 'schema_audit'):
        op.drop_column(name, 'base_schema_id')
        op.drop_column(name, 'is_inline')

    for name in ('atttribute', 'attribute_audit'):
        op.drop_column(name, 'object_schema_id')

    #
    # Remove "object" as a selectable type
    #

    # Backup the old ENUM
    op.execute('ALTER TYPE "attribute_type" RENAME TO "attribute_type_old"')

    # Declare the new ENUM
    new_attribute_type = sa.Enum(
        'blob', 'boolean', 'choice', 'date', 'datetime', 'decimal', 'integer', 'string', 'text',
        name='attribute_type')

    # swap the type
    for name in ('attribute', 'attribute_audit'):
        op.alter_column(name, 'type', type_=new_attribute_type)

    # Delete the old ENUM
    op.execute('DROP TYPE "attribute_type_old"')


def downgrade():
    pass
