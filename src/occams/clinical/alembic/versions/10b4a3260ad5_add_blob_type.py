"""Add blob type

Revision ID: 10b4a3260ad5
Revises: 3370866e8d07
Create Date: 2013-11-18 08:28:37.739411

"""

# revision identifiers, used by Alembic.
revision = '10b4a3260ad5'
down_revision = '3370866e8d07'

from alembic import op
import sqlalchemy as sa

from occams.clinical.migrations import alter_enum


def upgrade():

    # remove constraints reliant on the enum or else they are going to interfere
    op.drop_constraint('ck_attribute_valid_object_bind', 'attribute')

    types = [
        'blob',
        'boolean',
        'choice',
        'date',
        'datetime',
        'decimal',
        'integer',
        'object',
        'string',
        'text']

    alter_enum('attribute_type', types,
        ['attribute.type', 'attribute_audit.type'])

    # reinstate the check constraint
    op.create_check_constraint('ck_attribute_valid_object_bind', 'attribute',
        """
        CASE
        WHEN type = 'object'::attribute_type
        THEN object_schema_id IS NOT NULL
        ELSE object_schema_id IS NULL
        END
        """)


def downgrade():
    pass
