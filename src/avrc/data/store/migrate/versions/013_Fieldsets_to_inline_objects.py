import re
import hashlib
from random import random
from time import time

from sqlalchemy.sql.functions import coalesce
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from migrate import *


Model = declarative_base()


fieldset_fieldsetitem_table = Table('fieldset_fieldsetitem', Model.metadata,
    Column('fieldset_id', Integer, ForeignKey('fieldset.id', ondelete='CASCADE')),
    Column('item_id', Integer, ForeignKey('fieldsetitem.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('fieldset_id', 'item_id')
    )

schema_fieldset_table = Table('schema_fieldset', Model.metadata,
    Column('schema_id', Integer, ForeignKey('schema.id', ondelete='CASCADE')),
    Column('fieldset_id', Integer, ForeignKey('fieldset.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('schema_id', 'fieldset_id')
    )


class FieldsetItem(Model):
    __tablename__ = 'fieldsetitem'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    order = Column(Integer, nullable=False, default=1)


class Fieldset(Model):
    __tablename__ = 'fieldset'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    label = Column(Unicode, nullable=False)
    description = Column(Unicode)
    order = Column(Integer, nullable=False, default=1)


value_table_names = ['datetime', 'integer', 'decimal', 'string']


value_table_map = dict(
    datetime='datetime',
    time='datetime',
    date='datetime',
    boolean='integer',
    integer='integer',
    decimal='decimal',
    string='string',
    text='string',
    )

def _is_required_fieldset(connection, metadata, fieldset_id):
    """ Helper method to determine whether a fieldset has required fields
    """
    schema_table = metadata.tables['schema']
    fieldset_table = metadata.tables['fieldset']
    attribute_table = metadata.tables['attribute']
    fieldsetitem_table = metadata.tables['fieldsetitem']

    result = connection.execute(
        select([
            func.count(attribute_table.c.id).label('num_required')
            ]) \
        .select_from(
            fieldset_table \
            .join(
                schema_fieldset_table,
                schema_fieldset_table.c.fieldset_id == fieldset_table.c.id
                ) \
            .join(
                schema_table,
                schema_table.c.id == schema_fieldset_table.c.schema_id
                ) \
            .join(
                fieldset_fieldsetitem_table,
                fieldset_fieldsetitem_table.c.fieldset_id == fieldset_table.c.id
                ) \
            .join(
                fieldsetitem_table,
                fieldsetitem_table.c.id == fieldset_fieldsetitem_table.c.item_id,
                ) \
            .join(
                attribute_table,
                and_(
                    attribute_table.c.schema_id == schema_table.c.id,
                    attribute_table.c.name == fieldsetitem_table.c.name
                    )
                )\
            )\
        .where(
            and_(
                fieldset_table.c.id == fieldset_id,
                attribute_table.c.is_required == True
                )
            )
        )

    return result.first().num_required > 0

def _migrate_fieldsets(connection, metadata):
    """ Converts all the field sets into sub object classes
        Query the class' available field sets, only retrieve those that ACTUALLY
        contain items which reference the attributes
    """
    schema_table = metadata.tables['schema']
    fieldset_table = metadata.tables['fieldset']
    attribute_table = metadata.tables['attribute']
    fieldsetitem_table = metadata.tables['fieldsetitem']

    fieldsets = connection.execute(
        select([
            schema_table.c.id.label('schema_id'),
            schema_table.c.name.label('schema_name'),
            fieldset_table.c.id,
            fieldset_table.c.name,
            fieldset_table.c.label,
            fieldset_table.c.description,
            fieldset_table.c.order,
            ]) \
        .distinct()\
        .select_from(
            fieldset_table \
            .join(
                schema_fieldset_table,
                schema_fieldset_table.c.fieldset_id == fieldset_table.c.id
                ) \
            .join(
                schema_table,
                schema_table.c.id == schema_fieldset_table.c.schema_id
                ) \
            .join(
                fieldset_fieldsetitem_table,
                fieldset_fieldsetitem_table.c.fieldset_id == fieldset_table.c.id
                ) \
            .join(
                fieldsetitem_table,
                fieldsetitem_table.c.id == fieldset_fieldsetitem_table.c.item_id,
                ) \
            .join(
                attribute_table,
                and_(
                    attribute_table.c.schema_id == schema_table.c.id,
                    attribute_table.c.name == fieldsetitem_table.c.name
                    )
                )\
            )\
        .order_by(
            schema_table.c.id.asc(),
            fieldset_table.c.order.asc(),
            fieldset_table.c.id.asc(),
            )
        )

    for fieldset in fieldsets:
        new_schema_title = u'%s %s' % (fieldset.schema_name, fieldset.label)
        new_schema_name = re.sub(r'\W+', '_', u''.join(new_schema_title.split()))

        result = connection.execute(
            schema_table.insert() \
            .values(
                name=new_schema_name,
                title=new_schema_title,
                description=u'Auto generated from field set.',
                )
            )

        (new_schema_id,) = result.inserted_primary_key

        is_required = _is_required_fieldset(connection, metadata, fieldset.id)

        connection.execute(
            attribute_table.update() \
            .where(
                attribute_table.c.id.in_(
                    select([attribute_table.c.id]) \
                    .select_from(
                        fieldset_fieldsetitem_table \
                        .join(
                            fieldsetitem_table,
                            fieldsetitem_table.c.id == fieldset_fieldsetitem_table.c.item_id
                            ) \
                        .join (
                            attribute_table,
                            attribute_table.c.name == fieldsetitem_table.c.name
                            ) \
                        )\
                    .where(
                        and_(
                            fieldset_fieldsetitem_table.c.fieldset_id == fieldset.id,
                            attribute_table.c.schema_id == fieldset.schema_id
                            )
                        )
                    ) \
                )\
            .values(schema_id=new_schema_id)
            )

        connection.execute(
            attribute_table.insert() \
            .values(
                schema_id=fieldset.schema_id,
                name=fieldset.name,
                title=fieldset.label,
                description=fieldset.description,
                type='object',
                is_required=is_required,
                is_inline_object=True,
                object_schema_id=new_schema_id,
                order=999999,
                )
            )

def _migrate_data(connection, metadata):
    """ Migrates all EAV data to correspond to the newly created sub object
        schemaes.
    """
    entity_table = metadata.tables['entity']
    schema_table = metadata.tables['schema']
    object_table = metadata.tables['object']
    attribute_table = metadata.tables['attribute']

    subqueries = []

    for value_table_name in value_table_names:
        table = metadata.tables[value_table_name]
        subqueries.append(select([table.c.entity_id, table.c.attribute_id]))

    value_table = union(*subqueries).alias('value')

    sub_attribute_table = attribute_table.alias('sub_attribtue')
    main_attribute_table = attribute_table.alias('main_attribute')

    main_schema_table = schema_table.alias('main_schema')
    sub_schema_table = schema_table.alias('sub_schema')

    # Get the sub-object values
    query = (
        select([
            entity_table.c.id.label('main_entity_id'),
            entity_table.c.schema_id.label('main_schema_id'),
            main_attribute_table.c.id.label('main_attribute_id'),
            sub_schema_table.c.id.label('sub_schema_id'),
            sub_schema_table.c.name.label('sub_schema_name'),
            sub_schema_table.c.title.label('sub_schema_title'),
            ])
        .distinct()
        .select_from(
            entity_table
            .join(
                main_schema_table,
                (entity_table.c.schema_id == main_schema_table.c.id)
                )
            .join(
                main_attribute_table,
                (main_schema_table.c.id == main_attribute_table.c.schema_id)
                )
            .join(
                sub_schema_table,
                (main_attribute_table.c.object_schema_id == sub_schema_table.c.id)
                )
            .join(
                sub_attribute_table,
                (sub_schema_table.c.id == sub_attribute_table.c.schema_id)
                )
            .join(
                value_table,
                    and_(
                        (sub_attribute_table.c.id == value_table.c.attribute_id),
                        (entity_table.c.id == value_table.c.entity_id)
                        )
                )
            )
        )

    # List of objects to be created
    entries = connection.execute(query)
    total = entries.rowcount
    count = 0

    for entry in entries:
        count += 1
        print '%s of %s' % (count, total)

        result = connection.execute(
            entity_table.insert()
            .values(
                schema_id=entry.sub_schema_id,
                name=hashlib.sha1(str(random()) + str(time())).hexdigest(),
                title='Unnamed object: %s' % entry.sub_schema_name,
                )
            )

        (sub_entity_id,) = result.inserted_primary_key

        connection.execute(
            entity_table.update() \
            .where(entity_table.c.id == sub_entity_id) \
            .values(
                name='%s-%s' % (entry.sub_schema_name, sub_entity_id),
                title='%s - %s' % (entry.sub_schema_title, sub_entity_id),
                )
            )

        connection.execute(
            object_table.insert()
            .values(
                entity_id=entry.main_entity_id,
                attribute_id=entry.main_attribute_id,
                value=sub_entity_id,
                )
            )

        for value_table_name in value_table_names:
            table = metadata.tables[value_table_name]
            connection.execute(
                table.update()
                .where(
                    and_(
                        table.c.entity_id == entry.main_entity_id,
                        table.c.attribute_id.in_(
                            select([attribute_table.c.id])
                            .where(attribute_table.c.schema_id == entry.sub_schema_id)
                            )
                         )
                    )
                .values(entity_id=sub_entity_id)
                )


def _order_attributes(connection, metadata):
    """ Helper method to order the attributes giving priority to the field set
        item ordering.
    """
    attribute_table = metadata.tables['attribute']
    fieldset_table = metadata.tables['fieldset']

    fieldset_subtable = \
        select([
            schema_fieldset_table.c.schema_id.label('schema_id'),
            fieldset_table.c.id,
            fieldset_table.c.name,
            fieldset_table.c.order
        ]) \
        .select_from(
            fieldset_table \
            .join(
                schema_fieldset_table,
                 schema_fieldset_table.c.fieldset_id == fieldset_table.c.id
                )
            ).correlate(None).alias()

    order_column = coalesce(fieldset_subtable.c.order, text('1'))
    id_column = coalesce(fieldset_subtable.c.id, text('1'))

    attributes = connection.execute(
        select([
            attribute_table.c.id,
            attribute_table.c.schema_id,
            attribute_table.c.name,
            attribute_table.c.order,
            order_column,
            id_column
            ]) \
        .select_from(
            attribute_table \
            .outerjoin(
                fieldset_subtable,
                and_(
                    fieldset_subtable.c.schema_id == attribute_table.c.schema_id,
                    fieldset_subtable.c.name == attribute_table.c.name,
                    )
                ) \
            )\
        .order_by(
            attribute_table.c.schema_id.asc(),
            order_column.asc(),
            id_column.asc(),
            attribute_table.c.order.asc()
            )
        )

    last_schema_id = None
    counter = None

    for attribute in attributes:
        if last_schema_id is None or attribute.schema_id != last_schema_id:
            last_schema_id = attribute.schema_id
            counter = 1
        else:
            counter += 1

        connection.execute(
            attribute_table.update() \
            .where(attribute_table.c.id == attribute.id)\
            .values(order=counter)
            )


def upgrade(migrate_engine):
    """ Converts the fieldset tables to inline objects.
        The reason for the complexity in upgrading from the fieldset tables is
        to take into account legacy data in a time when this module wasn't
        correctly ordering attributes (all had a default of 1). Therefore, great
        care needs to be taken when querying attribute and fieldsets to get the
        proper order at creation time.
        
        When this upgrade step is complete, this module will now properly
        support nested objects (which will still be rendered as fieldsets, i.e.
        sub forms)
    """
    work_tables = ['schema', 'entity', 'object', 'attribute']
    Model.metadata.bind = migrate_engine
    Model.metadata.reflect(only=value_table_names + work_tables)
    connection = Model.metadata.bind.connect()

    with connection.begin() as transaction:
        args = (connection, Model.metadata)
        _migrate_fieldsets(*args)
        _migrate_data(*args)
        _order_attributes(*args)
        transaction.commit()

    fieldset_fieldsetitem_table.drop()
    schema_fieldset_table.drop()
    FieldsetItem.__table__.drop()
    Fieldset.__table__.drop()


def downgrade(migrate_engine):
    """
    """
    Model.metadata.bind = migrate_engine
    Model.metadata.reflect(only=value_table_names)
    connection = Model.metadata.bind.connect()

    schema_table = Table('schema', Model.metadata, autoload=True)
    entity_table = Table('entity', Model.metadata, autoload=True)
    object_table = Table('object', Model.metadata, autoload=True)
    attribute_table = Table('attribute', Model.metadata, autoload=True)
    fieldset_table = Fieldset.__table__
    fieldsetitem_table = FieldsetItem.__table__

    fieldset_table.create()
    fieldsetitem_table.create()
    fieldset_fieldsetitem_table.create()
    schema_fieldset_table.create()

    with connection.begin() as transaction:
        attributes = connection.execute(
            select([attribute_table]) \
            .order_by(
                attribute_table.c.schema_id.asc(),
                attribute_table.c.order.asc()
                )
            )

        delete_schema_ids = []

        counter = None
        last_schema_id = None

        for attribute in attributes:

            if last_schema_id is None or attribute.schema_id != last_schema_id:
                last_schema_id = attribute.schema_id
                counter = 1
            else:
                counter += 1

            if attribute.type != 'object':
                continue

            delete_schema_ids.append(attribute.object_schema_id)

            result = connection.execute(
                fieldset_table.insert() \
                .values(
                    name=attribute.name,
                    label=attribute.title,
                    description=attribute.description,
                    order=attribute.order
                    )
                )

            (fieldset_id,) = result.inserted_primary_key

            connection.execute(
                schema_fieldset_table.insert()\
                .values(
                    schema_id=attribute.schema_id,
                    fieldset_id=fieldset_id,
                    )
                )

            object_attributes = connection.execute(
                select([attribute_table]) \
                .where(attribute_table.c.schema_id == attribute.object_schema_id) \
                .order_by(attribute_table.c.order.asc())
                )

            for object_attribute in object_attributes:
                result = connection.execute(
                    fieldsetitem_table.insert() \
                    .values(
                        name=object_attribute.name,
                        order=object_attribute.order,
                        )
                    )

                (fieldsetitem_id,) = result.inserted_primary_key

                connection.execute(
                    fieldset_fieldsetitem_table.insert() \
                    .values(
                        fieldset_id=fieldset_id,
                        item_id=fieldsetitem_id,
                        )
                    )

                connection.execute(
                    attribute_table.update() \
                    .where(attribute_table.c.id == object_attribute.id)
                    .values(
                        schema_id=attribute.schema_id,
                        order=counter
                        )
                    )

                counter += 1

            objects = connection.execute(select([object_table]))

            for object_ in objects:
                for value_table_name in value_table_names:
                    table = Model.metadata.tables[value_table_name]

                    connection.execute(
                        table.update() \
                        .where(table.c.entity_id == object_.value)
                        .values(entity_id=object_.entity_id)
                        )

            connection.execute(object_table.delete())

            connection.execute(
                attribute_table.delete() \
                .where(attribute_table.c.id == attribute.id)
                )

        connection.execute(
            schema_table.delete() \
            .where(schema_table.c.id.in_(delete_schema_ids))
            )

        transaction.commit()
