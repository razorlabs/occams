"""
Storage models
"""

from decimal import Decimal
from datetime import date
from datetime import datetime
import re

from sqlalchemy import (
    event,
    text,
    Column,
    ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint,
    Date, DateTime, Boolean, LargeBinary, Numeric, Integer,
    Unicode, UnicodeText, String)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import collection
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from occams.datastore.exc import ConstraintError, InvalidEntitySchemaError
from occams.datastore.models import DataStoreModel as Model
from occams.datastore.models.auditing import Auditable
from occams.datastore.models.metadata import (
    Referenceable, Describeable, Modifiable)
from occams.datastore.models.schema import Schema, Attribute, Choice


def enforceSchemaState(entity):
    """
    Makes sure an entity cannot be added to an unpublished schema
    """
    if not entity.schema.publish_date or entity.schema.retract_date:
        raise InvalidEntitySchemaError(entity.schema.name, entity.schema.state)


class Context(Model, Referenceable, Modifiable, Auditable):

    __tablename__ = 'context'

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
            external=external,)

    key = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['entity_id'],
                refcolumns=['entity.id'],
                name='fk_%s_entity_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('entity_id', 'external', 'key'))


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
            list(map(self._remove, self[key]))

    def __contains__(self, key):
        return key in self._groups

    @collection.remover
    def _remove(self, value):
        self._groups[self._keyfunc(value)].remove(value)

    @collection.iterator
    def _iterator(self):
        for group in self._groups.values():
            for value in group:
                yield value

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._groups)


def grouped_collection(keyfunc):
    return lambda: GroupedCollection(keyfunc)


class State(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    An entity state to keep track of the entity's progress through some
    externally defined work flow.
    """

    __tablename__ = 'state'

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('name'),)


class Entity(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    An object that describes how an EAV object is generated.
    """

    __tablename__ = 'entity'

    schema_id = Column(Integer, nullable=False)

    schema = relationship(
        Schema,
        doc='The scheme the object will provide once generated.')

    contexts = relationship(
        Context,
        cascade='all, delete-orphan',
        backref=backref(
            name='entity'))

    state_id = Column(Integer)

    state = relationship(
        State,
        backref=backref(
            name='entities',
            lazy='dynamic'),
        doc='The current workflow state')

    is_null = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text('FALSE'),
        doc='Flag to indicate if the entity is intentionally blank')

    collect_date = Column(
        Date,
        nullable=False,
        default=date.today,
        doc='The date that the information was physically collected')

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['state.id'],
                name='fk_%s_state_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('schema_id', 'name'),
            Index('ix_%s_schema_id' % cls.__tablename__, 'schema_id'),
            Index('ix_%s_state_id' % cls.__tablename__, 'state_id'),
            Index('ix_%s_collect_date' % cls.__tablename__, 'collect_date'))

    def _getCollector(self, key):
        type_ = self.schema[key].type
        if type_ == 'boolean':
            type_ = 'integer'
        elif type_ == 'date':
            type_ = 'datetime'
        try:
            return getattr(self, '_%s_values' % type_)
        except AttributeError:  # pragma: no cover
            # Extreme edge case that is actually a programming error
            raise NotImplementedError(type_)

    def __getitem__(self, key):
        collector = self._getCollector(key)
        attribute = self.schema[key]

        def convert(container):
            if container.value is None:
                value = None
            elif container.attribute.type == 'date' \
                    and isinstance(container.value, datetime):
                # Sometimes it's converted to datetime and so we need to
                # convert it back
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

        # Helper method for getting the appropriate parameters for
        # an attribute/value
        params = lambda a, v: dict(list(zip(('attribute', 'value'), (a, v))))

        # Helper methot to add an item to the value collector
        collect = lambda v: collector.__setitem__(
            attribute.name, wrapperFactory(**params(attribute, v)))

        def convert(value, type_):
            if value is None:
                converted = None
            elif type_ == 'boolean':
                converted = int(value)
            else:
                converted = value
            return converted

        if attribute.is_collection:
            # don't even bother getting a diff, just create a new list
            del self[key]
            for v in value:
                collect(convert(v, attribute.type))
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
        for key in self.schema.keys():
            yield (key, self[key])

    def serialize(self):
        result = dict(
            __metadata__=dict(
                id=self.id,
                state=self.state,
                collect_date=self.collect_date,
                create_date=self.create_date,
                create_user=getattr(self.create_user, 'name', None),
                modify_date=self.modify_date,
                modify_user=getattr(self.create_user, 'name', None)))

        # TODO: might be better to user a subquery table instead of
        # accessing as dictionary
        for key, value in self.items():
            if self.schema[key].type == 'object':
                if self[key] is not None:
                    value = self[key].serialize()
                else:
                    value = {}
            result[key] = value

        return result


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
            creator=Context.creator(name))

        return relationship(
            Context,
            primaryjoin=(
                '(%s.id == Context.key) & (Context.external == "%s")'
                % (cls.__name__, name)),
            foreign_keys=[Context.key, Context.external],
            cascade='all, delete-orphan',
            collection_class=set,
            backref=backref(
                '%s_parent' % name,
                uselist=False))


def TypeMappingClass(typeName, className, tableName, valueType, index=True):
    """
    Helper method to generate value mappings
    """

    class _ValueBaseMixin(Referenceable, Modifiable, Auditable):
        """
        An object that records values assigned to an EAV Entity.
        """

        __tablename__ = None
        __valuetype__ = None

        @declared_attr
        def entity_id(cls):
            return Column(
                Integer,
                ForeignKey(
                    column='entity.id',
                    name='fk_%s_entity_id' % cls.__tablename__,
                    ondelete='CASCADE'),
                nullable=False)

        @declared_attr
        def entity(cls):
            return relationship(
                Entity,
                primaryjoin='%s.entity_id == Entity.id' % cls.__name__,
                backref=backref(
                    name='_%s_values' % cls.__typename__,
                    collection_class=grouped_collection(
                        lambda v: v.attribute.name),
                    cascade='all, delete-orphan'))

        @declared_attr
        def attribute_id(cls):
            return Column(
                Integer,
                ForeignKey(
                    column='attribute.id',
                    name='fk_%s_attribute_id' % cls.__tablename__,
                    ondelete='CASCADE'),
                nullable=False)

        @declared_attr
        def attribute(cls):
            return relationship(Attribute)

        @declared_attr
        def _value(cls):
            return Column('value', cls.__valuetype__)

    class_ = type(className, (Model, _ValueBaseMixin), dict(
        __tablename__=tableName,
        __valuetype__=valueType,
        __typename__=typeName))

    Index('ix_%s_entity_id' % class_.__tablename__, class_.entity_id)
    Index('ix_%s_attribute_id' % class_.__tablename__, class_.attribute_id)

    if index:
        Index('ix_%s_value' % class_.__tablename__, class_._value)

    return class_


ValueDatetime = TypeMappingClass(
    'datetime', 'ValueDatetime', 'value_datetime', DateTime)

ValueInteger = TypeMappingClass(
    'integer', 'ValueInteger', 'value_integer', Integer)

ValueDecimal = TypeMappingClass(
    'decimal', 'ValueDecimal', 'value_decimal', Numeric)

ValueString = TypeMappingClass(
    'string', 'ValueString', 'value_string', Unicode)

ValueText = TypeMappingClass(
    'text', 'ValueText', 'value_text', UnicodeText, index=False)

ValueChoice = TypeMappingClass(
    'choice', 'ValueChoice', 'value_choice',
    ForeignKey('choice.id', name='fk_value_choice_value', ondelete='CASCADE'))

ValueBlob = TypeMappingClass(
    'blob', 'ValueBlob', 'value_blob', LargeBinary, index=False)

# Specify how the ``value`` properties behave, pretty much they're synonymns
# of the ``_value`` property,
valueProperty = hybrid_property(lambda s: s._value,
                                lambda s, v: setattr(s, '_value', v))
ValueDatetime.value = valueProperty
ValueInteger.value = valueProperty
ValueDecimal.value = valueProperty
ValueString.value = valueProperty
ValueText.value = valueProperty
ValueChoice.value = relationship(Choice,
                                 primaryjoin='Choice.id == ValueChoice._value')
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
            raise NotImplementedError(
                'Cannot coerce limit for type: %s' % type_)
        return check, interpreted

    if attribute.value_min is not None:
        check, interpreted = compareable(
            attribute.type, attribute.value_min, value)

        if interpreted < check:
            raise ConstraintError(
                attribute.schema.name, attribute.name, check, '<', interpreted,
                value)

    if attribute.value_max is not None:
        check, interpreted = compareable(
            attribute.type, attribute.value_max, value)

        if interpreted > check:
            raise ConstraintError(
                attribute.schema.name, attribute.name, check, '>', interpreted,
                value)

    # TODO: collections

    if attribute.validator is not None \
            and not re.match(attribute.validator, str(value)):
        raise ConstraintError(
            attribute.schema.name, attribute.name, attribute.validator, value)

    if attribute.choices:
        found = None
        for choice in attribute.choices:
            if choice.value == value:
                found = choice
                break
        if not found:
            raise ConstraintError(attribute.schema.name,
                                  attribute.name,
                                  [c.value for c in attribute.choices], value)

        target.choice = choice


event.listen(ValueDatetime.value, 'set', validateValue)
event.listen(ValueInteger.value, 'set', validateValue)
event.listen(ValueDecimal.value, 'set', validateValue)
event.listen(ValueString.value, 'set', validateValue)
event.listen(ValueText.value, 'set', validateValue)
event.listen(ValueChoice.value, 'set', validateValue)
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
    choice=ValueChoice,
    blob=ValueBlob,
    )
