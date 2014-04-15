"""Alter description data type to text

Revision ID: 473a7fc77f5d
Revises: 97848b8c0b6
Create Date: 2013-12-03 13:41:56.619675

"""

# revision identifiers, used by Alembic.
revision = '473a7fc77f5d'
down_revision = '97848b8c0b6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    for name in (
            'category', 'schema', 'section', 'attribute', 'choice',
            'entity', 'state'):
        for table_name in (name, name + '_audit'):
            op.alter_column(table_name, 'description', type_=sa.UnicodeText)


def downgrade():
    pass
