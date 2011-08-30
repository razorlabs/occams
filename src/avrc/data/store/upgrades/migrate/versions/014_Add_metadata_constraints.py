from sqlalchemy import *
from migrate import *


# Constraints pass if TRUE AND NULL
TIMELINE_CHECK_SQL = 'create_date <= modify_date AND modify_date <= remove_date'
TIMELINE_NAME_FMT = '%s_valid_edit_timeline'


target_table_names = [
    'entity',
    'choice', 'attribute', 'schema',
    'datetime', 'integer', 'object', 'decimal', 'string',
    ]


def upgrade(migrate_engine):
    """ Adds date constraints to the the EAVCR tables, such that it is
        impossible (or difficult, at least) to have an entry that was
        removed or modified before it was even created.
    """
    metadata = MetaData(migrate_engine)
    metadata.reflect(only=target_table_names)

    for table_name in target_table_names:
        table = metadata.tables[table_name]
        name = TIMELINE_NAME_FMT % table.name
        CheckConstraint(TIMELINE_CHECK_SQL, name=name, table=table).create()


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    metadata.reflect(only=target_table_names)

    for table_name in target_table_names:
        table = metadata.tables[table_name]
        name = TIMELINE_NAME_FMT % table.name
        CheckConstraint(TIMELINE_CHECK_SQL, name=name, table=table).drop()
