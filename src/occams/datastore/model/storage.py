""" Database Definitions
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm.collections import mapped_collection
from sqlalchemy.orm.collections import collection
from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.schema import Index
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Enum
from sqlalchemy.types import Numeric
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode
from sqlalchemy.orm import object_session
from zope.interface import implements

from occams.datastore.interfaces import IEntity
from occams.datastore.interfaces import IValue
from occams.datastore.model import Model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.metadata import buildModifiableConstraints
from occams.datastore.model.auditing import Auditable


ENTITY_STATE_NAMES = sorted([term.token for term in IEntity['state'].vocabulary])


def defaultCollectDate(context):
    """
    Callback for generating default collect date value.
    It will try to lookup the previous ``collect_date`` and give the
    date the entry is input by default if none is found.
    This method should not be called if one is supplied by the user.
    """
    entity_table = Entity.__table__
    name = context.current_parameters['name']
    collect_date = date.today()
    if name:
        result = context.connection.execute(
            select([entity_table.c.collect_date], (entity_table.c.name == name))
            .order_by(entity_table.c.create_date.desc())
            .limit(1)
            )
        previous = result.first()
        if previous:
            collect_date = previous.collect_date
    return collect_date


def cleanDataByState(entity):
    """
    """
    if entity.state == 'not-done':
        for name, attribute in entity.schema.attributes.items():
            if attribute.type == 'object':
                cleanDataByState(entity[name])
            else:
                del entity[name]


def entityBeforeFlush(session, flush_context, instances):
    """
    Session Event handler to update attribute checksums
    """
    attributes = lambda i: isinstance(i, Entity)
    for instance in filter(attributes, session.new):
        instance._checksum = cleanDataByState(instance)
    for instance in filter(attributes, session.dirty):
        instance._checksum = cleanDataByState(instance)


def registerEntityListener(session):
    """
    """
    event.listen(session, 'before_flush', entityBeforeFlush)


def unregisterEntityListenter(session):
    """
    """
    event.remove(session, 'before_flush', entityBeforeFlush)


class ValueDictionary(object):
    """
    """

    def __init__(self):
        self.data = dict()
        self.keyfunc = lambda item:  (item.entity, item.attribute)

    @collection.appender
    def append(self, item):
        key = self.keyfunc(item)
        if item.attribute.is_collection:
            self.data.setdefault(key, [])
            self.data[key].append(item)
        else:
            self.data[key] = item

    @collection.remover
    def remove(self, item):
        del self.data[self.keyfunc(item)]

    @collection.iterator
    def __iter__(self):
        return self.data.__iter__()


class Entity(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IEntity)

    schema_id = Column(Integer, nullable=False)

    schema = Relationship('Schema')

    state = Column(
        Enum(*ENTITY_STATE_NAMES, name='entity_state'),
        nullable=False,
        server_default=IEntity['state'].default
        )

    collect_date = Column(Date, nullable=False, default=defaultCollectDate)

    _string_values = Relationship('ValueString', collection_class=ValueDictionary)

    _integer_values = Relationship('ValueInteger', collection_class=ValueDictionary)

    _datetime_values = Relationship('ValueDatetime', collection_class=ValueDictionary)

    _decimal_values = Relationship('ValueDecimal', collection_class=ValueDictionary)

    _obect_values = Relationship(
        'ValueObject',
        primaryjoin='Entity.id == ValueObject._value',
        collection_class=ValueDictionary
        )

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint('schema_id', 'name'),
            Index('ix_%s_schema_id' % cls.__tablename__, 'schema_id'),
            Index('ix_%s_collect_date' % cls.__tablename__, 'collect_date'),
            )

    def _values(self, key):
        if key not in self.schema:
            raise KeyError
        type_ = self.schema[key].type
        if type_ in ('string', 'text'):
            result = self._string_values
        elif type_ in ('integer', 'boolean'):
            result = self._integer_values
        elif type_ in ('datetime', 'date'):
            result = self._datetime_values
        elif type_ == 'decimal':
            result = self._decimal_values
        elif type_ == 'object':
            result = self._object_values
        else:
            raise NotImplementedError
        return result

    def __getitem__(self, key):
        return self._values(key)[(self, self.schema[key])].value

    def __setitem__(self, key, value):
        valueKey = (self, self.schema[key])
        valueFactory = nameModelMap[self.schema[key].type]
        values = self._values[key]
        values.append(valueFactory(value=value))

    def __delitem__(self, key):
        del self.__map[key]

    def __contains__(self, key):
        return key in self.schema

    def keys(self):
        self.schema.keys()

    def values(self):
        return [prop.value for prop in self.__map.values()]

    def items(self):
        return [(key, prop.value) for key, prop in self.__map.items()]


def TypeMappingClass(className, tableName, valueType):
    """
    Helper method to generate value mappings
    """
    class _ValueBaseMixin(Referenceable, Modifiable, Auditable):
        implements(IValue)

        __tablename__ = None
        __valuetype__ = None

        @declared_attr
        def entity_id(cls):
            return Column(Integer, nullable=False)

        @declared_attr
        def entity(cls):
            return Relationship('Entity',
                primaryjoin='%s.entity_id == Entity.id' % cls.__name__)

        @declared_attr
        def attribute_id(cls):
            return Column(Integer, nullable=False)

        @declared_attr
        def attribute(cls):
            return Relationship('Attribute')

        @declared_attr
        def choice_id(cls):
            return Column(Integer)

        @declared_attr
        def choice(cls):
            return Relationship('Choice')

        @declared_attr
        def _value(cls):
            return Column('value', cls.__valuetype__)

        @property
        def value(self):
            type_ = self.attribute.type
            value = self._value
            if type_ == 'date':
                value = value.date()
            elif type_ == 'boolean':
                value = bool(value)
            elif type_ == 'object':
                session = object_session(self)
                if session:
                    value = session.query(Entity).get(self._value)
            return value

        @declared_attr
        def __table_args__(cls):
            constraints = buildModifiableConstraints(cls) + (
                ForeignKeyConstraint(
                    columns=['entity_id'],
                    refcolumns=['entity.id'],
                    name='fk_%s_entity_id' % cls.__tablename__,
                    ondelete='CASCADE',
                    ),
                ForeignKeyConstraint(
                    columns=['attribute_id'],
                    refcolumns=['attribute.id'],
                    name='fk_%s_attribute_id' % cls.__tablename__,
                    ondelete='CASCADE',
                    ),
                ForeignKeyConstraint(
                    columns=['choice_id'],
                    refcolumns=['choice.id'],
                    name='fk_%s_choice_id' % cls.__tablename__,
                    ondelete='CASCADE',
                    ),
                Index('ix_%s_entity_id' % cls.__tablename__, 'entity_id'),
                Index('ix_%s_attribute_id' % cls.__tablename__, 'attribute_id'),
                Index('ix_%s_choice_id' % cls.__tablename__, 'choice_id'),
                Index('ix_%s_value' % cls.__tablename__, 'value')
                )

            if cls.__tablename__ == 'object':
                constraints += (
                    ForeignKeyConstraint(
                        columns=['value'],
                        refcolumns=['entity.id'],
                        name='fk_%s_value' % cls.__tablename__,
                        ondelete='CASCADE'
                        ),
                    )

            return constraints

    return type(className, (Model, _ValueBaseMixin), dict(
        __tablename__=tableName,
        __valuetype__=valueType,
        ))


ValueDatetime = TypeMappingClass('ValueDatetime', 'datetime', DateTime)

ValueInteger = TypeMappingClass('ValueInteger', 'integer', Integer)

ValueDecimal = TypeMappingClass('ValueDecimal', 'decimal', Numeric)

ValueString = TypeMappingClass('ValueString', 'string', Unicode)

ValueObject = TypeMappingClass('ValueObject', 'object', Integer)

nameModelMap = dict(
    integer=ValueInteger,
    boolean=ValueInteger,
    string=ValueString,
    text=ValueString,
    decimal=ValueDecimal,
    date=ValueDatetime,
    datetime=ValueDatetime,
    object=ValueObject,
    )
