"""Rename value tables

Revision ID: de16a2b0367
Revises: 10b4a3260ad5
Create Date: 2013-11-18 08:28:58.211446

"""

# revision identifiers, used by Alembic.
revision = 'de16a2b0367'
down_revision = '10b4a3260ad5'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql

types = ['decimal', 'integer', 'string', 'datetime', 'text', 'blob']

def upgrade():
    """
    Renames value tables to make them easier to locate
    """

    for type in types:
        old_name = type
        new_name = 'value_' + type

        # Take care of the common behavior between the main and audit tables
        for tablename in (type, type + '_audit'):
            table = sql.table(tablename, sql.column('value'))

            # Removed nulled entries
            op.execute(table.delete().where(table.c.value == None))

            # Modify time constraints
            op.drop_constraint('ck_{0}_valid_timeline'.format(tablename), tablename)
            op.create_check_constraint('ck_value_{0}_valid_timeline'.format(tablename), tablename, 'create_date <= modify_date')

            # Enforce non-null values
            op.alter_column(tablename, 'value', nullable=False)

            # Rename primary keys
            op.execute('ALTER SEQUENCE "{0}_id_seq"  RENAME TO "value_{0}_id_seq"'.format(tablename))

            op.execute('ALTER INDEX "ix_{0}_create_user_id" RENAME TO "ix_{0}_create_user_id"'.format(tablename))
            op.execute('ALTER INDEX "ix_{0}_modify_user_id" RENAME TO "ix_{0}_modify_user_id"'.format(tablename))

            op.rename_table(tablename, 'value_' + tablename)

        # Rename the main table foreign keys
        for remote, local_col, ondelete in [
                ('entity', 'entity_id', 'CASCADE'),
                ('attribute', 'attribute_id', 'CASCADE'),
                ('choice', 'choice_id', 'CASCADE'),
                ('user', 'create_user_id', 'RESTRICT'),
                ('user', 'modify_user_id', 'RESTRICT')]:

            op.drop_constraint('fk_{0}_{1}'.format(type, local_col), new_name)
            op.create_foreign_key('fk_{0}_{1}'.format(new_name, local_col), new_name, remote, [local_col], ['id'], ondelete=ondelete)

        # Rename the main table indexes
        for col in ('entity_id', 'attribute_id', 'choice_id'):
            op.execute('ALTER INDEX "ix_{0}_{1}" RENAME TO "ix_value_{0}_{1}"'.format(type, col))

        # Optimize main table primitive values
        if type not in ('blob', 'text'):
            op.execute('ALTER INDEX "ix_{0}_value" RENAME TO "ix_{0}_value"'.format(type, new_name))


def downgrade():
    pass
