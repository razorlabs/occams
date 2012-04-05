""" Database Definitions
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.collections import collection
from sqlalchemy.orm.exc import NoResultFound
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
    if entity is not None and entity.state == 'not-done':
        for name, attribute in entity.schema.attributes.items():
            if attribute.type == 'object':
                cleanDataByState(entity[name])
            else:
                del entity[name]


def enforceSchemaState(entity):
    schema = entity.schema
    if schema.state != 'published':
        raise ValueError('Cannot collect data for unpublished Schema(%s)' % schema.name)


class External(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            )


class Context(Model, AutoNamed, Modifiable, Auditable):

    entity_id = Column(Integer, nullable=False, primary_key=True)

    entity = Relationship('Entity')

    external_id = Column(Integer, nullable=False, primary_key=True)

    external = Relationship('External')

    key = Column(Integer, nullable=False, primary_key=True)

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            ForeignKeyConstraint(
                columns=['entity_id'],
                refcolumns=['entity.id'],
                name='fk_%s_entity_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['external_id'],
                refcolumns=['external.id'],
                name='fk_%s_external_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            )


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

    _string_values = Relationship(
        'ValueString',
        cascade='all, delete-orphan',
        back_populates='entity',
        lazy='dynamic',
        )

    _integer_values = Relationship(
        'ValueInteger',
        cascade='all, delete-orphan',
        back_populates='entity',
        lazy='dynamic',
        )

    _datetime_values = Relationship(
        'ValueDatetime',
        cascade='all, delete-orphan',
        back_populates='entity',
        lazy='dynamic',
        )

    _decimal_values = Relationship(
        'ValueDecimal',
        cascade='all, delete-orphan',
        back_populates='entity',
        lazy='dynamic',
        )

    _object_values = Relationship(
        'ValueObject',
        cascade='all, delete-orphan',
        back_populates='entity',
        primaryjoin='Entity.id == ValueObject._value',
        lazy='dynamic',
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

    def _getCollector(self, key):
        type_ = self.schema[key].type
        if type_ in ('string', 'text',):
            return self._string_values
        elif type_ in ('integer', 'boolean'):
            return self._integer_values
        elif type_ in ('datetime', 'date'):
            return self._datetime_values
        elif type_ == 'decimal':
            return self._decimal_values
        elif type_ == 'object':
            return self._object_values
        else:
            raise NotImplementedError(type_)

    def __getitem__(self, key):
        collector = self._getCollector(key)
        attribute = self.schema[key]
        query = collector.filter_by(attribute=attribute)
        if attribute.is_collection:
            value = [v.value for v in iter(query)]
        else:
            try:
                wrappedValue = query.one()
            except NoResultFound:
                value = None
            else:
                value = wrappedValue.value
        return value

    def __setitem__(self, key, value):
        collector = self._getCollector(key)
        attribute = self.schema[key]
        wrapperFactory = nameModelMap[attribute.type]

        if attribute.is_collection:
            # Don't even bother to try and get a diff, just remove it
            del self[key]

        values = [value] if not isinstance(value, list) else value

        for value in values:
            if not collector.filter_by(attribute=attribute, _value=value).count() > 0:
                collector.append(wrapperFactory(attribute=attribute, _value=value))

    def __delitem__(self, key):
        collector = self._getCollector(key)
        attribute = self.schema[key]
        collector.filter_by(attribute=attribute).delete('fetch')

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        for key in self.schema.iterkeys():
            yield (key, self[key])


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
            return Relationship(
                'Entity',
                primaryjoin='%s.entity_id == Entity.id' % cls.__name__
                )

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
