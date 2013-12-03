"""Add is_null

Revision ID: 282c6f2fdf29
Revises: None
Create Date: 2013-11-15 18:13:09.471855

"""

# revision identifiers, used by Alembic.
revision = '282c6f2fdf29'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    """
    Allows entities to be able to be set to 'nil'
    """

    for tablename in ('entity', 'entity_audit'):

        op.add_column(tablename, sa.Column(
            'is_null',
            sa.Boolean,
            nullable=False,
            default=False,
            server_default=sql.false()))

        # ad-hoc table for updating values
        table = sql.table(tablename,
            sql.column('state', sa.String),
            sql.column('is_null', sa.Boolean))


        # "Not Done" and "Not Applicable" states should not contain any data.
        op.execute(
            table.update()
            .where(table.c.state.in_(
                map(op.inline_literal, ['not-done', 'not-applicable'])))
            .values(
                state=op.inline_literal('complete'),
                is_null=sql.true()))


def downgrade():
    pass
