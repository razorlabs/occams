"""Update state enum

Revision ID: 3a7bb2b60182
Revises: 282c6f2fdf29
Create Date: 2013-11-18 08:28:09.360143

"""

# revision identifiers, used by Alembic.
revision = '3a7bb2b60182'
down_revision = '282c6f2fdf29'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql

from occams.clinical.migrations import alter_enum


def upgrade():

    set_state_optional()
    remove_outdated_states()

    values = [
      'pending-entry',
      'in-progress',
      'pending-review',
      'pending-correction',
      'complete']

    alter_enum('entity_state', values, ['entity.state', 'entity_audit.state'])


def downgrade():
    pass


def set_state_optional():
    """
    Allows states to be null
    """

    # The changes need to happen on BOTH the live and audit tables
    for table_name in ('entity', 'entity_audit'):
        op.alter_column(table_name, 'state', nullable=True, server_default=None)


def remove_outdated_states():
    """
    Sets deprecated states to null
    """

    # The changes need to happen on BOTH the live and audit tables
    for table_name in ('entity', 'entity_audit'):

        # ad-hoc table for updating
        table = sql.table(table_name, sql.column('state'))

        op.execute(
            table.update()
            .where(table.c.state.in_(
                map(op.inline_literal, ['inline', 'error', 'inaccurate'])))
            .values(state=op.inline_literal(None)))

