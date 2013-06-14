""" Database Definitions
"""

from decimal import Decimal
from datetime import date
from datetime import datetime
import re

from sqlalchemy.orm.collections import collection
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import event
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import backref
from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.schema import Index
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Boolean
from sqlalchemy.types import Enum
from sqlalchemy.types import LargeBinary
from sqlalchemy.types import Numeric
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode
from sqlalchemy.types import UnicodeText
from sqlalchemy.types import String
from sqlalchemy.orm import object_session
from zope.interface import implements

from occams.datastore.interfaces import IEntity
from occams.datastore.interfaces import IValue
from occams.datastore.interfaces import IState
from occams.datastore.interfaces import InvalidEntitySchemaError
from occams.datastore.interfaces import ConstraintError
from occams.datastore.model import DataStoreModel as Model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.auditing import Auditable
from occams.datastore.model.schema import Schema
from occams.datastore.model.schema import Attribute
from occams.datastore.model.schema import Choice



def enforceSchemaState(entity):
    """
    Makes sure an entity cannot be added to an unpublished schema
    """
    if entity.schema.state != 'published':
        raise InvalidEntitySchemaError(entity.schema.name, entity.schema.state)


class Context(Model, AutoNamed, Referenceable, Modifiable, Auditable):

    entity_id = Column(Integer, nullable=False)

    # Discriminator column for the keys and associations
    external = Column(String, nullable=False)

    @classmethod
    def creator(cls, external):
        """
        Provide a 'creator' function to use with the association proxy.
        """

        return lambda entity: Context(
            entity=entity,
            external=external,
            )

    key = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['entity_id'],
                refcolumns=['entity.id'],
                name='fk_%s_entity_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint('entity_id', 'external', 'key'),
            )


class GroupedCollection(object):
    u"""
    Collects relationship values into a dictionary grouped by a discriminator
    """

    def __init__(self, keyfunc):
        self._keyfunc = keyfunc
        self._groups = dict()

    @collection.appender
    def _append(self, value):
        self._groups.setdefault(self._keyfunc(value), []).append(value)

    def __setitem__(self, key, value):
        self._append(value)

    def __getitem__(self, key):
        return tuple(value for value in self._groups.get(key, []))

    def __delitem__(self, key):
        if key in self._groups:
            map(self._remove, self[key])

    def __contains__(self, key):
        return key in self._groups

    @collection.remover
    def _remove(self, value):
        self._groups[self._keyfunc(value)].remove(value)

    @collection.iterator
    def _iterator(self):
        for group in self._groups.itervalues():
            for value in group:
                yield value

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._groups)


def grouped_collection(keyfunc):
    return lambda: GroupedCollection(keyfunc)


class State(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IState)

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('name'),)


class Entity(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IEntity)

    schema_id = Column(Integer, nullable=False)

    schema = Relationship(Schema)

    contexts = Relationship(
        Context,
        cascade='all, delete-orphan',
        backref=backref(
            name='entity',
            )
        )

    state_id = Column(Integer)

    state = Relationship(
        State,
        backref=backref(
            name='entities',
            lazy='dynamic'))

    is_null = Column(Boolean, nullable=False, server_default=True)

    collect_date = Column(Date, nullable=False, default=date.today)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['state.id'],
                name='fk_%s_state_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint('schema_id', 'name'),
            Index('ix_%s_schema_id' % cls.__tablename__, 'schema_id'),
            Index('ix_%s_state_id' % cls.__tablename__, 'state_id'),
            Index('ix_%s_collect_date' % cls.__tablename__, 'collect_date'),
            )

    def _getCollector(self, key):
        type_ = self.schema[key].type
        if type_ == 'string':
            return self._string_values
        elif type_ == 'text':
            return self._text_values
        elif type_ in ('integer', 'boolean'):
            return self._integer_values
        elif type_ in ('datetime', 'date'):
            return self._datetime_values
        elif type_ == 'decimal':
            return self._decimal_values
        elif type_ == 'object':
            return self._object_values
        elif type_ == 'blob':
            return self._blob_values
        else: # pragma: no cover
            # Extreme edge case that is actually a programming error
            raise NotImplementedError(type_)

    def __getitem__(self, key):
        collector = self._getCollector(key)
        attribute = self.schema[key]

        def convert(container):
            if container.value is None:
                value = None
            elif container.attribute.type == 'date' and isinstance(container.value, datetime):
                # Sometimes it's converted to datetime and so we need to convert it back
                value = container.value.date()
            elif container.attribute.type == 'boolean':
                value = bool(container.value)
            else:
                value = container.value
            return value

        if attribute.is_collection:
            value = [convert(v) for v in iter(collector[attribute.name])]
        else:
            try:
                wrappedValue = collector[attribute.name][0]
            except IndexError:
                value = None
            else:
                value = convert(wrappedValue)
        return value

    def __setitem__(self, key, value):
        collector = self._getCollector(key)
        attribute = self.schema[key]
        wrapperFactory = nameModelMap[attribute.type]

        # Helper method for getting the appropriate parameters for an attribute/value
        params = lambda a, v: dict(zip(('attribute', 'value'), (a, v)))

        # Helper methot to add an item to the value collector
        collect = lambda v: collector.__setitem__(attribute.name, wrapperFactory(**params(attribute, v)))

        def convert(value, type_):
            if value is None:
                converted = None
            elif type_ == 'boolean':
                converted = int(value)
            else:
                converted = value
            return converted

        if attribute.is_collection:
            # don't even bother getting a diff and updating, just create a new list
            del self[key]
            map(collect, map(lambda v: convert(v, attribute.type), value))
        else:
            # For scalars, we're only dealing with one value, so it's OK to
            # try and update it
            convertedValue = convert(value, attribute.type)
            value_entries = collector[key]
            if value_entries:
                value_entries[0].value = convertedValue
            else:
                collect(convertedValue)

    def __delitem__(self, key):
        collector = self._getCollector(key)
        del collector[key]

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        for key in self.schema.iterkeys():
            yield (key, self[key])


class HasEntities(object):
    """
    Mixin class to allow other models to associate with entities using a
    central association class (i.e. ``Context``)
    """

    @declared_attr
    def contexts(cls):
        """
        Relationship to the context mapping class.
        If you want to be forwared to entities, use ``entities`` instead.
        """
        name = cls.__tablename__

        cls.entities = association_proxy(
            'contexts', 'entity',
            creator=Context.creator(name)
            )

        return Relationship(
            Context,
            primaryjoin='(%s.id == Context.key) & (Context.external == "%s")' % (cls.__name__, name),
            foreign_keys=[Context.key, Context.external],
            cascade='all, delete-orphan',
            collection_class=set,
            backref=backref(
                '%s_parent' % name,
                uselist=False
                )
            )


def TypeMappingClass(className, tableName, valueType, index=True):
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
            return Relationship(
                Entity,
                primaryjoin='%s.entity_id == Entity.id' % cls.__name__,
                backref=backref(
                    name='_%s_values' % cls.__tablename__,
                    collection_class=grouped_collection(lambda v: v.attribute.name),
                    cascade='all, delete-orphan',
                    )
                )

        @declared_attr
        def attribute_id(cls):
            return Column(Integer, nullable=False)

        @declared_attr
        def attribute(cls):
            return Relationship(Attribute)

        @declared_attr
        def choice_id(cls):
            return Column(Integer)

        @declared_attr
        def choice(cls):
            return Relationship(Choice)

        @declared_attr
        def _value(cls):
            return Column('value', cls.__valuetype__)

        @declared_attr
        def __table_args__(cls):
            constraints = (
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

    class_ = type(className, (Model, _ValueBaseMixin), dict(
        __tablename__=tableName,
        __valuetype__=valueType,
        ))

    if index:
        Index('ix_%s_value' % tableName, class_._value)

    return class_


ValueDatetime = TypeMappingClass('ValueDatetime', 'datetime', DateTime)

ValueInteger = TypeMappingClass('ValueInteger', 'integer', Integer)

ValueDecimal = TypeMappingClass('ValueDecimal', 'decimal', Numeric)

ValueString = TypeMappingClass('ValueString', 'string', Unicode)

ValueText = TypeMappingClass('ValueText', 'text', UnicodeText, index=False)

ValueObject = TypeMappingClass('ValueObject', 'object', Integer)

ValueBlob = TypeMappingClass('ValueBlob', 'blob', LargeBinary, index=False)

# Specify how the ``value`` properties behave, pretty much they're synonymns
# of the ``_value`` property, except for objects, which behave as relationships
valueProperty = hybrid_property(lambda self: self._value, lambda self, value: setattr(self, '_value', value))
ValueDatetime.value = valueProperty
ValueInteger.value = valueProperty
ValueDecimal.value = valueProperty
ValueString.value = valueProperty
ValueText.value = valueProperty
ValueObject.value = Relationship(Entity, primaryjoin='Entity.id == ValueObject._value')
ValueBlob.value = valueProperty


def validateValue(target, value, oldvalue, initiator):
    """
    Attempts to make sure that valid values are set to an entity
    """
    attribute = target.attribute

    if attribute is None:
        raise ConstraintError('No attribute assigned for value: %s' % value)

    # Don't check None values, as the user may want to create empty/placeholder
    # scheamta
    if value is None:
        return

    def compareable(type_, check, interpreted):
        """
        Local helper function to convert the check expression and target value
        into a equally comparable values
        """
        if type_ in ('string', 'text'):
            interpreted = len(value)
        elif type_ in ('integer'):
            pass
        elif type_ in ('decimal'):
            check = Decimal(check)
        elif type_ in ('date'):
            check = date.fromtimestamp(check)
        elif type_ in ('datetime'):
            check = datetime.fromtimestamp(check)
        else:
            raise NotImplementedError('Cannot coerce limit for type: %s' % type_)
        return check, interpreted

    if attribute.value_min is not None:
        check, interpreted = compareable(attribute.type, attribute.value_min, value)

        if interpreted < check:
            raise ConstraintError(attribute.schema.name, attribute.name, check, '<', interpreted, value)

    if attribute.value_max is not None:
        check, interpreted = compareable(attribute.type, attribute.value_max, value)

        if interpreted > check:
            raise ConstraintError(attribute.schema.name, attribute.name, check, '>', interpreted, value)

    # TODO: collections

    if attribute.validator is not None and not re.match(attribute.validator, str(value)):
        raise ConstraintError(attribute.schema.name, attribute.name, attribute.validator, value)

    if attribute.choices:
        found = None
        for choice in attribute.choices:
            if choice.value == value:
                found = choice
                break
        if not found:
            raise ConstraintError(attribute.schema.name, attribute.name, [c.value for c in attribute.choices], value)

        target.choice = choice


event.listen(ValueDatetime.value, 'set', validateValue)
event.listen(ValueInteger.value, 'set', validateValue)
event.listen(ValueDecimal.value, 'set', validateValue)
event.listen(ValueString.value, 'set', validateValue)
event.listen(ValueText.value, 'set', validateValue)
event.listen(ValueObject.value, 'set', validateValue)
event.listen(ValueBlob.value, 'set', validateValue)


# Where the types are stored
nameModelMap = dict(
    integer=ValueInteger,
    boolean=ValueInteger,
    string=ValueString,
    text=ValueText,
    decimal=ValueDecimal,
    date=ValueDatetime,
    datetime=ValueDatetime,
    object=ValueObject,
    blob=ValueBlob,
    )

