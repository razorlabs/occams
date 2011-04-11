from sqlalchemy import *
from migrate import *


range_table = Table('range', MetaData(),
    Column('id', Integer, primary_key=True),
    Column('instance_id', Integer,
        ForeignKey('instance.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        ),
    Column('attribute_id', Integer,
        ForeignKey('attribute.id', ondelete='CASCADE'),
        nullable=False
        ),
    Column('value_low', Integer, nullable=False),
    Column('value_high', Integer, nullable=False),
    )



indexes = {
    'range_attribute_value_low': ('attribute_id', 'value_low'),
    'range_attribute_value_high': ('attribute_id', 'value_high'),
    'range_attribute_value': ('value_low', 'value_high'),
    }


def upgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    for index_name, column_names in indexes.items():
        columns = [getattr(tables['range'].c, n) for n in column_names]
        Index(index_name, *columns).drop(migrate_engine)

    tables['range'].drop()

    query = tables['type'].delete().where(tables['type'].c.title == u'range')
    migrate_engine.execute(query)


def downgrade(migrate_engine):

    metadata = MetaData(bind=migrate_engine)
    metadata.reflect(only=['instance', 'attribute'])
    range_table.metadata = metadata
    range_table.create()

    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    for index_name, column_names in indexes.items():
        columns = [getattr(tables['range'].c, n) for n in column_names]
        Index(index_name, *columns).create(migrate_engine)

    migrate_engine.execute(tables['type'].insert().values(title=u'range'))