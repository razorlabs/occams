"""V3 LIMS cleanup

Revision ID: 7739dda4276
Revises: 1d2d71fb2bde
Create Date: 2015-10-22 22:47:21.314965

"""

# revision identifiers, used by Alembic.
revision = '7739dda4276'
down_revision = '1d2d71fb2bde'

from alembic import op, context
import sqlalchemy as sa


def upgrade():
    op.add_column('location', sa.Column(
        'is_enabled',
        sa.Boolean(),
        nullable=False,
        server_default=sa.sql.false()
    ))

    url = context.config.get_main_option('sqlalchemy.url')

    location_table = sa.sql.table(
        'location',
        sa.sql.column('id'),
        sa.sql.column('name'),
        sa.sql.column('is_enabled'),
    )

    if 'cctg' in url:
        pre_enabled = [1, 57, 73, 73, 75, 76]
    elif 'mhealth' in url:
        pre_enabled = [1]
    else:
        pre_enabled = []

    if pre_enabled:
        op.execute(
            location_table.update()
            .where(location_table.c.id.in_(pre_enabled))
            .values(is_enabled=sa.sql.true()))

    op.execute(
        location_table.update()
        .where(location_table.c.name == u'long_beach_lab')
        .values(name='long-beach-lab')
    )


def downgrade():
    op.drop_column('location', 'is_enabled')
