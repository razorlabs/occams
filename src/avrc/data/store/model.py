""" Database Definitions
"""

from zope.interface import implements

from sqlalchemy import text
from sqlalchemy import case
from sqlalchemy import select
from sqlalchemy import union
from sqlalchemy import alias
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import has_inherited_table
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm import synonym as Synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.types import Enum
from sqlalchemy.types import Numeric
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.types import Unicode

from avrc.data.store.interfaces import ISchema
from avrc.data.store.interfaces import IAttribute
from avrc.data.store.interfaces import IChoice
from avrc.data.store.interfaces import IEntity
from avrc.data.store.interfaces import IValue


# NOTE: CURRENT_TIMESTAMP in PostgreSQL returns the START of the transaction
NOW = text('CURRENT_TIMESTAMP')
FALSE = text('FALSE')


TIMELINE_CHECK_SQL = 'create_date <= modify_date AND modify_date <= remove_date'
TIMELINE_NAME_FMT = '%s_valid_edit_timeline'

STORAGE_NAMES = sorted([term.token for term in ISchema['storage'].vocabulary])
TYPE_NAMES = sorted([term.token for term in IAttribute['type'].vocabulary])


# Base class for declarative syntax on our models
Model = declarative_base()


class _AutoNamed(object):
    """ 
    Generates the SQL table name from the class name.
    """

    @declared_attr
    def __tablename__(cls):
        if has_inherited_table(cls) and _AutoNamed not in cls.__bases__:
            return None
        return cls.__name__.lower()


class _Entry(object):
    """ 
    Adds primary key id columns to tables.
    """

    id = Column(Integer, primary_key=True)


class _Describeable(object):
    """ 
    Adds standard content properties to tables.
    """

    name = Column(String, nullable=False, index=True)

    title = Column(Unicode, nullable=False)

    description = Column(Unicode)


class _History(object):

    @classmethod
    def asOf(cls, on):
        """ 
        Helper method to generate timeline filter
        
        Arguments
            ``on``
                A `datetime` object to to check against. A filter that checks
                if ``on`` falls between `create_date` <= `on` < `remove_date`
                will be returned. A value of `None` indicates the most
                recent value should be checked for: 
                `create_date` <= `on` < `infinity`
        """
        filter = (None == cls.remove_date)
        if on is not None:
            after_create = (on >= cls.create_date)
            before_remove = (on < cls.remove_date)
            during = after_create & before_remove
            filter = case([(filter, after_create)], else_=during)
        return filter


class _Editable(object):
    """ 
    Adds user edit modification meta data for lifecycle tracking.
    """

    @declared_attr
    def create_date(cls):
        return Column(DateTime, nullable=False, server_default=NOW)

    @declared_attr
    def create_user_id(cls):
        return Column(Integer)

    @declared_attr
    def modify_date(cls):
        return Column(DateTime, nullable=False, server_default=NOW, onupdate=NOW)

    @declared_attr
    def modify_user_id(cls):
        return Column(Integer)

    @declared_attr
    def remove_date(cls):
        return Column(DateTime, index=True)

    @declared_attr
    def remove_user_id(cls):
        return Column(Integer)



class State(Model):
    """
    Workflow state of an object instance.
    TODO: move into it's own package
    """

    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)

    name = Column(Unicode, nullable=False, unique=True)

    title = Column(Unicode, nullable=False)

    description = Column(Unicode)

    is_default = Column(Boolean, nullable=False, default=False, index=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=NOW)

    modify_date = Column(DateTime, nullable=False, default=NOW, onupdate=NOW)


class Schema(Model, _AutoNamed, _Entry, _Describeable, _Editable, _History):
    implements(ISchema)

    base_schema_id = Column(ForeignKey('schema.id', ondelete='CASCADE'))

    @declared_attr
    def base_schema(cls):
        return Relationship('Schema', remote_side='%s.id' % cls.__name__)

    sub_schemata = Relationship('Schema', remote_side=base_schema_id)

    storage = Column(
        Enum(*STORAGE_NAMES, name='schema_storage'),
        nullable=False,
        server_default=ISchema['storage'].default
        )

    is_association = Column(Boolean)

    is_inline = Column(Boolean)

    __table_args__ = (
        CheckConstraint(TIMELINE_CHECK_SQL, (TIMELINE_NAME_FMT % 'class')),
        dict(),
        )


class Attribute(Model, _AutoNamed, _Entry, _Describeable, _Editable, _History):
    implements(IAttribute)

    schema_id = Column(
        ForeignKey(Schema.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
        )

    schema = Relationship('Schema', primaryjoin=(schema_id == Schema.id))

    type = Column(Enum(*TYPE_NAMES, name='attribute_type'), nullable=False)

    choices = Relationship('Choice', collection_class=attribute_mapped_collection('name'))

    is_collection = Column(Boolean, nullable=False, server_default=FALSE)

    is_readonly = Column(Boolean, nullable=False, server_default=FALSE)

    is_required = Column(Boolean, nullable=False, server_default=FALSE)

    is_inline_object = Column(Boolean)

    object_schema_id = Column(ForeignKey(Schema.id, ondelete='SET NULL'), index=True)

    object_schema = Relationship('Schema', primaryjoin=(object_schema_id == Schema.id))

    url_template = Column(String)

    min = Column(Integer)

    max = Column(Integer)

    default = Column(Unicode)

    validator = Column(Unicode)

    widget = Column(String)

    order = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            """
            CASE
                WHEN type = 'object' THEN 
                    object_schema_id IS NOT NULL AND is_inline_object IS NOT NULL
                ELSE 
                    object_schema_id IS NULL AND is_inline_object IS NULL
            END
            """,
            name='attribute_valid_object_bind',
            ),
        CheckConstraint(TIMELINE_CHECK_SQL, (TIMELINE_NAME_FMT % 'attribute')),
        dict(),
        )


class Choice(Model, _AutoNamed, _Entry, _Describeable, _Editable):
    implements(IChoice)

    attribute_id = Column(
        ForeignKey(Attribute.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    attribute = Relationship('Attribute')

    _value = Column('value', Unicode, nullable=False, index=True)

    order = Column(Integer, nullable=False, index=True)

    def get_value(self):
        return self._value

    def set_value(self, value):
        if value is not None:
            value = unicode(value)
        self._value = value

    value = Synonym('_value', descriptor=property(get_value, set_value))

    __table_args__ = (
        CheckConstraint(TIMELINE_CHECK_SQL, (TIMELINE_NAME_FMT % 'choice')),
        dict()
        )


class Entity(Model, _AutoNamed, _Entry, _Describeable, _Editable, _History):
    implements(IEntity)

    schema_id = Column(
        ForeignKey(Schema.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    schema = Relationship('Schema')

    state_id = Column(ForeignKey(State.id, ondelete='CASCADE'), index=True)

    state = Relationship('State')

    # Private reference to child objects so that they can be removed in a 
    # cascading fashion by the ORM (otherwise they'll be left as orphaned 
    # entries.  
    _value_objects = Relationship(
        'ValueObject',
        primaryjoin='(Entity.id == ValueObject.entity_id)',
        cascade='all,delete-orphan',
        )

    __table_args__ = (
        CheckConstraint(TIMELINE_CHECK_SQL, (TIMELINE_NAME_FMT % 'entity')),
        dict(),
        )


class _ValueBaseMixin(_Entry, _Editable, _History):
    implements(IValue)

    __valuetype__ = None


    @declared_attr
    def entity_id(cls):
        return Column(
            ForeignKey(Entity.id, ondelete='CASCADE'),
            nullable=False,
            index=True
            )


    @declared_attr
    def entity(cls):
        return Relationship(
            'Entity',
            primaryjoin='%s.entity_id == Entity.id' % cls.__name__
            )


    @declared_attr
    def attribute_id(cls):
        return Column(
            ForeignKey(Attribute.id, ondelete='CASCADE'),
            nullable=False,
            index=True
            )


    @declared_attr
    def attribute(cls):
        return Relationship('Attribute')


    @declared_attr
    def choice_id(cls):
        return Column(
            ForeignKey(Choice.id, ondelete='CASCADE'),
            index=True
            )


    @declared_attr
    def choice(cls):
        return Relationship('Choice')


    @declared_attr
    def value(cls):
        return Column(cls.__valuetype__, nullable=False, index=True)


    @declared_attr
    def __table_args__(cls):
        table_name = cls.__tablename__
        return (
            CheckConstraint(TIMELINE_CHECK_SQL, (TIMELINE_NAME_FMT % table_name)),
            dict(),
            )


class ValueDatetime(Model, _ValueBaseMixin):
    """ 
    A datetime EAV value.
    """

    __tablename__ = 'datetime'
    __valuetype__ = DateTime


class ValueInteger(Model, _ValueBaseMixin):
    """ 
    A integer EAV value.
    """

    __tablename__ = 'integer'
    __valuetype__ = Integer



class ValueDecimal(Model, _ValueBaseMixin):
    """ 
    A decimal EAV value.
    """

    __tablename__ = 'decimal'
    __valuetype__ = Numeric


class ValueString(Model, _ValueBaseMixin):
    """ 
    A string EAV value.
    """

    __tablename__ = 'string'
    __valuetype__ = Unicode


class ValueObject(Model, _ValueBaseMixin):
    """ 
    An object EAV value.
    """

    __tablename__ = 'object'
    __valuetype__ = ForeignKey(Entity.id, ondelete='CASCADE')

    # NOTE: If there are shared objects, THEY WILL BE REMOVED AS WELL...
    @declared_attr
    def value_object(cls):
        return Relationship(
            'Entity',
            primaryjoin='(%s.value == Entity.id)' % cls.__name__,
            single_parent=True,
            cascade='all,delete-orphan'
            )


def _buildAssignmentTable():
    """ 
    Builds a union-table for easily searching for value assignments to
    an entity, as currently separate value-specific tables are used which
    unfortunately makes it hard to track this information down.
    """
    queries = []

    for m in (ValueString, ValueInteger, ValueObject, ValueDatetime, ValueDecimal):
        query = (
            select([
                m.entity_id.label('entity_id'),
                m.attribute_id.label('attribute_id'),
                m.create_date.label('create_date'),
                m.modify_date.label('modify_date'),
                m.remove_date.label('remove_date'),
                ])
            )
        queries.append(query)

    return alias(union(*queries))


assignment_table = _buildAssignmentTable()


class Assignment(Model, _History):
    """ 
    Helper object for easily accessing value assignments in one table
    as opposed to looking at each value table individually.
    """
    __table__ = assignment_table

    attribute = Relationship('Attribute')

    entity = Relationship('Entity')

    __mapper_args__ = dict(
        primary_key=[assignment_table.c.entity_id, assignment_table.c.attribute_id]
        )
