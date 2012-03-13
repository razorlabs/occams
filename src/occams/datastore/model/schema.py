""" Database Definitions
"""

import hashlib
from decimal import Decimal
import re

from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm import synonym as Synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Column
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.schema import Index
from sqlalchemy.types import Boolean
from sqlalchemy.types import Enum
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.types import Unicode
from zope.interface import implements

from occams.datastore.interfaces import ISchema
from occams.datastore.interfaces import IAttribute
from occams.datastore.interfaces import IChoice
from occams.datastore.model.model import Model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.metadata import buildModifiableConstraints
from occams.datastore.model.auditing import Auditable


SCHEMA_STORAGE_NAMES = sorted([term.token for term in ISchema['storage'].vocabulary])
SCHEMA_STATE_NAMES = sorted([term.token for term in ISchema['state'].vocabulary])
ATTRIBUTE_TYPE_NAMES = sorted([term.token for term in IAttribute['type'].vocabulary])


def checksum(*args):
    """
    Returns a checksum of the combined arguments
    """
    # Finds any unicode whitespace in a string
    rex = re.compile('\s+', re.MULTILINE | re.UNICODE)
    # Condense all whitespace and strip trailing whitespace
    values = [rex.sub(u' ', unicode(a)).strip() for a in args if a is not None]
    # encode and generate checksum
    return hashlib.md5(u''.join(values).encode('utf-8')).hexdigest()


def generateChecksum(attribute):
    return checksum(*[
            attribute.schema.name,
            attribute.schema.description,
            attribute.name,
            attribute.title,
            attribute.description,
            attribute.type,
            attribute.is_collection,
            attribute.is_required,
            attribute.object_schema_id,
            ])


def attributeBeforeFlush(session, flush_context, instances):
    attributes = lambda i: isinstance(i, Attribute)
    for instance in filter(attributes, session.new):
        instance.checksum = generateChecksum(instance)
    for instance in filter(attributes, session.dirty):
        instance.checksum = generateChecksum(instance)


def registerLibarianSession(session):
    event.listens_for(session, 'before_flush', attributeBeforeFlush)


def unregisterLibarianSession(session):
    event.remove(session, 'before_flush', attributeBeforeFlush)


class Schema(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(ISchema)

    base_schema_id = Column(Integer)

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

    attributes = Relationship('Attribute',
        collection_class=attribute_mapped_collection('name'))

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            ForeignKeyConstraint(
                columns=['base_schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_base_schema_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            Index('ix_%s_name' % cls.__tablename__, 'name'),
            Index('ix_%s_base_schema_id' % cls.__tablename__, 'base_schema_id'),
            )

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, value):
        self.attributes[key] = value

    def __delitem__(self, key):
        del self.attributes[key]

    def __contains__(self, key):
        return key in self.attributes

    def keys(self):
        return self.attributes.keys()

    def values(self):
        return self.attributes.values()

    def items(self):
        return self.attributes.items()

    def __iter__(self):
        return self.attributes.__iter__()


class Attribute(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IAttribute)

    schema_id = Column(Integer, nullable=False,)

    schema = Relationship('Schema', primaryjoin=(schema_id == Schema.id))

    type = Column(Enum(*ATTRIBUTE_TYPE_NAMES, name='attribute_type'), nullable=False)

    choices = Relationship('Choice', collection_class=attribute_mapped_collection('name'))

    is_collection = Column(Boolean, nullable=False, server_default='FALSE')

    is_required = Column(Boolean, nullable=False, server_default='FALSE')

    object_schema_id = Column(Integer)

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
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['object_schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_object_schema_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
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


class Choice(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IChoice)

    attribute_id = Column(Integer, nullable=False,)

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
            ForeignKeyConstraint(
                columns=['attribute_id'],
                refcolumns=['attribute.id'],
                name='fk_%s_attribute_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint('attribute_id', 'name'),
            UniqueConstraint('attribute_id', 'order'),
            Index('ix_%s_value' % cls.__tablename__, 'value')
            )

