"""Fix missing deffered choice constraint

Revision ID: 5eb8bce63d7e
Revises: 66de8d816999
Create Date: 2016-06-27 15:28:14.350166

"""

# revision identifiers, used by Alembic.
revision = '5eb8bce63d7e'
down_revision = '66de8d816999'
branch_labels = None


from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('uq_choice_order', 'choice')
    op.create_unique_constraint(
        'uq_choice_order',
        'choice',
        ['attribute_id', 'order'],
        deferrable=True,
        initially='DEFERRED'
    )


def downgrade():
    pass
