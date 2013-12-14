"""
Helper functions for migrations.

Alembic isolates upgrade scripts such that it's not possible to have
common upgrade helpers in the environment. Custom helpers are
implemented in the client application (occams.clinical in this case)
and then imported in the migration steps.

Restrict use of these helpers to only alembic migrations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def alter_enum(name, new_values, cols, new_name=None):
    """
    Modification of ENUMs is not very well supported in PostgreSQL so we have
    to do a bit of hacking to get this to work properly: swap the old
    type with a newly-created type of the same name
    """

    new_name = new_name or name

    op.execute('ALTER TYPE "{0}" RENAME TO "{0}_old"'.format(name))

    sa.Enum(*new_values, name=new_name).create(op.get_bind(), checkfirst=False)

    if isinstance(cols, basestring):
        cols = [cols]

    for col in cols:
        table_name, col_name = col.split('.')

        op.execute("""
            ALTER TABLE {0}
            ALTER COLUMN "{1}" TYPE "{2}"
            USING "{1}"::text::"{2}"
            """.format(table_name, col_name, new_name))

    op.execute('DROP TYPE "{0}_old"'.format(name))


def query_user_id(user):
    """
    Returns a subquery for the specified user.
    """
    user_table = sql.table('user',
                           sql.column('id', sa.Integer()),
                           sql.column('key', sa.String()))

    return (
        sa.select([user_table.c.id])
        .where(user_table.c.key == op.inline_literal(user))
        .as_scalar())
