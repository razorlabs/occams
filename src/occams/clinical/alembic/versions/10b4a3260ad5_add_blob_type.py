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


def upgrade():

    # Modification of ENUMs is not very well supported in PostgreSQL so we have
    # to do a bit of hacking to get this to work properly: swap the old
    # type with a newly-created type of the same name

    op.execute('ALTER TYPE "attribute_type" RENAME TO "attribute_type_old"')

    new_attribute_type = sa.Enum(['blob', 'boolean', 'choice', 'date', 'datetime', 'decimal', 'integer', 'object', 'string', 'text'],
          name='attribute_type')

    new_attribute_type.create(op.get_bind(), checkfirst=False)

    # constraint reliant on the enum are going to interfere
    # they have to be temporarily removed
    op.drop_constraint('ck_attribute_valid_object_bind', 'attribute')

    for tablename in ('attribute', 'attribute_audit'):
        op.alter_column(tablename, 'state', type_=new_attribute_type)

    op.create_check_constraint(
        'ck_attribute_valid_object_bind',
        'attribute',
        """
        CASE
        WHEN type = 'object'::attribute_type
        THEN object_schema_id IS NOT NULL
        ELSE object_schema_id IS NULL
        """)

    op.execute('DROP TYPE "attribute_type_old"')


def downgrade():
    pass
