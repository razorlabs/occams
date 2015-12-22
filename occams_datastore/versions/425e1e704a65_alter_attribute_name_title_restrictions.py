"""Alter attribute name/title restrictions

Revision ID: 425e1e704a65
Revises: 1d2d71fb2bde
Create Date: 2015-12-22 12:44:33.926495

"""

# revision identifiers, used by Alembic.
revision = '425e1e704a65'
down_revision = '1d2d71fb2bde'
branch_labels = ('datastore',)

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('attribute', 'title', nullable=True)
    op.alter_column('attribute', 'name', type_=sa.String(100))


def downgrade():
    pass
