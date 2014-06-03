"""Drop checksum

Revision ID: 1fe4b434842c
Revises: 11a7280901f1
Create Date: 2014-06-03 12:24:18.057468

"""

# revision identifiers, used by Alembic.
revision = '1fe4b434842c'
down_revision = '11a7280901f1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('attribute', 'checksum')


def downgrade():
    pass
