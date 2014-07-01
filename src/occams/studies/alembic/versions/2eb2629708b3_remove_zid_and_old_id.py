"""Remove zid and old_id

Revision ID: 2eb2629708b3
Revises: 60f4ba5ba66
Create Date: 2014-05-19 13:06:58.677357

"""

# revision identifiers, used by Alembic.
revision = '2eb2629708b3'
down_revision = '60f4ba5ba66'

from alembic import op
import sqlalchemy as sa

from alembic import context


def upgrade():
    for table in ['site', 'patient', 'partner',
                  'enrollment', 'visit', 'study', 'cycle']:
        op.drop_column(table, 'zid')
        op.drop_column(table + '_audit', 'zid')

    untrack = [
        'partner',
        'arm', 'cycle', 'enrollment', 'patientreference',
        'reftype', 'site', 'stratum', 'study', 'visit',
        'attribute', 'value_blob', 'category', 'choice',
        'value_datetime', 'value_decimal', 'entity', 'value_integer',
        'schema', 'value_string', 'value_text',
        'context',
        'aliquot', 'aliquotstate', 'aliquottype',
        'location', 'specialinstruction',
        'specimen', 'specimenstate', 'specimentype']

    db = context.get_x_argument(as_dictionary=True).get('db')
    if db and 'cctg' in db:
        untrack += ['patient_log', 'patient_log_nonresponse_type']

    for table in untrack:
        op.drop_column(table, 'old_db')
        op.drop_column(table, 'old_id')


def downgrade():
    pass
