""" Database Definitions
"""

import hashlib
from decimal import Decimal
import datetime
import re

from sqlalchemy import event
from sqlalchemy import cast
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm import synonym as Synonym
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Column
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.schema import Index
from sqlalchemy.types import Boolean
from sqlalchemy.types import Enum
from sqlalchemy.types import Date
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.types import Unicode
from zope.interface import implements

from occams.datastore.interfaces import ISchema
from occams.datastore.interfaces import IAttribute
from occams.datastore.interfaces import IChoice
from occams.datastore.model import Model
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
    """
    Creates a checksum for an attribute.
    """
    values = [
        # Consider ONLY the schema name, as descriptions would create a new
        # checksum for all attributes
        attribute.schema.name,

        # Attribute properties to consider, note object_schema_id is not
        # considered because only its fields matter not the actual sub form
        # itself
        attribute.name,
        attribute.title,
        attribute.description,
        attribute.type,
        attribute.is_collection,
        attribute.is_required,
        ]

    # Consider choices as well, but order them alphabetically instead of
    # by order in case things were just rearranged, which apparently
    # should never affect the checksum
    for choice in attribute.choices:
        # Choice name does not matter because it's only used for communication
        # between the user interface and the data dictionary
        values.extend([choice.order, choice.title, choice.value])

    attribute._checksum = checksum(*values)


def defaultPublishDate(context):
    if context.current_parameters['state'] == 'published':
        return datetime.date.today()


def defaultDeprecateDate(context):
    if context.current_parameters['state'] == 'deprecated':
        return datetime.date.today()


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
        default=ISchema['state'].default,
        server_default=ISchema['state'].default
        )

    storage = Column(
        Enum(*SCHEMA_STORAGE_NAMES, name='schema_storage'),
        nullable=False,
        server_default=ISchema['storage'].default
        )

    publish_date = Column(Date, nullable=True, default=defaultPublishDate)

    is_association = Column(Boolean)

    is_inline = Column(Boolean)

    attributes = Relationship(
        'Attribute',
        primaryjoin='Schema.id == Attribute.schema_id',
        collection_class=attribute_mapped_collection('name'),
        back_populates='schema',
        order_by='Attribute.order',
        )

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            ForeignKeyConstraint(
                columns=['base_schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_base_schema_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint('name', 'publish_date'),
            Index('ix_%s_base_schema_id' % cls.__tablename__, 'base_schema_id'),
            CheckConstraint(
                """
                CASE
                    WHEN state = 'draft' OR state='review' THEN
                        publish_date IS NULL
                    WHEN state = 'published' OR state = 'retracted' THEN
                        publish_date IS NOT NULL
                END
                """,
                name='ck_%s_valid_publication'
                ),
            )

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, value):
        self.attributes[value.name] = value

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

    @classmethod
    def asOf(cls, key, on, session):
        """
        Helper method for finding the most recently published version of a schema
        """
        query = session.query(cls).filter_by(name=key, state='published')
        if on is not None:
            if not isinstance(on, datetime.date):
                raise ValueError('[%s] is not a valid timestamp' % on)
            query = query.filter(cls.publish_date <= cast(on, Date))
        query = query.order_by(cls.publish_date.desc()).limit(1)
        return query.first()

    def copy(self):
        schemaList = (
            'base_schema', 'name', 'title', 'description', 'storage', 'is_inline',
            )
        attributeList = (
            'name', 'title', 'description', 'type', 'is_collection',
            'object_schema', 'object_schema_id',
            'is_required', 'collection_min', 'collection_max',
            'value_min', 'value_max', 'validator', 'order'
            )
        choiceList = ('name', 'title', 'description', 'value', 'order')

        copy = lambda c, l: c.__class__(**dict([(p, getattr(c, p)) for p in l]))

        schemaCopy = copy(self, schemaList)

        for attributeName, attribute in self.attributes.items():
            attributeCopy = copy(attribute, attributeList)
            schemaCopy.attributes[attributeName] = attributeCopy

            if attribute.type == 'object':
                attributeCopy.object_schema = attribute.object_schema.copy()

            for choice in attribute.choices:
                attributeCopy.choices.append(copy(choice, choiceList))

        return schemaCopy


class Attribute(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IAttribute)

    schema_id = Column(Integer, nullable=False,)

    schema = Relationship(
        'Schema',
        back_populates='attributes',
        primaryjoin=(schema_id == Schema.id),
        )

    type = Column(Enum(*ATTRIBUTE_TYPE_NAMES, name='attribute_type'), nullable=False)

    choices = Relationship(
        'Choice',
        back_populates='attribute',
        order_by='Choice.order',
        )

    is_collection = Column(Boolean, nullable=False, default=False)

    is_required = Column(Boolean, nullable=False, default=False)

    object_schema_id = Column(Integer)

    object_schema = Relationship('Schema', primaryjoin=(object_schema_id == Schema.id))

    _checksum = Column('checksum', String(32), nullable=False)

    checksum = Synonym('_checksum', descriptor=property(lambda self: self._checksum))

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
                CASE WHEN type = 'object' THEN
                    object_schema_id IS NOT NULL
                ELSE
                    object_schema_id IS NULL
                END
                """,
                name='ck_%s_valid_object_bind' % cls.__tablename__,
                ),
            )


class Choice(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IChoice)

    attribute_id = Column(Integer, nullable=False,)

    attribute = Relationship('Attribute', back_populates='choices')

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
