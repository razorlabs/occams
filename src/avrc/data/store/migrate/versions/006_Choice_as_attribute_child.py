from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    """ Conforms to DS1 specification by making the choice table a child of
        the attribute table.
    """
    metadata = MetaData(bind=migrate_engine)
    connection = metadata.bind.connect()

    choice_table = Table('choice', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)

    # Use a temporary column to hold the reference from choice to attribute
    Column('temp_id', Integer, ForeignKey('attribute.id')).create(choice_table)

    # Populate the temporary attribute reference
    with connection.begin() as transaction:
        join = (attribute_table.c.field_id == choice_table.c.field_id)
        query = select([attribute_table.c.id, choice_table.c.id], join)

        for (attribute_id, choice_id) in connection.execute(query):
            connection.execute(
                choice_table.update() \
                .where(choice_table.c.id == choice_id) \
                .values(temp_id=attribute_id)
                )

        transaction.commit()

    # Drop the foreign key constraint so there are no reference errors
    fk = ForeignKeyConstraint(
        ['field_id'],
        ['field.id'],
        name='choice_field_id_fkey',
        table=choice_table,
        ondelete='CASCADE',
        )

    fk.drop()

    # Swap the former reference column with the temporary values
    with connection.begin() as transaction:
        query = choice_table.update().values(field_id=choice_table.c.temp_id)
        connection.execute(query)
        transaction.commit()

    # The reference column is now the attribute reference column
    Index('ix_choice_field_id', choice_table.c.field_id).rename('ix_choice_attribute_id')
    choice_table.c.field_id.alter(name='attribute_id')
    choice_table.deregister()
    choice_table = Table('choice', metadata, autoload=True)

    fk = ForeignKeyConstraint(
        ['attribute_id'],
        ['attribute.id'],
        name='choice_attribute_id_fkey',
        table=choice_table,
        ondelete='CASCADE',
        )

    fk.create()

    choice_table.c.temp_id.drop()


def downgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine)
    connection = metadata.bind.connect()

    field_table = Table('field', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)

    # Use a temporary column to hold the reference from choice to attribute
    Column('temp_id', Integer, ForeignKey('field.id')).create(choice_table)

    # Populate the temporary field reference
    with connection.begin() as transaction:
        join = (attribute_table.c.id == choice_table.c.attribute_id)
        query = select([attribute_table.c.field_id, choice_table.c.id], join)

        for (field_id, choice_id) in connection.execute(query):
            connection.execute(
                choice_table.update() \
                .where(choice_table.c.id == choice_id) \
                .values(temp_id=field_id)
                )

        transaction.commit()

    # Drop the foreign key constraint so there are no reference errors
    fk = ForeignKeyConstraint(
        ['attribute_id'],
        ['attribute.id'],
        name='choice_attribute_id_fkey',
        table=choice_table,
        ondelete='CASCADE',
        )
    fk.drop()

    # Swap the former reference column with the temporary values
    with connection.begin() as transaction:
        query = choice_table.update().values(attribute_id=choice_table.c.temp_id)
        connection.execute(query)
        transaction.commit()

    # The reference column is now the field reference column
    Index('ix_choice_attribute_id', choice_table.c.attribute_id).rename('ix_choice_field_id')
    choice_table.c.attribute_id.alter(name='field_id')

    choice_table.c.temp_id.drop()
    choice_table.deregister()
    choice_table = Table('choice', metadata, autoload=True)

    fk = ForeignKeyConstraint(
        ['field_id'],
        ['field.id'],
        name='choice_field_id_fkey',
        table=choice_table,
        ondelete='CASCADE',
        )
    fk.create(metadata.bind)
