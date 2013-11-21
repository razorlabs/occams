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


def upgrade():

    tablename = 'value_choice'
    auditname = 'value_choice_audit'

    # Create the common attributes
    for name in (tablename, auditname):
        op.create_table(name,
            sa.Column('id', sa.Integer, sa.Sequence('{0}_id_seq'.format(name)), autoincrement=True, nullable=False),
            sa.Column('entity_id', sa.Integer, nullable=False),
            sa.Column('attribute_id', sa.Integer, nullable=False),
            sa.Column('value', sa.Integer, nullable=False),
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column('create_date', sa.DateTime, server_default=sa.text('NOW'), nullable=False),
            sa.Column('modify_date', sa.DateTime, server_default=sa.text('NOW'), nullable=False),
            sa.Column('revision', sa.Integer, nullable=False),
            sa.Index('ix_{0}_create_user_id'.format(name), 'create_user_id'),
            sa.Index('ix_{0}_modify_user_id'.format(name), 'modify_user_id'),
            sa.CheckConstraint('create_date <= modify_date', name='ck_{0}_valid_timeline'.format(name)))

    op.create_primary_key(tablename + '_pkey', tablename, ['id'])
    op.create_primary_key(auditname + '_pkey', auditname, ['id', 'revision'])

    for col in ('attribute_id', 'entity_id', 'value'):
        op.create_index('ix_{0}_{1}'.format(tablename, col), tablename, [col])

    for local_col, remote, remote_col, ondelete in [
            ('attribute_id', 'attribute', 'id', 'CASCADE'),
            ('entity_id', 'entity', 'id', 'CASCADE'),
            ('value', 'choice', 'id', 'RESTRICT'),
            ('create_user_id', 'user', 'id', 'RESTRICT'),
            ('modify_user_id', 'user', 'id', 'RESTRICT')]:

        op.create_foreign_key('fk_{0}_{1}'.format(tablename, local_col), tablename, remote, [local_col], [remote_col], ondelete=ondelete)

    # ad-hoc tables for migration of data
    value_choice_table = sql.table(tablename,
        sql.column('entity_id'),
        sql.column('attribute_id'),
        sql.column('value'),
        sql.column('create_date'),
        sql.column('create_user_id'),
        sql.column('modify_date'),
        sql.column('modify_user_id'),
        sql.column('revision'))

    choice_table = sql.table('choice',
        sql.column('id'),
        sql.column('attribute_id'),
        sql.column('name'),
        sql.column('order'))

    choice_audit_table = sql.table('choice_audit',
        sql.column('id'),
        sql.column('attribute_id'),
        sql.column('name'),
        sql.column('order'))

    value_selects = []

    # Migrade choice selections to the new table
    for typename in ('decimal', 'integer', 'string', 'datetime'):
        value_table = sql.table(typename,
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

    all_choices_query = sa.union(*value_selects)
    op.execute(
        value_choice_table.insert()
        .from_select(all_choices_query.columns, all_choices_query))

    for typename in ('decimal', 'integer', 'string', 'datetime', 'blob', 'text'):

        # Delete moved values
        value_table = sql.table(typename, sql.column('attribute_id'))
        op.execute(
            value_table.delete()
            .where(
                sa.exists(
                    choice_table.select()
                    .where(value_table.c.attribute_id == choice_table.c.attribute_id))))

        # drop the old columns
        op.drop_column('value_' + typename, 'choice_id')
        op.drop_column('value_' + typename + '_audit', 'choice_id')

    # Use the choice name as the code value
    for name in ('choice', 'choice_audit'):
        table = sql.table(name, sql.column('name'), sql.column('value'))
        op.execute(table.update().values(name=table.c.value))
        op.drop_column(name, 'value')

    attribute_table = sql.table('attribute',
        sql.column('id'),
        sql.column('type'))

    # Update choice codes for booleans
    op.execute(
        choice_table.update()
        .values(name=sa.case(value=choice_table.c.name, whens=[
            (sa.text('FALSE'), op.inline_literal('0')),
            (sa.text('TRUE'), op.inline_literal('1'))]))
        .where(
            sa.exists(
                attribute_table.select()
                .where(
                    (attribute_table.c.id == choice_table.c.attribute_id)
                    & (attribute_table.c.type == op.inline_literal('boolean'))))))

    # update all string codes to use the order number
    # note that there are some numeric strings that we need to watch out for
    # (e.g. 00332, in this case leave those alone)
    # this is a raw statement because we need regular expressions
    op.execute("""
        UPDATE "choice" SET
          "name" = CAST("order" AS VARCHAR)
        WHERE EXISTS(
          SELECT 1
          FROM "attribute"
          WHERE "attribute"."id" = "choice"."attribute_id"
          AND "attribute"."type" = 'string')
        AND EXISTS(
          SELECT 1
          FROM "choice" as "group"
          WHERE "group"."attribute_id" = "choice"."attribute_id"
          AND "name" ~ '[^0-9]')
        """)

    op.execute(
        attribute_table.update()
        .values(type=op.inline_literal('choice'))
        .where(sa.exists(
            choice_table.select()
            .where(choice_table.c.attribute_id == attribute_table.c.id))))

    op.create_check_constraint('ck_numeric_choice', 'choice', 'name ~ [0-9]+')


def downgrade():
    pass

