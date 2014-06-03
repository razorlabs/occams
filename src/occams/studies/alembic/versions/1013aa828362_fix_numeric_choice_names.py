"""Fix numeric choice names

Revision ID: 1013aa828362
Revises: 1fe4b434842c
Create Date: 2014-06-03 12:24:57.478679

"""

# revision identifiers, used by Alembic.
revision = '1013aa828362'
down_revision = '1fe4b434842c'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    op.create_check_constraint(
        'ck_choice_numeric_name',
        'choice',
        sa.cast(sql.column('name'), sa.Integer) != sa.null())


def downgrade():
    pass
