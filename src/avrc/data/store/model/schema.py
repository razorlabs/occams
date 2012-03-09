""" Database Definitions
"""

from decimal import Decimal

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm import synonym as Synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import Index
from sqlalchemy.types import Boolean
from sqlalchemy.types import Enum
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.types import Unicode
from zope.interface import implements

from avrc.data.store.interfaces import ISchema
from avrc.data.store.interfaces import IAttribute
from avrc.data.store.interfaces import IChoice
from avrc.data.store.model._meta import Model
from avrc.data.store.model._meta import Referenceable
from avrc.data.store.model._meta import Describeable
from avrc.data.store.model.tracking import Modifiable
from avrc.data.store.model.tracking import buildModifiableConstraints


SCHEMA_STORAGE_NAMES = sorted([term.token for term in ISchema['storage'].vocabulary])
SCHEMA_STATE_NAMES = sorted([term.token for term in ISchema['state'].vocabulary])
ATTRIBUTE_TYPE_NAMES = sorted([term.token for term in IAttribute['type'].vocabulary])


class Schema(Model, Referenceable, Describeable, Modifiable):
    implements(ISchema)

    base_schema_id = Column(ForeignKey('schema.id', ondelete='CASCADE'))

    @declared_attr
    def base_schema(cls):
        return Relationship('Schema', remote_side='%s.id' % cls.__name__)

    sub_schemata = Relationship('Schema', remote_side=base_schema_id)

    state = Column(
        Enum(*SCHEMA_STATE_NAMES, name='schema_state'),
        nullable=False,
        server_default=ISchema['state'].default
        )

    storage = Column(
        Enum(*SCHEMA_STORAGE_NAMES, name='schema_storage'),
        nullable=False,
        server_default=ISchema['storage'].default
        )

    is_association = Column(Boolean)

    is_inline = Column(Boolean)

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            Index('ix_%s_name' % cls.__tablename__, 'name'),
            Index('ix_%s_base_schema_id' % cls.__tablename__, 'base_schema_id'),
            )


class Attribute(Model, Referenceable, Describeable, Modifiable):
    implements(IAttribute)

    schema_id = Column(ForeignKey(Schema.id, ondelete='CASCADE'), nullable=False,)

    schema = Relationship('Schema', primaryjoin=(schema_id == Schema.id))

    type = Column(Enum(*ATTRIBUTE_TYPE_NAMES, name='attribute_type'), nullable=False)

    choices = Relationship('Choice', collection_class=attribute_mapped_collection('name'))

    is_collection = Column(Boolean, nullable=False, server_default='FALSE')

    is_required = Column(Boolean, nullable=False, server_default='FALSE')

    object_schema_id = Column(ForeignKey(Schema.id, ondelete='SET NULL'))

    object_schema = Relationship('Schema', primaryjoin=(object_schema_id == Schema.id))

    checksum = Column(String(32), nullable=False)

    value_min = Column(Integer)

    value_max = Column(Integer)

    collection_min = Column(Integer)

    collection_max = Column(Integer)

    validator = Column(String)

    order = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            UniqueConstraint('schema_id', 'name'),
            UniqueConstraint('schema_id', 'order'),
            Index('ix_%s_object_schema_id' % cls.__tablename__, 'object_schema_id'),
            Index('ix_%s_checksum' % cls.__tablename__, 'checksum'),
            CheckConstraint(
                """
                CASE WHEN type = 'object'
                THEN object_schema_id IS NOT NULL
                ELSE object_schema_id IS NULL
                END
                """,
                name='ck_%s_valid_object_bind' % cls.__tablename__,
                ),
            )


class Choice(Model, Referenceable, Describeable, Modifiable):
    implements(IChoice)

    attribute_id = Column(ForeignKey(Attribute.id, ondelete='CASCADE'), nullable=False,)

    attribute = Relationship('Attribute')

    def get_value(self):
        value = self._value
        if value is not None:
            type_ = self.attribute.type
            if type_ == 'boolean':
                value = (self._value == 'True')
            elif type_ == 'integer':
                value = int(self._value)
            elif type_ == 'decimal':
                value = Decimal(self._value)
            else:
                value = unicode(self._value)
        return value

    def set_value(self, value):
        if value is not None:
            value = unicode(value)
        self._value = value

    _value = Column('value', Unicode, nullable=False)

    value = Synonym('_value', descriptor=property(get_value, set_value))

    order = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            UniqueConstraint('attribute_id', 'name'),
            UniqueConstraint('attribute_id', 'order'),
            Index('ix_%s_value' % cls.__tablename__, 'value')
            )

