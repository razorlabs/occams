from datetime import datetime
from sqlalchemy import *
from migrate import *

metadata = MetaData()

PY_NOW = datetime.now
SQL_NOW = text('CURRENT_TIMESTAMP')

#
# The new choice table, follows DS-1 specification as closely as possible.
# field_id will be migrated to attribute_id at a later time since we cannot
# do a full upgrade to DS-1.
#
choice_table = Table('choice', metadata,
    Column('id', Integer, primary_key=True),
    Column('field_id',
        Integer,
        ForeignKey('field.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        ),
    Column('name', String, nullable=False),
    Column('title', Unicode, nullable=False),
    Column('description', UnicodeText),
    Column('value', Unicode, nullable=False),
    Column('order', Integer, nullable=False),
    Column('create_date', DateTime, nullable=False, default=SQL_NOW),
    Column('create_user_id', Integer),
    Column('modify_date', DateTime, nullable=False, default=SQL_NOW, onupdate=PY_NOW),
    Column('modify_user_id', Integer),
    Column('remove_date', DateTime, index=True),
    Column('remove_user_id', Integer),
    UniqueConstraint('field_id', 'name', name='choice_field_id_name'),
    UniqueConstraint('field_id', 'value', name='choice_field_id_value'),
    UniqueConstraint('field_id', 'order', name='choice_field_id_order'),
    )

#
# The old vocabulary/term joining table, for downgrade purposes
#
vocabulary_term_table = Table('vocabulary_term', metadata,
    Column('vocabulary_id', Integer,
           ForeignKey('vocabulary.id', ondelete='CASCADE')),
    Column('term_id', Integer, ForeignKey('term.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('vocabulary_id', 'term_id')
    )

#
# The old vocabulary table, for downgrade purposes
#
vocabulary_table = Table('vocabulary', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', Unicode, nullable=False, index=True),
    Column('description', Unicode),
    )

#
# The old term table, for downgrade purposes
#
term_table = Table('term', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', Unicode),
    Column('token', Unicode, nullable=False, index=True),
    Column('value_str', Unicode),
    Column('value_int', Integer),
    Column('value_real', Float),
    Column('value_range_low', Integer),
    Column('value_range_high', Integer),
    Column('order', Integer, nullable=False, default=1),
    )

#
# The old selection table, for downgrade purposes
#
selection_table = Table('selection', metadata,
    Column('id', Integer, primary_key=True),
    Column(
        'instance_id',
        Integer,
        ForeignKey('instance.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        ),
    Column(
       'attribute_id',
       Integer,
       ForeignKey('attribute.id', ondelete='CASCADE'),
       nullable=False
       ),
    Column('value', Integer, ForeignKey('term.id'), nullable=False),
    )

selection_index = Index(
    'selection_attribute_value',
    selection_table.c.attribute_id,
    selection_table.c.value
    )

#
# The EAV value tables to be updated with the new choice_id property (DS-1)
#
value_table_names = ['datetime', 'string', 'real', 'integer', 'object']


def upgrade(migrate_engine):
    """ Upgrades the attribute vocabularies to the DS-1 specification.

        Note that an irreversible side effect of this upgrade is that
        choice terms orders will be changed permanently. The reason for
        this is because originally datastore did not handle vocabulary term
        order and thus defaulted everything to 1. This upgrade tries to
        fix that by guessing the possible order based on the current order
        value (in case the term has been updated with a correct order) and then
        the id value (creation order, because DS-0 doesn't specify
        create/modify data on some tables).
    """
    metadata.bind = migrate_engine
    metadata.reflect(only=['field', 'type'] + value_table_names)

    field_table = metadata.tables['field']
    selection_table = metadata.tables['selection']
    string_table = metadata.tables['string']
    type_table = metadata.tables['type']

    choice_table.drop(checkfirst=True)
    choice_table.create()

    # Add the choice attribute to EAV value tables
    for name in value_table_names:
        choice_column = Column(
            'choice_id',
            Integer,
            ForeignKey('choice.id', ondelete='CASCADE'),
            )

        choice_column.create(metadata.tables[name], 'ix_%s_choice_id' % name)

    connection = migrate_engine.connect()

    # Migrate the data from the old vocabulary tables to the
    # choice table and related columns
    with connection.begin() as transaction:

        # As of the current version all vocabularies are strings
        (string_type_id,) = connection.execute(
            select([type_table.c.id]).where(type_table.c.title == 'string')
            ).fetchone()

        (selection_type_id,) = connection.execute(
            select([type_table.c.id]).where(type_table.c.title == 'selection')
            ).fetchone()

        field_query = \
            select([field_table.c.id, field_table.c.vocabulary_id]) \
            .where(field_table.c.vocabulary_id != None)

        # Only retrieve field which actually have a vocabulary
        for field_id, vocabulary_id, in connection.execute(field_query):
            join_query = term_table.join(vocabulary_term_table)
            term_query = select([term_table], from_obj=join_query) \
                .where(vocabulary_term_table.c.vocabulary_id == vocabulary_id)\
                .order_by(term_table.c.order.asc(), term_table.c.id.asc())

            order = 0

            connection.execute(
                field_table.update() \
                .where(field_table.c.id == field_id) \
                .values(type_id=string_type_id) \
                )

            # Each term will me migrated to a new choice entry, along
            # with new order value
            for term in connection.execute(term_query):
                order += 1
                term_id = term['id']

                result = connection.execute(
                    choice_table.insert() \
                    .values(
                        field_id=field_id,
                        name=term['token'],
                        title=term['title'],
                        value=term['value_str'],
                        order=order
                        )
                    )

                (choice_id,) = result.last_inserted_ids()

                value_query = \
                    select([selection_table]) \
                    .where(selection_table.c.value == term_id)

                for value in connection.execute(value_query):
                    connection.execute(
                        string_table.insert() \
                        .values(
                            instance_id=value['instance_id'],
                            attribute_id=value['attribute_id'],
                            choice_id=choice_id,
                            value=term['value_str'],
                            )
                        )

        connection.execute(
            type_table.delete() \
            .where(type_table.c.id == selection_type_id)
            )

        transaction.commit()

    field_table.c.vocabulary_id.drop()
    selection_table.drop()
    vocabulary_term_table.drop()
    term_table.drop()
    vocabulary_table.drop()


def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.reflect(only=['field', 'type'] + value_table_names)
    field_table = metadata.tables['field']
    string_table = metadata.tables['string']
    type_table = metadata.tables['type']

    vocabulary_table.create()
    term_table.create()
    vocabulary_term_table.create()
    selection_table.create()

    # Add the column back to the field

    vocabulary_id_column = Column(
        'vocabulary_id',
        Integer,
        ForeignKey('vocabulary.id'),
        )

    vocabulary_id_column.create(field_table, index_name='ix_field_vobulary_id')

    connection = migrate_engine.connect()


    # Migrate the data from choice and associated columns back to
    # the selection table.

    with connection.begin() as transaction:

        result = connection.execute(
            type_table.insert() \
            .values(title=u'selection')
            )

        (selection_type_id,) = result.last_inserted_ids()

        # Only work on fields which are supposed to have vocabularies
        field_query = \
            select([field_table.c.id]) \
            .where(field_table.c.id.in_(
                select([choice_table.c.field_id]) \
                .correlate(None)
                ))

        for field_id, in connection.execute(field_query):
            result = connection.execute(
                vocabulary_table.insert() \
                .values(title='')
                )

            (vocabulary_id,) = result.last_inserted_ids()

            connection.execute(
                field_table.update() \
                .where(field_table.c.id == field_id) \
                .values(
                    vocabulary_id=vocabulary_id,
                    type_id=selection_type_id
                    )
                )

            # Get the choices to transfer into vocabulary/terms
            choice_query = \
                select([choice_table]) \
                .where(choice_table.c.field_id == field_id) \
                .order_by(choice_table.c.order.asc())

            for choice in connection.execute(choice_query):

                # Create the vocabulary/term associations

                result = connection.execute(term_table.insert().values(
                    title=choice['title'],
                    token=choice['name'],
                    value_str=choice['value'],
                    order=choice['order'],
                    ))

                (term_id,) = result.last_inserted_ids()

                result = connection.execute(
                    vocabulary_term_table.insert() \
                    .values(
                        vocabulary_id=vocabulary_id,
                        term_id=term_id,
                        )
                    )

                # Migrate available choice data back into the selection table

                value_query = \
                    select([string_table]) \
                    .where(string_table.c.choice_id == choice['id'])

                for value in connection.execute(value_query):
                    connection.execute(
                        selection_table.insert() \
                        .values(
                            instance_id=value['instance_id'],
                            attribute_id=value['attribute_id'],
                            value=term_id
                            )
                        )

        transaction.commit()

    # Remove associated columns and the field choice table.

    for value_name in value_table_names:
        metadata.tables[value_name].c.choice_id.drop()

    choice_table.drop()
