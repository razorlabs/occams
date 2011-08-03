from datetime import datetime

from sqlalchemy import *
from migrate import *

PY_NOW = datetime.now
SQL_NOW = text('CURRENT_TIMESTAMP')

SQL_FALSE = text('FALSE')


value_table_names = ('datetime', 'real', 'integer', 'string', 'object')


def upgrade(migrate_engine):
    """ Adds metadata values to EAV value tables and new indexing properties
    """

    metadata = MetaData(migrate_engine)
    metadata.reflect(only=value_table_names)
    connection = metadata.bind.connect()
    
    metadata_columns = (
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )

    metadata.tables['object'].c.order.drop()

    for value_table_name in value_table_names:
        table = metadata.tables[value_table_name]

        for target_column in metadata_columns:
            column = target_column.copy()
            column.create(table)

        Index('%s_attribute_value' % table.name, table.c.attribute_id, table.c.value).drop()
        Index('ix_%s_attribute_id' % table.name, table.c.attribute_id).create()
        Index('ix_%s_value' % table.name, table.c.value).create()
        Index('ix_%s_choice_id' % table.name, table.c.choice_id).create()
        Index('ix_%s_remove_date' % table.name, table.c.remove_date).create()

    instance_table = Table('instance', metadata, autoload=True)

    # Populate new metadata columns with the start date of the instance
    with connection.begin() as transaction:
        for value_table_name in value_table_names:
            table = metadata.tables[value_table_name]
            print 'Updating values for: %s' % table.name
            connection.execute(
                table.update() \
                .values(
                    create_date=\
                        select([instance_table.c.create_date]) \
                        .where(table.c.instance_id == instance_table.c.id) \
                        .limit(1)
                    )
                )

        transaction.commit()


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    metadata.reflect(only=value_table_names)
    connection = metadata.bind.connect()

    
    metadata_columns = (
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )


    order_column = Column('order', Integer, default=1)
    order_column.create(metadata.tables['object'], populate_default=True)

    for value_table_name in value_table_names:
        table = metadata.tables[value_table_name]
        for target_column in metadata_columns:
            getattr(table.c, target_column.name).drop()

        Index('%s_attribute_value' % table.name, table.c.attribute_id, table.c.value).create()
        Index('ix_entity_attribute_id', table.c.attribute_id).drop()
        Index('ix_entity_value', table.c.value).drop()
        Index('ix_entity_choice_id', table.c.choice_id).drop()
        Index('ix_entity_remove_date', table.c.remove_date).drop()
