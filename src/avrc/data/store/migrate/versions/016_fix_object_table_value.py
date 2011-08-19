from sqlalchemy import *
from migrate import *

def fk(*args, **kw):
    fk = ForeignKeyConstraint(*args, **kw)
    fk.drop()
    fk.create()


def upgrade(migrate_engine):
    """ Fixes the the object table's value column to NOT NULL and also 
        fixes the value foreign key to CASCADE on delete. Lastly, also
        prevents the object reference from being removed until the child
        objects are removed (preventing orphans). 
    """
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)

    # Also fix object table's cascade
    value_table = Table('object', metadata, autoload=True)
    value_table.c.value.alter(nullable=False)

    fk([value_table.c.entity_id], [entity_table.c.id],
       name='object_entity_id_fkey', ondelete='RESTRICT')

    fk([value_table.c.value], [entity_table.c.id],
       name='object_value_fkey', ondelete='CASCADE')


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)

    # Also fix object table's cascade
    value_table = Table('object', metadata, autoload=True)
    value_table.c.value.alter(nullable=False)

    fk([value_table.c.entity_id], [entity_table.c.id],
       name='object_entity_id_fkey')

    fk([value_table.c.value], [entity_table.c.id],
       name='object_value_fkey')
