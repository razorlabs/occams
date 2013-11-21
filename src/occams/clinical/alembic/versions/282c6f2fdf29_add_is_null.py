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

    for tablename in ('entity', 'entity_audit'):
        op.add_column(tablename, sa.Column(
            'is_null',
            sa.Boolean(),
            nullable=False,
            default=False,
            server_default=sa.text('FALSE')))

        # ad-hoc table for updating values
        table = sql.table(tablename,
            sql.column('state', sa.String),
            sql.column('is_null', sa.Boolean))

        op.execute(
            table
            .update()
            .where(table.c.state.in_(map(op.inline_literal, ['not-done', 'not-applicable'])))
            .values(
                state=op.inline_literal('complete'),
                is_null=op.inline_literal(True)))


def downgrade():
    pass
