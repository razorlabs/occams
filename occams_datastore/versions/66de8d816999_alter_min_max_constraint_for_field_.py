"""Alter min max constraint for field validation

Revision ID: 66de8d816999
Revises: 2319d7836e29
Create Date: 2016-04-20 13:46:24.477393

"""

# revision identifiers, used by Alembic.
revision = '66de8d816999'
down_revision = '2319d7836e29'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('ck_attribute_valid_value', 'attribute')
    op.create_check_constraint(
        'ck_attribute_valid_value', 'attribute', 'value_min <= value_max')

def downgrade():
    op.drop_constraint('ck_attribute_valid_value', 'attribute')
    op.create_check_constraint(
        'ck_attribute_valid_value', 'attribute', 'value_min < value_max')
