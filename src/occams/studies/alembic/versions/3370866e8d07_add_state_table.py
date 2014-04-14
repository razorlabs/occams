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
from sqlalchemy.schema import CreateSequence

from occams.studies.migrations import query_user_id


def upgrade():
    create_state_table()
    create_entity_state()
    initialize_state_data()
    migrate_state_enums()
    drop_state_column()


def downgrade():
    pass


def create_state_table():
    """
    Installs the new state table and its corresponding audit table.
    """
    # create the common column/constraints/indexes first
    for table_name in ('state', 'state_audit'):
        op.create_table(table_name,
                        sa.Column('id', sa.Integer,
                                  primary_key=True, autoincrement=True, nullable=False),
                        sa.Column('name', sa.String, nullable=False),
                        sa.Column('title', sa.Unicode, nullable=False),
                        sa.Column('description', sa.Unicode),
                        sa.Column(
                            'create_user_id',
                            sa.Integer,
                            nullable=False),
                        sa.Column('create_date', sa.DateTime,
                                  nullable=False, server_default=sql.func.now(
                                  )),
                        sa.Column(
                            'modify_user_id',
                            sa.Integer,
                            nullable=False),
                        sa.Column('modify_date', sa.DateTime,
                                  nullable=False, server_default=sql.func.now(
                                  )),
                        sa.Column('revision', sa.Integer,
                                  primary_key=(
                                      'audit' in table_name), nullable=False),
                        sa.Index(
                            'ix_%s_create_user_id' %
                            table_name,
                            'create_user_id'),
                        sa.Index(
                            'ix_%s_modify_user_id' %
                            table_name,
                            'modify_user_id'),
                        # Both main/audit tables keep the same check constraint
                        # names
                        sa.CheckConstraint('create_date <= modify_date',
                                           name='ck_state_valid_timeline'))

    # The live table will have some extra data integrity constraints
    op.create_foreign_key(
        'fk_state_create_user_id',
        'state', 'user', ['create_user_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(
        'fk_state_modify_user_id',
        'state', 'user', ['modify_user_id'], ['id'], ondelete='RESTRICT')
    op.create_unique_constraint('uq_state_name', 'state', ['name'])


def create_entity_state():
    """
    Creates an entity-state dependency.
    """
    for table_name in ('entity', 'entity_audit'):
        op.add_column(table_name, sa.Column('state_id', sa.Integer))

    op.create_index('ix_entity_state_id', 'entity', ['state_id'])
    op.create_foreign_key(
        'fk_entity_state_id', 'entity', 'state', ['state_id'], ['id'])


def initialize_state_data():
    """
    Duplicates the enum types to the new state table.
    """

    blame = op.get_context().opts['blame']

    # ad-hoc table for updating data
    state_table = sql.table('state',
                            sql.column('id', sa.Integer),
                            sql.column('name', sa.String()),
                            sql.column('title', sa.String()),
                            sql.column('create_user_id', sa.Integer),
                            sql.column('modify_user_id', sa.Integer),
                            sql.column('revision', sa.Integer))

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
            create_user_id=query_user_id(blame),
            modify_user_id=query_user_id(blame),
            revision=op.inline_literal(1)))


def migrate_state_enums():
    """
    Switch enum values to corresponding state table values.
    """

    state_table = sql.table('state',
                            sql.column('id'),
                            sql.column('name'))

    for table_name in ('entity', 'entity_audit'):
        table = sql.table(table_name,
                          sql.column('state', sa.String()),
                          sql.column('state_id', sa.Integer()))

        op.execute(
            table.update().values(
                state_id=(
                    sa.select([state_table.c.id])
                    .where(state_table.c.name == sa.cast(table.c.state, sa.String))
                    .as_scalar())))


def drop_state_column():
    """
    Removes support for state ENUM values in favor of state table references.
    """
    for table_name in ('entity', 'entity_audit'):
        op.drop_column(table_name, 'state')
