"""Add retract date

Revision ID: 97848b8c0b6
Revises: 437b5e22cf29
Create Date: 2013-11-18 08:30:01.669481

"""

# revision identifiers, used by Alembic.
revision = '97848b8c0b6'
down_revision = '437b5e22cf29'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql

def upgrade():
    """
    Remove form workflow in favor of simple publish/retract dates
    """

    op.drop_constraint('ck_schema_valid_publication', 'schema')

    for tablename in ('schema', 'schema_audit'):
        op.add_column(tablename, sa.Column('retract_date', sa.Date))

        table = sql.table(tablename,
            sql.column('state'),
            sql.column('retract_date'),
            sql.column('modify_date'))

        op.execute(
            table.update()
            .where(table.c.state == op.inline_literal('retracted'))
            .values(retract_date=table.c.modify_date))

        op.drop_column(tablename, 'state')

    op.create_check_constraint('ck_schema_valid_publication', 'schema', 'publish_date <= retract_date')


def downgrade():
    pass
