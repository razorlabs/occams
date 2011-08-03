from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from migrate import *


PY_NOW = datetime.now
SQL_NOW = text('CURRENT_TIMESTAMP')

SQL_FALSE = text('FALSE')

TYPE_NAMES = sorted((
    u'integer',
    u'string', u'text' ,
    u'boolean',
    u'decimal',
    u'date', u'datetime', u'time',
    u'object',
    ))


Model = declarative_base()

class Field(Model):
    __tablename__ = 'field'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode, nullable=False)
    description = Column(Unicode)
    documentation = Column(Unicode)
    type_id = Column(
        Integer,
        ForeignKey('type.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        )
    schema_id = Column(Integer, ForeignKey('schema.id', ondelete='SET NULL'), index=True)
    default = Column(Unicode)
    is_list = Column(Boolean, nullable=False, default=False)
    is_readonly = Column(Boolean, nullable=False, default=False)
    is_searchable = Column(Boolean, nullable=False, default=False)
    is_required = Column(Boolean, nullable=False, default=False)
    is_inline_image = Column(Boolean)
    is_repeatable = Column(Boolean, nullable=False, default=False)
    minimum = Column(Integer)
    maximum = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    url = Column(Unicode)
    directive_widget = Column(Unicode)
    directive_omitted = Column(Boolean)
    directive_no_ommit = Column(Unicode)
    directive_mode = Column(Unicode)
    directive_before = Column(Unicode)
    directive_after = Column(Unicode)
    directive_read = Column(Unicode)
    directive_write = Column(Unicode)
    create_date = Column(DateTime, nullable=False, default=PY_NOW)
    modify_date = Column(DateTime, nullable=False, default=PY_NOW, onupdate=PY_NOW)


class Type(Model):
    __tablename__ = 'type'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode, nullable=False, unique=True)
    description = Column(Text)


def upgrade(migrate_engine):
    """ Removes the field table and a lot of its unnecessary values.
        Also converts the type of an attribute to an enum.0
    """
    metadata = MetaData(bind=migrate_engine)
    connection = metadata.bind.connect()

    attribute_type = Enum(*TYPE_NAMES, name='attribute_type')
    
    new_attribute_columns = (
        Column('title', Unicode),
        Column('description', Unicode),
        Column('type', attribute_type),
        Column('is_collection', Boolean, nullable=False, server_default=SQL_FALSE),
        Column('is_readonly', Boolean, nullable=False, server_default=SQL_FALSE),
        Column('is_required', Boolean, nullable=False, server_default=SQL_FALSE),
        Column('is_inline_object', Boolean),
        Column('object_schema_id', Integer, ForeignKey('schema.id', ondelete='SET NULL')),
        Column('url_template', String),
        Column('min', Integer),
        Column('max', Integer),
        Column('default', Unicode),
        Column('validator', Unicode),
        Column('widget', String),
        Column('order', Integer),
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )


    attribute_table = Table('attribute', metadata, autoload=True)
    field_table = Table('field', metadata, autoload=True)
    type_table = Table('type', metadata, autoload=True)

    # Rename columns that will be moved or deleted
    attribute_table.c.name.alter(type=String)
    attribute_table.c.order.alter(name='old_order')
    attribute_table.c.create_date.alter(name='old_create_date')

    attribute_type.create(metadata.bind)

    create_column = lambda c: c.create(attribute_table)
    map(create_column, new_attribute_columns)

    Index('ix_attribute_name', attribute_table.c.name).create()
    Index('ix_attribute_object_schema_id', attribute_table.c.object_schema_id).create()

    Index('ix_attribute_remove_date', attribute_table.c.remove_date).create()

    attribute_table.deregister()
    attribute_table = Table('attribute', metadata, autoload=True)

    # Since types are now ENUM values, we need to map them
    type_result = connection.execute(select([type_table.c.id, type_table.c.title]))
    type_ids = dict()

    for id, name in type_result:
        if name == 'real':
            name = 'decimal'
        type_ids[id] = name

    # Transfer values from field table
    with connection.begin() as transaction:
        for field in connection.execute(select([field_table])):
            connection.execute(
                attribute_table.update() \
                .where(attribute_table.c.field_id == field.id) \
                .values(
                    title=field.title,
                    description=field.description,
                    type=type_ids[field.type_id],
                    object_schema_id=field.schema_id,
                    url_template=field.url,
                    is_collection=field.is_list,
                    is_readonly=field.is_readonly,
                    is_required=field.is_required,
                    min=field.minimum,
                    max=field.maximum,
                    widget=field.directive_widget,
                    default=field.default,
                    order=attribute_table.c.old_order,
                    create_date=field.create_date,
                    modify_date=field.modify_date,
                    )
                )

        transaction.commit()

    attribute_table.c.field_id.drop()
    attribute_table.c.old_order.drop()
    attribute_table.c.old_create_date.drop()

    attribute_table.c.title.alter(nullable=False)
    attribute_table.c.type.alter(nullable=False)
    attribute_table.c.order.alter(nullable=False)

    field_table.drop()
    type_table.drop()

    UniqueConstraint('schema_id', 'name', table=attribute_table).drop()


def downgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine)
    connection = metadata.bind.connect()

    attribute_type = Enum(*TYPE_NAMES, name='attribute_type')
    
    new_attribute_columns = (
        Column('title', Unicode),
        Column('description', Unicode),
        Column('type', attribute_type),
        Column('is_collection', Boolean, nullable=False, server_default=SQL_FALSE),
        Column('is_readonly', Boolean, nullable=False, server_default=SQL_FALSE),
        Column('is_required', Boolean, nullable=False, server_default=SQL_FALSE),
        Column('is_inline_object', Boolean),
        Column('object_schema_id', Integer, ForeignKey('schema.id', ondelete='SET NULL')),
        Column('url_template', String),
        Column('min', Integer),
        Column('max', Integer),
        Column('default', Unicode),
        Column('validator', Unicode),
        Column('widget', String),
        Column('order', Integer),
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )


    type_table = Type.__table__.tometadata(metadata)
    field_table = Field.__table__.tometadata(metadata)
    attribute_table = Table('attribute', metadata, autoload=True)

    type_table.create()
    field_table.create()

    Index('ix_attribute_name', attribute_table.c.name).drop()

    field_id_column = Column('field_id', Integer, ForeignKey('field.id', ondelete='CASCADE'),)
    field_id_column.create(attribute_table, index_name='ix_attribute_field_id')

    type_ids = dict()

    for type_ in attribute_table.c.type.type.enums:
        if type_ != 'object':
            if type_ == 'decimal':
                type_name = 'real'
            else:
                type_name = type_
            result = connection.execute(type_table.insert().values(title=type_name))
            (type_id,) = result.last_inserted_ids()
            type_ids[type_] = type_id


    with connection.begin() as transaction:
        for attribute in connection.execute(select([attribute_table])):
            result = connection.execute(
                field_table.insert() \
                .values(
                    title=attribute.title,
                    description=attribute.description,
                    type_id=type_ids[attribute.type],
                    schema_id=attribute.object_schema_id,
                    url=attribute.url_template,
                    is_list=attribute.is_collection,
                    is_readonly=attribute.is_readonly,
                    is_required=attribute.is_required,
                    minimum=attribute.min,
                    maximum=attribute.max,
                    directive_widget=attribute.widget,
                    default=attribute.default,
                    order=attribute.order,
                    create_date=attribute.create_date,
                    modify_date=attribute.modify_date
                    )
                )

            (field_id,) = result.last_inserted_ids()

            connection.execute(
                attribute_table.update() \
                .where(attribute_table.c.id == attribute.id) \
                .values(field_id=field_id)
                )

        transaction.commit()

    attribute_table.c.field_id.alter(nullable=False)

    for column in new_attribute_columns:
        if column.name not in ('id', 'schema_id', 'field_id', 'name', 'order', 'create_date'):
            getattr(attribute_table.c, column.name).drop()

    attribute_type.drop(bind=metadata.bind)

    UniqueConstraint('schema_id', 'name', table=attribute_table).create()
