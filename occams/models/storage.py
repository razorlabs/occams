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
    CheckConstraint,
    ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint,
    Date, DateTime, Boolean, Numeric, Integer,
    Unicode, UnicodeText, String
)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import collection
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from ..exc import ConstraintError, InvalidEntitySchemaError
from .auditing import Auditable
from .metadata import Referenceable, Describeable, Modifiable, User
from .meta import Base
from .schema import Schema, Attribute, Choice


def enforceSchemaState(entity):
    """
    Makes sure an entity cannot be added to an unpublished schema
    """
    if not entity.schema.publish_date or entity.schema.retract_date:
        raise InvalidEntitySchemaError(entity.schema.name)


class Context(Base, Referenceable, Modifiable, Auditable):

    __tablename__ = 'context'

    entity_id = Column(Integer, nullable=False)

    # Discriminator column for the keys and associations
    external = Column(String, nullable=False)

    key = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['entity_id'],
                refcolumns=['entity.id'],
                name='fk_%s_entity_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('entity_id', 'external', 'key'),
            Index('ix_%s_external_key' % cls.__tablename__, 'external', 'key'))


class GroupedCollection(object):
    """
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

    @collection.remover
    def _remove(self, value):
        self._groups[self._keyfunc(value)].remove(value)

    @collection.iterator
    def _iterator(self):
        for group in self._groups.values():
            for value in group:
                yield value


def grouped_collection(keyfunc):
    return lambda: GroupedCollection(keyfunc)


class State(Base, Referenceable, Describeable, Modifiable, Auditable):
    """
    An entity state to keep track of the entity's progress through some
    externally defined work flow.
    """

    __tablename__ = 'state'

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('name'),)


@event.listens_for(State.__table__, 'after_create')
def populate_default_states(target, connection, **kw):
    """
    We currently only ship with hard-coded states.

    This method expectecs the current connection to be annotated with
    a user in the info "blame" key. This user is ideally created after the
    "user" table is created.
    """

    blame = connection.info['blame']
    user_table = User.__table__

    result = connection.execute(
        user_table
        .select()
        .where(user_table.c.key == blame))

    user = result.fetchone()
    blame_id = user['id']

    def state(**kw):
        values = kw.copy()
        values.update({
            'create_user_id': blame_id,
            'modify_user_id': blame_id,
            'revision': 1
        })
        return values

    connection.execute(target.insert().values([
        state(name=u'pending-entry', title=u'Pending Entry'),
        state(name=u'in-progress', title=u'In Progress'),
        state(name=u'pending-review', title=u'Pending Review'),
        state(name=u'pending-correction', title=u'Pending Correction'),
        state(name=u'complete', title=u'Complete'),
    ]))


class Entity(Base, Referenceable, Modifiable, Auditable):
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

    not_done = Column(
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
            Index('ix_%s_schema_id' % cls.__tablename__, 'schema_id'),
            Index('ix_%s_state_id' % cls.__tablename__, 'state_id'),
            Index('ix_%s_collect_date' % cls.__tablename__, 'collect_date'))

    def _getCollector(self, key):
        type_ = self.schema.attributes[key].type
        if type_ == 'date':
            type_ = 'datetime'
        try:
            return getattr(self, '_%s_values' % type_)
        except AttributeError:  # pragma: no cover
            # Extreme edge case that is actually a programming error
            raise NotImplementedError(type_)

    def __getitem__(self, key):
        collector = self._getCollector(key)
        attribute = self.schema.attributes[key]

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
            elif container.attribute.type == 'choice':
                value = container.value.name
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
        attribute = self.schema.attributes[key]
        wrapperFactory = nameModelMap[attribute.type]

        if value is None:
            del self[key]
            return

        def convert(value, type_):
            if value is None:
                converted = None
            elif type_ == 'boolean':
                converted = int(value)
            elif type_ == 'choice':
                try:
                    converted = attribute.choices[value]
                except KeyError:
                    raise ConstraintError(
                        attribute.schema.name,
                        attribute.name,
                        [n for n in attribute.choices], value)
            else:
                converted = value
            return converted

        if attribute.is_collection:
            # don't even bother getting a diff, just create a new list
            del self[key]
            for v in value:
                convertedValue = convert(v, attribute.type)
                collector[attribute.name] = wrapperFactory(
                    attribute=attribute,
                    value=convertedValue)
        else:
            # For scalars, we're only dealing with one value, so it's OK to
            # try and update it
            convertedValue = convert(value, attribute.type)
            value_entries = collector[key]
            if value_entries:
                value_entries[0].value = convertedValue
            else:
                collector[attribute.name] = wrapperFactory(
                    attribute=attribute,
                    value=convertedValue)

    def __delitem__(self, key):
        collector = self._getCollector(key)
        del collector[key]


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
            creator=lambda e: Context(entity=e, external=name))

        return relationship(
            Context,
            primaryjoin=(
                '(%s.id == Context.key) & (Context.external == "%s")'
                % (cls.__name__, name)),
            foreign_keys=[Context.key, Context.external],
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

    class_ = type(className, (Base, _ValueBaseMixin), dict(
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

ValueNumber = TypeMappingClass(
    'number', 'ValueNumber', 'value_number', Numeric)

ValueString = TypeMappingClass(
    'string', 'ValueString', 'value_string', Unicode)

ValueText = TypeMappingClass(
    'text', 'ValueText', 'value_text', UnicodeText, index=False)

ValueChoice = TypeMappingClass(
    'choice', 'ValueChoice', 'value_choice',
    ForeignKey('choice.id', name='fk_value_choice_value', ondelete='CASCADE'))

ValueBlob = TypeMappingClass(
    'blob', 'ValueBlob', 'value_blob', String, index=False)

# Specify how the ``value`` properties behave, pretty much they're synonymns
# of the ``_value`` property,
valueProperty = hybrid_property(lambda s: s._value,
                                lambda s, v: setattr(s, '_value', v))
ValueDatetime.value = valueProperty
ValueNumber.value = valueProperty
ValueString.value = valueProperty
ValueText.value = valueProperty
ValueChoice.value = relationship(Choice,
                                 primaryjoin='Choice.id == ValueChoice._value')


class BlobInfo(object):

    def __init__(self, file_name, path, mime_type=None):
        self.file_name = file_name
        self.path = path
        self.mime_type = mime_type


def get_blob(self):
    if self.path:
        return BlobInfo(self.file_name, self.path, self.mime_type)


def set_blob(self, value):
    self.file_name = value.file_name if value else None
    self.path = value.path if value else None
    self.mime_type = value.mime_type if value else None


ValueBlob.file_name = Column(
    Unicode,
    CheckConstraint(
        'CASE WHEN value IS NOT NULL THEN file_name IS NOT NULL END',
        name='ck_name_has_value'),
    doc='The original file name (we use a sanitized file name internally)')
ValueBlob.mime_type = Column(String, doc='The MIME type of the file')
# path is an alias of the value (to keep things consisten, albeit confusing)
ValueBlob.path = valueProperty
ValueBlob.value = property(get_blob, set_blob)


def validateValue(target, value, oldvalue, initiator):
    """
    Attempts to make sure that valid values are set to an entity,
    Limitation: can only check one value at a time and does not work
    for multiple choice
    """
    attribute = target.attribute

    # Don't check None values, as the user may want to create empty/placeholder
    # scheamta
    if attribute.is_collection or value is None:
        return

    def check_length(func, op, limit, value):
        """
        Perform limit check operation
        :param func: Callback function to perform the actual operation,
                     must return true for pass
        :param op: label for the function
        :param limit: raw limit value (an integer)
        :param value: value to validate
        """
        if attribute.type in ('string', 'text'):
            value = len(value)
        elif attribute.type in ('number'):
            limit = Decimal(limit)
        elif attribute.type in ('date'):
            limit = date.fromtimestamp(limit)
        elif attribute.type in ('datetime'):
            limit = datetime.fromtimestamp(limit)
        else:
            raise NotImplementedError(
                'Cannot coerce limit for type: %s' % attribute.type)

        if not func(value, limit):
            raise ConstraintError(
                attribute.schema.name,
                attribute.name,
                limit, op, value,
                value)

    if attribute.value_min is not None:
        check_length(
            lambda length, limit: limit <= length,
            '<=',
            attribute.value_min,
            value
        )

    if attribute.value_max is not None:
        check_length(
            lambda length, limit: limit >= length,
            '>=',
            attribute.value_max,
            value
        )

    if attribute.pattern is not None \
            and not re.match(attribute.pattern, str(value)):
        raise ConstraintError(
            attribute.schema.name, attribute.name, attribute.pattern, value)


event.listen(ValueDatetime.value, 'set', validateValue)
event.listen(ValueNumber.value, 'set', validateValue)
event.listen(ValueString.value, 'set', validateValue)
event.listen(ValueText.value, 'set', validateValue)
event.listen(ValueChoice.value, 'set', validateValue)


# Where the types are stored
nameModelMap = dict(
    string=ValueString,
    text=ValueText,
    number=ValueNumber,
    date=ValueDatetime,
    datetime=ValueDatetime,
    choice=ValueChoice,
    blob=ValueBlob,
)
