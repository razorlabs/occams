"""Add state table

Revision ID: 3370866e8d07
Revises: 3a7bb2b60182
Create Date: 2013-11-18 08:28:16.589010

"""

# revision identifiers, used by Alembic.
revision = '3370866e8d07'
down_revision = '3a7bb2b60182'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    blame = op.get_context().opts['blame']

    # create the common column/constraints/indexes first
    for tablename in ('state', 'state_audit'):
        op.create_table(tablename,
            sa.Column('id', sa.Integer, nullable=False),
            sa.Column('name', sa.String, nullable=False),
            sa.Column('title', sa.Unicode, nullable=False),
            sa.Column('description', sa.Unicode),
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column('create_date', sa.DateTime, nullable=False, server_default=sa.text('NOW')),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column('modify_date', sa.DateTime, nullable=False, server_default=sa.text('NOW')),
            sa.Column('revision', sa.Integer, nullable=False),
            sa.Index('ix_%s_create_user_id' % tablename, 'create_user_id'),
            sa.Index('ix_%s_modify_user_id' % tablename, 'modify_user_id'),
            sa.CheckConstraint('create_date <= modify_date',
                            name='ck_%s_valid_timeline' % tablename))

    op.create_primary_key('state_pkey', 'state', ['id'])
    op.create_primary_key('state_audit_pkey', 'state_audit', ['id', 'revision'])

    op.create_foreign_key(
        'fk_state_create_user_id',
        'state', 'user', ['create_user_id'], ['id'], ondelete='RESTRICT')

    op.create_foreign_key(
        'fk_state_modify_user_id',
        'state', 'user', ['modify_user_id'], ['id'], ondelete='RESTRICT')

    op.create_unique_constraint('uq_state_name', 'state', ['name'])

    op.add_column('entity',
        sa.Column(
            'state_id',
            sa.Integer,
            sa.ForeignKey('state.id', name='fk_entity_state_id')))

    op.create_index('ix_entity_state_id', 'entity', ['state_id'])

    op.add_column('entity_audit', sa.Column('state_id', sa.Integer))

    # ad-hoc table for updating data
    state_table = sql.table('state',
        sql.column('id', sa.Integer),
        sql.column('name', sa.String()),
        sql.column('title', sa.String()),
        sql.column('create_user_id', sa.Integer),
        sql.column('modify_user_id', sa.Integer),
        sql.column('revision', sa.Integer))

    user_table = sql.table('user',
        sql.column('id', sa.Integer()),
        sql.column('key', sa.String()))

    state_values = [
        {'name': u'pending-entry', 'title': u'Pending Entry', },
        {'name': u'in-progress', 'title': u'In Progress'},
        {'name': u'pending-review', 'title': u'Pending Review'},
        {'name': u'pending-correction', 'title': u'Pending Correction'},
        {'name': u'complete', 'title': u'Complete'}]

    for state in state_values:
        op.execute(state_table.insert().values(
            name=op.inline_literal(state['name']),
            title=op.inline_literal(state['title']),
            create_user_id=sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar(),
            modify_user_id=sa.select([user_table.c.id], user_table.c.key == op.inline_literal(blame)).as_scalar(),
            revision=op.inline_literal(1)))

    for tablename in ('entity', 'entity_audit'):
        table = sql.table(tablename,
            sql.column('state', sa.String()),
            sql.column('state_id', sa.Integer()))

        op.execute(
            table.update().values(
                state_id=sa.select(
                    [state_table.c.id],
                    state_table.c.name == sa.cast(table.c.state, sa.String)).as_scalar()))

        op.drop_column(tablename, 'state')


def downgrade():
    pass
