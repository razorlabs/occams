from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    """ Converts the floating point table to a decimal numeric table for
        exact floating point values.
    """
    metadata = MetaData(migrate_engine)
    metadata.reflect(only=['attribute', 'choice', 'entity'])
    decimal_table = Table('real', metadata, autoload=True)

    decimal_table.rename('decimal')
    decimal_table.c.value.alter(type=Numeric)

    DDL('ALTER SEQUENCE real_id_seq RENAME TO decimal_id_seq', on='postgresql').execute(metadata.bind)

    ix = Index('ix_real_entity_id', decimal_table.c.attribute_id, decimal_table.c.value)
    ix.rename('ix_decimal_entity_id')

    Index('real_pkey', decimal_table.c.id).rename('decimal_pkey')

    ForeignKeyConstraint([decimal_table.c.attribute_id], ['attribute.id'], name='real_attribute_id_fkey').drop()
    ForeignKeyConstraint([decimal_table.c.attribute_id], ['attribute.id'], name='decimal_attribute_id_fkey', ondelete='CASCADE').create()

    ForeignKeyConstraint([decimal_table.c.choice_id], ['choice.id'], name='real_choice_id_fkey').drop()
    ForeignKeyConstraint([decimal_table.c.choice_id], ['choice.id'], name='decimal_choice_id_fkey', ondelete='CASCADE').create()

    ForeignKeyConstraint([decimal_table.c.entity_id], ['entity.id'], name='real_entity_id_fkey').drop()
    ForeignKeyConstraint([decimal_table.c.entity_id], ['entity.id'], name='decimal_entity_id_fkey', ondelete='CASCADE').create()


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    metadata.reflect(only=['attribute', 'choice', 'entity'])
    real_table = Table('decimal', metadata, autoload=True)

    real_table.rename('real')
    real_table.c.value.alter(type=Float)

    DDL('ALTER SEQUENCE decimal_id_seq RENAME TO real_id_seq', on='postgresql').execute(metadata.bind)

    ix = Index('ix_decimal_entity_id', real_table.c.attribute_id, real_table.c.value)
    ix.rename('ix_real_entity_id')

    Index('decimal_pkey', real_table.c.id).rename('real_pkey')

    ForeignKeyConstraint([real_table.c.attribute_id], ['attribute.id'], name='decimal_attribute_id_fkey').drop()
    ForeignKeyConstraint([real_table.c.attribute_id], ['attribute.id'], name='real_attribute_id_fkey', ondelete='CASCADE').create()

    ForeignKeyConstraint([real_table.c.choice_id], ['choice.id'], name='decimal_choice_id_fkey').drop()
    ForeignKeyConstraint([real_table.c.choice_id], ['choice.id'], name='real_choice_id_fkey', ondelete='CASCADE').create()

    ForeignKeyConstraint([real_table.c.entity_id], ['entity.id'], name='decimal_entity_id_fkey').drop()
    ForeignKeyConstraint([real_table.c.entity_id], ['entity.id'], name='real_entity_id_fkey', ondelete='CASCADE').create()
