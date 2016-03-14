"""Alter attribute audit name/title rescrictions

We forgot to do this in the last revision.

Revision ID: 2319d7836e29
Revises: 425e1e704a65
Create Date: 2016-03-08 16:04:25.037251

"""

# revision identifiers, used by Alembic.
revision = '2319d7836e29'
down_revision = '425e1e704a65'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('attribute_audit', 'title', nullable=True)
    op.alter_column('attribute_audit', 'name', type_=sa.String(100))


def downgrade():
    pass
