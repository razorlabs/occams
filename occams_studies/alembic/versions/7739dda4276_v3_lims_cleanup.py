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
    upgrade_location_titles()
    upgrade_site_locations()
    upgrade_aliquot_type_units()


def downgrade():
    op.drop_column('location', 'is_enabled')


def upgrade_location_titles():

    from slugify import slugify

    location_table = sa.sql.table(
        'location',
        sa.sql.column('id'),
        sa.sql.column('name'),
        sa.sql.column('title'),
        sa.sql.column('active'),
    )

    duplicates = {}
    locations_query = (
        location_table.select()
        .order_by(location_table.c.active.desc()))

    conn = op.get_bind()

    for location in conn.execute(locations_query):
        found = duplicates[location.id] = duplicates.get(location.id, 0) + 1
        # Prefer active to not have duplicate count
        if not location.active and found > 1:
            title = '{0} - {1}'.formate(location.title, found)
        else:
            title = location.title
        op.execute(
            location_table.update()
            .where(location_table.c.id == op.inline_literal(location.id))
            .values(name=op.inline_literal(slugify(title)))
        )


def upgrade_site_locations():
    op.add_column('location', sa.Column(
        'is_enabled',
        sa.Boolean(),
        nullable=False,
        server_default=sa.sql.false()
    ))

    location_table = sa.sql.table(
        'location',
        sa.sql.column('id'),
        sa.sql.column('name'),
        sa.sql.column('is_enabled'),
    )

    url = context.config.get_main_option('sqlalchemy.url')

    # ID's are more reliable in this case....
    if 'cctg' in url:
        pre_enabled = [1, 57, 73, 73, 75, 76]
    elif 'mhealth' in url:
        pre_enabled = [1]
    elif 'aeh' in url:
        pre_enabled = [56, 57]
    else:
        pre_enabled = []

    pre_enabled = [op.inline_literal(i) for i in pre_enabled]

    if pre_enabled:
        op.execute(
            location_table.update()
            .where(location_table.c.id.in_(pre_enabled))
            .values(is_enabled=sa.sql.true()))


def upgrade_aliquot_type_units():
    op.add_column('aliquottype', sa.Column('units', sa.String()))
    op.add_column('aliquot', sa.Column('amount', sa.Numeric()))

    aliquot_type_table = sa.sql.table(
        'aliquottype',
        sa.sql.column('name'),
        sa.sql.column('units'))

    aliquot_table = sa.sql.table(
        'aliquot',
        sa.sql.column('cell_amount'),
        sa.sql.column('volume'),
        sa.sql.column('amount'))

    volume_unit = op.inline_literal(u'mL')
    cell_unit = op.inline_literal(u'x10^6')

    op.execute(
        aliquot_type_table.update()
        .values(
            units=sa.case(value=aliquot_type_table.c.name, whens=[
                # CCTG
                (op.inline_literal(u'pbmc'), cell_unit)
                (op.inline_literal(u'plasma'), volume_unit),
                (op.inline_literal(u'swab'), sa.null()),
                (op.inline_literal(u'urine'), volume_unit),
                (op.inline_literal(u'blood-spot'), sa.null()),
                (op.inline_literal(u'wb-plasma'), volume_unit),
                (op.inline_literal(u'whole-blood'), volume_unit),

                # MHEALTH
                (op.inline_literal(u'heparin-plasma'), volume_unit),

            ], else_=sa.null()))
    )

    op.execute(
        aliquot_table.update()
        .values(
            # The label logic uses these heuristics
            amount=sa.case([
                ((aliquot_table.c.cell_amount > 0),
                    aliquot_table.c.cell_amount),
                ((aliquot_table.c.volume > 0), aliquot_table.c.volume),
            ], else_=sa.null()))
    )

    op.drop_column('aliquot', 'cell_amount')
    op.drop_column('aliquot', 'volume')
