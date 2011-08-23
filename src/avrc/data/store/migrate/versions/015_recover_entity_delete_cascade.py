from sqlalchemy import *
from migrate import *

def fk(*args, **kw):
    fk = ForeignKeyConstraint(*args, **kw)
    fk.drop()
    fk.create()


def upgrade(migrate_engine):
    """ Recovers missing ONDELETE CASCADE triggers for value tables.
    """
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)

    # Only process tables that are missing ONDELETE CASCADE as of this revision
    # (so far only decimal doesn't need correction)
    for name in ('integer', 'string', 'datetime', 'object'):
        value_table = Table(name, metadata, autoload=True)
        fk_name = '%s_entity_id_fkey' % name
        fk(['entity_id'], ['entity.id'],
           name=fk_name, table=value_table, ondelete='CASCADE')


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)

    for name in ('integer', 'string', 'datetime', 'object'):
        value_table = Table(name, metadata, autoload=True)
        fk_name = '%s_entity_id_fkey' % name
        fk(['entity_id'], ['entity.id'], name=fk_name, table=value_table)
