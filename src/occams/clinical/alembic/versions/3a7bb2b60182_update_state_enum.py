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


def upgrade():

    # Modification of ENUMs is not very well supported in PostgreSQL so we have
    # to do a bit of hacking to get this to work properly: swap the old
    # type with a newly-created type of the same name

    op.execute('ALTER TYPE "entity_state" RENAME TO "entity_state_old"')

    new_entity_state = sa.Enum([
          'pending-entry',
          'in-progress',
          'pending-review',
          'pending-correction',
          'complete'],
          name='entity_state')

    new_entity_state.create(op.get_bind(), checkfirst=False)

    for tablename in ('entity', 'entity_audit'):

        op.alter_column(tablename, 'state', nullable=True, server_default=None)

        # ad-hoc table for updating
        table = sql.table(tablename, sql.column('state', new_entity_state))

        op.execute(
            table.update(state=None)
            .where(table.c.state.in_(['inline', 'error', 'inaccurate'])))

        op.alter_column(tablename, 'state', type_=new_entity_state)

    op.execute('DROP TYPE "entity_state_old"')


def downgrade():
    pass
