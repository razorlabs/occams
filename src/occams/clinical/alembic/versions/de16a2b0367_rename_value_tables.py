"""Rename value tables to make them visually easier to locate

Revision ID: de16a2b0367
Revises: 10b4a3260ad5
Create Date: 2013-11-18 08:28:58.211446

"""

# revision identifiers, used by Alembic.
revision = 'de16a2b0367'
down_revision = '274852cdf579'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    """
    Renames all the value tables and their corresponding constraints
    """

    for type_name in  ['decimal', 'integer', 'string', 'datetime', 'text', 'blob']:

        # Take care of the common behavior between the main and audit tables
        for table_name in (type_name, type_name + '_audit'):

            # blob/text were created incorrectly and so we must fix the
            # timeline check name here (audit checks constraints
            # apparently use the main table name in their own name generatoin)
            ck_name = table_name if type_name in ('text', 'blob') else type_name

            # Modify time constraints
            op.drop_constraint(
                'ck_{0}_valid_timeline'.format(ck_name), table_name)
            op.create_check_constraint(
                'ck_value_{0}_valid_timeline'.format(type_name), table_name,
                'create_date <= modify_date')

            # Rename indexes
            op.execute("""
                ALTER SEQUENCE "{0}_id_seq"
                RENAME TO "value_{0}_id_seq"
                """.format(table_name))

            op.execute("""
                ALTER INDEX "ix_{0}_create_user_id"
                RENAME TO "ix_value_{0}_create_user_id"
                """.format(table_name))
            op.execute("""
                ALTER INDEX "ix_{0}_modify_user_id"
                RENAME TO "ix_value_{0}_modify_user_id"
                """.format(table_name))

            op.rename_table(table_name, 'value_' + table_name)

        # Rename the main table foreign keys
        for remote, local_col, ondelete in [
                ('entity', 'entity_id', 'CASCADE'),
                ('attribute', 'attribute_id', 'CASCADE'),
                ('choice', 'choice_id', 'CASCADE'),
                ('user', 'create_user_id', 'RESTRICT'),
                ('user', 'modify_user_id', 'RESTRICT')]:

            op.drop_constraint(
                'fk_{0}_{1}'.format(type_name, local_col),
                'value_' + type_name)
            op.create_foreign_key(
                'fk_value_{0}_{1}'.format(type_name, local_col),
                'value_' + type_name,
                remote, [local_col], ['id'], ondelete=ondelete)

        # Rename the main table indexes
        for col in ('entity_id', 'attribute_id', 'choice_id'):
            op.execute("""
                ALTER INDEX "ix_{0}_{1}"
                RENAME TO "ix_value_{0}_{1}"
                """.format(type_name, col))

        # Optimize main table primitive values only
        if type_name not in ('blob', 'text'):
            op.execute("""
                ALTER INDEX "ix_{0}_value"
                RENAME TO "ix_value_{0}_value"
                """.format(type_name))


def downgrade():
    pass

