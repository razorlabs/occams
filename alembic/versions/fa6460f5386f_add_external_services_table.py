"""Add external services table

Revision ID: fa6460f5386f
Revises: 1669ebc3dc6
Create Date: 2016-04-13 15:19:19.150771

"""

# revision identifiers, used by Alembic.
revision = 'fa6460f5386f'
down_revision = '1669ebc3dc6'
branch_labels = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    main_name = 'external_service'
    audit_name = 'external_service_audit'

    for table_name in (main_name, audit_name):
        op.create_table(
            table_name,
            sa.Column(
                'id',
                sa.Integer,
                primary_key=True,
                autoincrement=True,
                nullable=False),
            sa.Column('study_id', sa.Integer, nullable=False),
            sa.Column('name', sa.String, nullable=False),
            sa.Column('title', sa.Unicode, nullable=False),
            sa.Column('description', sa.Text),
            sa.Column('url_template', sa.String, nullable=False),
            sa.Column(
                'create_date',
                sa.DateTime,
                nullable=False,
                server_default=sql.func.now()),
            sa.Column('create_user_id', sa.Integer, nullable=False),
            sa.Column(
                'modify_date',
                sa.DateTime,
                nullable=False,
                server_default=sql.func.now()),
            sa.Column('modify_user_id', sa.Integer, nullable=False),
            sa.Column(
                'revision',
                sa.Integer,
                nullable=False,
                primary_key=('audit' in table_name),
            ),
            sa.Index('ix_%s_create_user_id' % table_name, 'create_user_id'),
            sa.Index('ix_%s_modify_user_id' % table_name, 'modify_user_id'),
            # Both main/audit tables keep the same check constraint names
            sa.CheckConstraint('create_date <= modify_date',
                               name='ck_%s_valid_timeline' % main_name)
        )

    # The live table will have some extra data integrity constraints
    op.create_foreign_key(
        'fk_%s_study_id' % main_name,
        main_name, 'study', ['study_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint(
        'uq_%s_study_id_name' % main_name, main_name, ['study_id', 'name'])
    op.create_foreign_key(
        'fk_%s_create_user_id' % main_name,
        main_name, 'user', ['create_user_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(
        'fk_%s_modify_user_id' % main_name,
        main_name, 'user', ['modify_user_id'], ['id'], ondelete='RESTRICT')


def downgrade():
    op.drop_table('external_service_audit')
    op.drop_table('external_service')
