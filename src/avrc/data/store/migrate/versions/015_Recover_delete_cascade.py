from sqlalchemy import *
from migrate import *

def fk(*args, **kw):
    fk = ForeignKeyConstraint(*args, **kw)
    fk.drop()
    fk.create()

def upgrade(migrate_engine):
    """ Recovers missing ONDELETE CASCADE triggers that have been lost during
        the huge migration jump from 4-14
    """
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)

    # Only process tables that are missing ONDELETE CASCADE as of this revision
    # (so far only decimal doesn't need correction)
    for name in ('integer', 'string', 'datetime', 'object'):
        value_table = Table('integer', metadata, autoload=True)
        fk_name = '%s_entity_id_fk' % name
        fk(['entity_id'], ['entity.id'],
           name=fk_name, table=value_table, ondelete='CASCADE')

    # Also fix object table's cascade
    value_table = Table('object', metadata, autoload=True)
    value_table.c.value.alter(nullable=False)
    fk(['value'], ['entity.id'],
       name='object_value_fkey', table=value_table, ondelete='CASCADE')


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)

    # Only process tables that are missing ONDELETE CASCADE as of this revision
    # (so far only decimal doesn't need correction)
    for name in ('integer', 'string', 'datetime', 'object'):
        value_table = Table('integer', metadata, autoload=True)
        fk_name = '%s_entity_id_fk' % name
        fk(['entity_id'], ['entity.id'], name=fk_name, table=value_table)

    # Also fix object table's cascade
    value_table = Table('object', metadata, autoload=True)
    value_table.c.value.alter(nullable=False)
    fk(['value'], ['entity.id'], name='object_value_fkey', table=value_table)
