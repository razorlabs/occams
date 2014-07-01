"""Rename is_null to not_done

Revision ID: 60f4ba5ba66
Revises: 17e83fd33667
Create Date: 2014-07-01 13:10:51.136269

"""

# revision identifiers, used by Alembic.
revision = '60f4ba5ba66'
down_revision = '17e83fd33667'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('entity', 'is_null', new_column_name='not_done')
    op.alter_column('entity_audit', 'is_null', new_column_name='not_done')


def downgrade():
    pass
