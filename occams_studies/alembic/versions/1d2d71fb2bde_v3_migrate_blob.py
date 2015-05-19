""" Migrate BLOBS to filesystem

Revision ID: 1d2d71fb2bde
Revises: 2eb2629708b3
Create Date: 2014-12-09 14:37:45.200430

"""

# revision identifiers, used by Alembic.
revision = '1d2d71fb2bde'
down_revision = '2eb2629708b3'

from alembic import op, context
import six
import sqlalchemy as sa

import os
import shutil
import uuid
from subprocess import check_output


def upgrade():

    if context.is_offline_mode():
        raise Exception('Cannot migrate blob files in offline mode')

    base_dir = os.path.normpath(context.config.get_section_option('app:main', 'studies.blob.dir'))
    conn = op.get_bind()

    if os.path.isdir(base_dir):
        shutil.rmtree(base_dir)
    os.mkdir(base_dir)

    for table_name in ('value_blob', 'value_blob_audit'):
        op.add_column(table_name, sa.Column('file_name', sa.Unicode))
        op.add_column(table_name, sa.Column('mime_type', sa.String))

    op.add_column('value_blob', sa.Column('placeholder_path', sa.String))

    for row in conn.execute('SELECT * FROM value_blob WHERE value IS NOT NULL').fetchall():
        relative_path = os.path.join(*str(uuid.uuid4()).split('-'))
        absolute_path = os.path.join(base_dir, relative_path)
        os.makedirs(os.path.dirname(absolute_path))
        with open(absolute_path, 'w+b') as fp:
            shutil.copyfileobj(six.BytesIO(row.value), fp)
        conn.execute(sa.text(
            """
            UPDATE value_blob
            SET placeholder_path = :path,
                mime_type = :mime_type,
                file_name = :file_name
            WHERE id = :id
            """),
            id=row.id,
            file_name=os.path.basename(absolute_path),
            mime_type=check_output(['file', '-b', '-i', absolute_path]).strip(),
            path=relative_path)

    for table_name in ('value_blob', 'value_blob_audit'):
        op.drop_column(table_name, 'value')
        op.add_column(table_name, sa.Column('value', sa.String))

    conn.execute('UPDATE value_blob SET value = placeholder_path')
    op.drop_column('value_blob', 'placeholder_path')

    op.create_check_constraint(
        'ck_name_has_value',
        'value_blob',
        'CASE WHEN value IS NOT NULL THEN file_name IS NOT NULL END')


def downgrade():
    pass
