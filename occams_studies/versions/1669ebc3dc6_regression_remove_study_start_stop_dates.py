"""Regression: remove study start/stop dates

Revision ID: 1669ebc3dc6
Revises: 1d2d71fb2bde
Create Date: 2015-12-21 16:49:05.465241

"""

# revision identifiers, used by Alembic.
revision = '1669ebc3dc6'
down_revision = '1d2d71fb2bde'
branch_labels = ('studies',)

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('ck_study_lifespan')
    op.drop_column('study', 'stop_date')
    op.drop_column('study', 'start_date')
    op.drop_column('study', 'is_locked')


def downgrade():
    pass
