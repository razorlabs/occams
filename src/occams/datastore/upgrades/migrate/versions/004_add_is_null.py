"""
Adds ``is_null`` property to entities and consolidates not-done/not-applicable
"""

from sqlalchemy import *
from migrate import *


NOW = text('CURRENT_TIMESTAMP')


def upgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    entity_audit_table = Table('entity_audit', metadata, autoload=True)

    build_update = lambda table: (
        table
        .update()
        .where(table.c.state.in_(['not-done', 'not-applicable']))
        .values(state='complete', is_null=True))

    build_column = lambda: (
        Column('is_null', Boolean, nullable=False, default=False, server_default=text('FALSE')))

    # Create columns
    build_column().create(entity_table, populate_default=True)
    build_column().create(entity_audit_table, populate_default=True)

    with migrate_engine.begin() as connection:
        connection.execute(build_update(entity_table))
        connection.execute(build_update(entity_audit_table))


def downgrade(migrate_engine):
    raise Exception('Downgrading not supported')

