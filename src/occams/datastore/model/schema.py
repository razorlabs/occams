""" Database Definitions
"""

from copy import copy
from copy import deepcopy
import hashlib
from decimal import Decimal
import datetime
import re

from sqlalchemy import text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm import synonym as Synonym
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Table
from sqlalchemy.schema import Column
from sqlalchemy.schema import PrimaryKeyConstraint
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
from occams.datastore.interfaces import ICategory
from occams.datastore.interfaces import IAttribute
from occams.datastore.interfaces import IChoice
from occams.datastore.model import DataStoreModel as Model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.auditing import Auditable


SCHEMA_STORAGE_NAMES = sorted([term.token for term in ISchema['storage'].vocabulary])
SCHEMA_STATE_NAMES = sorted([term.token for term in ISchema['state'].vocabulary])
ATTRIBUTE_TYPE_NAMES = sorted([term.token for term in IAttribute['type'].vocabulary])

IS_REQUIRED_DEFAULT = False
IS_COLLECTION_DEFAULT = False


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

    # This attribute has not been assigned a parent schema yet, let the
    # database handle this issue
    if attribute.schema is None:
        return None

    values = [
        # Consider ONLY the schema name, as descriptions would create a new
        # checksum for all attributes
        attribute.schema.name,

        # Attribute properties to consider, note object_schema_id is not
        # considered because only its fields matter not the actual sub form
        # itself
        attribute.name,
        attribute.title,
        attribute.description, # None != '', let the values behave naturally
        attribute.type,
        ]

    # is_collection and is_required could potentially not have been set at this
    # point, so assume their future default values
    if attribute.is_collection is None:
        values.append(IS_COLLECTION_DEFAULT)
    else:
        values.append(attribute.is_collection)

    if attribute.is_required is None:
        values.append(IS_REQUIRED_DEFAULT)
    else:
        values.append(attribute.is_required)

    # Consider choices as well, but order them alphabetically instead of
    # by order in case things were just rearranged, which apparently
    # should never affect the checksum
    for choice in attribute.choices:
        # Choice name does not matter because it's only used for communication
        # between the user interface and the data dictionary
        values.extend([choice.order, choice.title, choice.value])

    return checksum(*values)


def setChecksum(attribute):
    attribute._checksum = generateChecksum(attribute)


def defaultPublishDate(context):
    if context.current_parameters['state'] == 'published':
        return datetime.date.today()


class Category(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(ICategory)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            )


schema_category_table = Table('schema_category', Model.metadata,
    Column('schema_id', Integer),
    Column('category_id', Integer),
    PrimaryKeyConstraint('schema_id', 'category_id'),
    ForeignKeyConstraint(
        columns=['schema_id'],
        refcolumns=['schema.id'],
        name='fk_schema_category_schema_id',
        ondelete='CASCADE',
        ),
    ForeignKeyConstraint(
        columns=['category_id'],
        refcolumns=['category.id'],
        name='fk_schema_category_category_id',
        ondelete='CASCADE',
        ),
    )


class Schema(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(ISchema)

    categories = Relationship(
        Category,
        secondary=schema_category_table,
        collection_class=set,
        backref=backref(
            'schemata',
            collection_class=set,
            )
        )

    storage = Column(
        Enum(*SCHEMA_STORAGE_NAMES, name='schema_storage'),
        nullable=False,
        server_default=ISchema['storage'].default
        )

    publish_date = Column(Date, nullable=True, default=defaultPublishDate)

    retract_date = Column(Date)

    is_association = Column(Boolean)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name', 'publish_date'),
            CheckConstraint(
                'publish_date <= retract_date',
                name='ck_%s_valid_publication' % cls.__tablename__
                ),
            )

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, value):
        if key != value.name:
            value.name = key
        self.attributes[value.name] = value

    def __delitem__(self, key):
        del self.attributes[key]

    def __contains__(self, key):
        return key in self.attributes

    def keys(self):
        return list(self.iterkeys())

    def iterkeys(self):
        for attribute in sorted(self.attributes.values(), key=lambda a: a.order):
            yield attribute.name

    def values(self):
        return list(self.itervalues())

    def itervalues(self):
        for attribute in sorted(self.attributes.values(), key=lambda a: a.order):
            yield attribute

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        for attribute in sorted(self.attributes.values(), key=lambda a: a.order):
            yield attribute.name, attribute

    def __copy__(self):
        keys = ('name', 'title', 'description', 'storage')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        duplicate.categories = set([c for c in self.categories])
        duplicate.attributes = dict([(n, deepcopy(a)) for n, a in self.attributes.iteritems()])
        return duplicate


class Section(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):

    schema_id = Column(Integer, nullable=False)

    schema = Relationship(
        Schema,
        backref=backref(
            name='sections',
            order_by='Section.order',
            cascade='all, delete, delete-orphan'))

    order = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('schema_id', 'name', name='uq_%s_name' % cls.__tablename__),
            UniqueConstraint('schema_id', 'order', name='uq_%s_order' % cls.__tablename__))


class Attribute(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IAttribute)

    schema_id = Column(Integer, nullable=False,)

    schema = Relationship(
        Schema,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            cascade='all, delete, delete-orphan'))

    section_id = Column(Integer)

    section = Relationship(
        Section,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            cascade='all, delete, delete-orphan'))


    type = Column(Enum(*ATTRIBUTE_TYPE_NAMES, name='attribute_type'), nullable=False)

    is_collection = Column(Boolean, nullable=False, default=IS_COLLECTION_DEFAULT)

    is_required = Column(Boolean, nullable=False, default=IS_REQUIRED_DEFAULT)

    is_pii = Column(
        Boolean,
        nullable=False,
        default=False,
        doc='Stores Personnally Identifiable Information (PII).')

    _checksum = Column('checksum', String(32), nullable=False)

    checksum = Synonym('_checksum', descriptor=property(lambda self: self._checksum))

    # TODO: these should be something, they work for almost every type except decimal
    value_min = Column(Integer)

    value_max = Column(Integer)

    collection_min = Column(Integer)

    collection_max = Column(Integer)

    validator = Column(String)

    order = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['section_id'],
                refcolumns=['section.id'],
                name='fk_%s_section_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('schema_id', 'name', name='uq_%s_name' % cls.__tablename__),
            UniqueConstraint('section_id', 'order', name='uq_%s_order' % cls.__tablename__),
            Index('ix_%s_checksum' % cls.__tablename__, 'checksum'),
            CheckConstraint(
                "collection_min IS NULL OR collection_min >= 0",
                name='ck_%s_unsigned_collection_min' % cls.__tablename__,
                ),
            CheckConstraint(
                "collection_max IS NULL OR collection_max >= 0",
                name='ck_%s_unsigned_collection_max' % cls.__tablename__,
                ),
            CheckConstraint(
                "collection_min < collection_max",
                name='ck_%s_valid_collection' % cls.__tablename__,
                ),
            CheckConstraint(
                "value_min IS NULL OR value_min >= 0",
                name='ck_%s_unsigned_value_min' % cls.__tablename__,
                ),
            CheckConstraint(
                "value_max IS NULL OR value_max >= 0",
                name='ck_%s_unsigned_value_max' % cls.__tablename__,
                ),
            CheckConstraint(
                "value_min < value_max",
                name='ck_%s_valid_value' % cls.__tablename__,
                ),
            )

    def __copy__(self):
        keys = (
            'name', 'title', 'description', 'type', 'is_collection', 'is_required',
            'collection_min', 'collection_max', 'value_min', 'value_max',
            'validator', 'order'
            )
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        duplicate.choices = [deepcopy(c) for c in iter(self.choices)]
        return duplicate


class Choice(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):
    implements(IChoice)

    attribute_id = Column(Integer, nullable=False,)

    attribute = Relationship(
        Attribute,
        backref=backref(
            name='choices',
            order_by='Choice.order',
            collection_class=ordering_list('order'),
            cascade="all, delete, delete-orphan"
            )
        )

    order = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['attribute_id'],
                refcolumns=['attribute.id'],
                name='fk_%s_attribute_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint('attribute_id', 'name', name='uq_%s_name' % cls.__tablename__),
            UniqueConstraint('attribute_id', 'order', name='uq_%s_order' % cls.__tablename__),
            )

    def __copy__(self):
        keys = ('name', 'title', 'description', 'order')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        return copy(self)
