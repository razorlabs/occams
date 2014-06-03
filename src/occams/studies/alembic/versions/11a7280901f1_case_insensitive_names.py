"""Case Insensitive names

Revision ID: 11a7280901f1
Revises: 2eb2629708b3
Create Date: 2014-06-03 12:24:06.620581

"""

# revision identifiers, used by Alembic.
revision = '11a7280901f1'
down_revision = '2eb2629708b3'

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.alter_column('schema', 'name', type_=sa.String(32))
    op.alter_column('attribute', 'name', type_=sa.String(20))
    op.alter_column('choice', 'name', type_=sa.String(8))

    op.drop_constraint('schema_name_key', 'schema')
    # PG only
    op.execute('CREATE UNIQUE INDEX uq_schema_version ON schema (LOWER(name), publish_date)')

    op.drop_constraint('uq_attribute_name', 'attribute')
    op.execute('CREATE UNIQUE INDEX uq_attribute_name ON attribute (schema_id, LOWER(name))')

    op.drop_constraint('uq_choice_name', 'choice')
    op.execute('CREATE UNIQUE INDEX uq_choice_name ON choice (attribute_id, LOWER(name))')


def downgrade():
    pass
