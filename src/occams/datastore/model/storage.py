""" Database Definitions
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
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
from occams.datastore.model.schema import Schema
from occams.datastore.model.schema import Attribute
from occams.datastore.model.schema import Choice


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


def entityBeforeFlush(session, flush_context, instances):
    """
    Session Event handler to update attribute checksums
    """
#    attributes = lambda i: isinstance(i, Attribute)
#    for instance in filter(attributes, session.new):
#        instance._checksum = generateChecksum(instance)
#    for instance in filter(attributes, session.dirty):
#        instance._checksum = generateChecksum(instance)


def registerEntityListener(session):
    event.listen(session, 'before_flush', entityBeforeFlush)


def unregisterEntityListenter(session):
    event.remove(session, 'before_flush', entityBeforeFlush)


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

    integer_values = Relationship('ValueInteger')

    datetime_values = Relationship('ValueDatetime')

    decimal_values = Relationship('ValueDecimal')

    string_values = Relationship('ValueString')

    obect_values = Relationship('ValueObject',
        primaryjoin='Entity.id == ValueObject._value')

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


class ValueDatetime(Model, _ValueBaseMixin):
    __tablename__ = 'datetime'
    __valuetype__ = DateTime


class ValueInteger(Model, _ValueBaseMixin):
    __tablename__ = 'integer'
    __valuetype__ = Integer


class ValueDecimal(Model, _ValueBaseMixin):
    __tablename__ = 'decimal'
    __valuetype__ = Numeric


class ValueString(Model, _ValueBaseMixin):
    __tablename__ = 'string'
    __valuetype__ = Unicode


class ValueObject(Model, _ValueBaseMixin):
    __tablename__ = 'object'
    __valuetype__ = Integer

