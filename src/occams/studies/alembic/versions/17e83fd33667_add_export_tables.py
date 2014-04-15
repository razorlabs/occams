"""Add export tables

Revision ID: 17e83fd33667
Revises: 473a7fc77f5d
Create Date: 2013-12-04 08:37:36.465419

"""

# revision identifiers, used by Alembic.
revision = '17e83fd33667'
down_revision = '473a7fc77f5d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.dialects.postgres import JSON


def upgrade():

    table_name = 'export'
    audit_name = table_name + '_audit'

    for name in (table_name, audit_name):
        op.create_table(
            name,
            sa.Column('id', sa.Integer,
                      primary_key=True, autoincrement=True, nullable=False),
            sa.Column('name', sa.Unicode, nullable=False),
            sa.Column('owner_user_id', sa.Integer, nullable=False),
            sa.Column('expand_collections', sa.Boolean, nullable=False),
            sa.Column('use_choice_labels', sa.Boolean, nullable=False),
            sa.Column('notify', sa.Boolean, nullable=False),
            sa.Column('status',
                      sa.Enum('failed', 'pending', 'complete',
                              name='export_status'),
                      nullable=False,
                      default='pending'),
            sa.Column('contents', JSON, nullable=False),
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column('create_date',
                      sa.DateTime,
                      nullable=False,
                      server_default=sql.func.now()),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column('modify_date',
                      sa.DateTime,
                      nullable=False,
                      server_default=sql.func.now()),
            sa.Column('revision',
                      sa.Integer,
                      primary_key=('audit' in name),
                      nullable=False),
            sa.Index('ix_%s_create_user_id' % name, 'create_user_id'),
            sa.Index('ix_%s_modify_user_id' % name, 'modify_user_id'),
            # Both main/audit tables keep the same check constraint names
            sa.CheckConstraint('create_date <= modify_date',
                               name='ck_%s_valid_timeline' % table_name))

    # The live table will have some extra data integrity constraints
    op.create_unique_constraint(
        'uq_%s_name' % table_name, 'export', ['name'])
    op.create_index('ix_%s_owner_user_id' % table_name,
                    table_name, ['owner_user_id'])
    op.create_foreign_key(
        'fk_%s_owner_user_id' % table_name,
        table_name, 'user', ['create_user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(
        'fk_%s_create_user_id' % table_name,
        table_name, 'user', ['create_user_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(
        'fk_%s_modify_user_id' % table_name,
        table_name, 'user', ['modify_user_id'], ['id'], ondelete='RESTRICT')


def downgrade():
    pass
