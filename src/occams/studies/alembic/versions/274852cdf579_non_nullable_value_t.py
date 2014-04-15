"""Non-nullable value table values

Revision ID: 274852cdf579
Revises: 97848b8c0b6
Create Date: 2013-11-22 08:47:14.926290

"""

# revision identifiers, used by Alembic.
revision = '274852cdf579'
down_revision = '10b4a3260ad5'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():

    for type_name in ['decimal', 'integer', 'string', 'datetime', 'text', 'blob']:
        for table_name in (type_name, type_name + '_audit'):

            # Ad-hoc querying table
            table = sql.table(table_name, sql.column('value'))

            # Removed nulled entries
            op.execute(table.delete().where(table.c.value == sql.null()))

            # Enforce non-null values
            op.alter_column(table_name, 'value', nullable=False)


def downgrade():
    pass
