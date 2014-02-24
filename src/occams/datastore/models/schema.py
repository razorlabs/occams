"""
Metadata definitions
"""

from copy import copy, deepcopy
import hashlib
import re

from six import u
from sqlalchemy import(
    Table, Column,
    PrimaryKeyConstraint,
    CheckConstraint, UniqueConstraint, ForeignKeyConstraint, Index,
    Boolean, Enum, Date, Integer, String)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from occams.datastore.models import DataStoreModel as Model
from occams.datastore.models.metadata import (
    Referenceable, Describeable, Modifiable)
from occams.datastore.models.auditing import Auditable


def checksum(*args):
    """
    Returns a checksum of the combined arguments
    """
    # Finds any unicode whitespace in a string
    rex = re.compile('\s+', re.MULTILINE | re.UNICODE)
    # Condense all whitespace and strip trailing whitespace
    values = [rex.sub(u' ', u(a)).strip() for a in args if a is not None]
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
        attribute.description,  # None != '', let the values behave naturally
        attribute.type,
        ]

    # is_collection and is_required could potentially not have been set at this
    # point, so assume their future default values
    if attribute.is_collection is None:
        values.append(Attribute.is_collection.default)
    else:
        values.append(attribute.is_collection)

    if attribute.is_required is None:
        values.append(Attribute.is_required.default)
    else:
        values.append(attribute.is_required)

    # Consider choices as well, but order them alphabetically instead of
    # by order in case things were just rearranged, which apparently
    # should never affect the checksum
    for choice in attribute.choices:
        # Choice name does not matter because it's only used for communication
        # between the user interface and the data dictionary
        values.extend([choice.order, choice.title, choice.name])

    return checksum(*values)


def setChecksum(attribute):
    attribute._checksum = generateChecksum(attribute)


class Category(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    Logical categories for schemata in order to be able to group them.
    """

    __tablename__ = 'category'

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),)


schema_category_table = Table(
    'schema_category',
    Model.metadata,
    Column('schema_id', Integer),
    Column('category_id', Integer),
    PrimaryKeyConstraint('schema_id', 'category_id'),
    ForeignKeyConstraint(
        columns=['schema_id'],
        refcolumns=['schema.id'],
        name='fk_schema_category_schema_id',
        ondelete='CASCADE'),
    ForeignKeyConstraint(
        columns=['category_id'],
        refcolumns=['category.id'],
        name='fk_schema_category_category_id',
        ondelete='CASCADE'))


class Schema(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    An object that describes how an EAV schema is generated.
    Typically, an EAV schema represents a group of attributes that represent
    a meaningful data set. (e.g. contact details, name, test result.)
    Resulting schema objects can then be used to produce forms such as
    Zope-style interfaces.
    """

    __tablename__ = 'schema'

    categories = relationship(
        Category,
        secondary=schema_category_table,
        collection_class=set,
        backref=backref(
            'schemata',
            collection_class=set),
        doc='Listing of schema categories')

    storage = Column(
        Enum(*sorted(['eav', 'resource', 'table']), name='schema_storage'),
        nullable=False,
        server_default='eav',
        doc='How the generated objects will be stored. Storage methods are: '
            'eav - values are stored in a type-sharded set of tables; '
            'resource - the object exists in an external service; '
            'table - the object is stored in a conventional SQL table;')

    publish_date = Column(
        Date,
        doc='The date the schema was published for data collection')

    retract_date = Column(Date)

    is_association = Column(
        Boolean,
        doc='If set and True, the schema is an defines an association for '
            'multiple schemata.')

    @hybrid_property
    def has_private(self):
        for attribute in self.attributes.values():
            if attribute.is_private:
                return True
        return False

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name', 'publish_date'),
            CheckConstraint(
                'publish_date <= retract_date',
                name='ck_%s_valid_publication' % cls.__tablename__))

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
        sortfunc = lambda a: a.order
        for attribute in sorted(self.attributes.values(), key=sortfunc):
            yield attribute.name

    def values(self):
        sortfunc = lambda a: a.order
        for attribute in sorted(self.attributes.values(), key=sortfunc):
            yield attribute

    def items(self):
        sortfunc = lambda a: a.order
        for attribute in sorted(self.attributes.values(), key=sortfunc):
            yield attribute.name, attribute

    def __copy__(self):
        keys = ('name', 'title', 'description', 'storage')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        duplicate.categories = set([c for c in self.categories])
        duplicate.attributes = dict([(n, deepcopy(a))
                                    for n, a in self.attributes.items()])
        return duplicate


class Section(Model, Referenceable, Describeable, Modifiable, Auditable):

    __tablename__ = 'section'

    schema_id = Column(Integer, nullable=False)

    schema = relationship(
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
            UniqueConstraint('schema_id', 'name',
                             name='uq_%s_name' % cls.__tablename__),
            UniqueConstraint('schema_id', 'order',
                             name='uq_%s_order' % cls.__tablename__))


class Attribute(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    An object that describes how an EAV attribute is generated.
    Typically, an attribute is a meaningful property in the class data set.
    (e.g. user.firstname, user.lastname, contact.address, etc..)
    Note that if the attribute's type is an object, an object_class must
    be specified as well as a flag setting whether the object is to be
    rendered inline.
    Resulting attribute objects can then be used to produce forms such as
    Zope-style schema field.
    """

    __tablename__ = 'attribute'

    schema_id = Column(Integer, nullable=False,)

    schema = relationship(
        Schema,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            cascade='all, delete, delete-orphan'),
        doc=u'The schema that this attribute belongs to')

    section_id = Column(Integer, nullable=False)

    section = relationship(
        Section,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            cascade='all, delete, delete-orphan'))

    type = Column(
        Enum(*sorted(['boolean', 'decimal', 'integer', 'choice',
                      'date', 'datetime',
                      'string', 'text',
                      'blob']),
             name='attribute_type'),
        nullable=False)

    is_collection = Column(
        Boolean,
        nullable=False,
        default=False,
        doc='Enables attribute values to be stored multiple times (i.e. list)')

    is_required = Column(
        Boolean,
        nullable=False,
        default=False,
        doc='Forces attribute value to be required')

    is_private = Column(
        Boolean,
        nullable=False,
        default=False,
        doc='Stores Personnally Identifiable Information (PII).')

    _checksum = Column('checksum', String(32), nullable=False)

    checksum = hybrid_property(lambda self: self._checksum)

    value_min = Column(Integer, doc='Minimum length or value')

    value_max = Column(Integer, doc='Maximum length or value')

    collection_min = Column(Integer, doc='Minimum list length')

    collection_max = Column(Integer, doc='Maximum list length')

    validator = Column(String, doc='Regular expression validator')

    order = Column(Integer, nullable=False, doc='Display order')

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
            UniqueConstraint('schema_id', 'name',
                             name='uq_%s_name' % cls.__tablename__),
            UniqueConstraint('section_id', 'order',
                             name='uq_%s_order' % cls.__tablename__),
            Index('ix_%s_checksum' % cls.__tablename__, 'checksum'),
            CheckConstraint(
                "collection_min IS NULL OR collection_min >= 0",
                name='ck_%s_unsigned_collection_min' % cls.__tablename__),
            CheckConstraint(
                "collection_max IS NULL OR collection_max >= 0",
                name='ck_%s_unsigned_collection_max' % cls.__tablename__),
            CheckConstraint(
                "collection_min < collection_max",
                name='ck_%s_valid_collection' % cls.__tablename__),
            CheckConstraint(
                "value_min IS NULL OR value_min >= 0",
                name='ck_%s_unsigned_value_min' % cls.__tablename__),
            CheckConstraint(
                "value_max IS NULL OR value_max >= 0",
                name='ck_%s_unsigned_value_max' % cls.__tablename__),
            CheckConstraint(
                "value_min < value_max",
                name='ck_%s_valid_value' % cls.__tablename__))

    def __copy__(self):
        keys = (
            'name', 'title', 'description', 'type', 'is_collection',
            'is_required',
            'collection_min', 'collection_max', 'value_min', 'value_max',
            'validator', 'order')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        duplicate.choices = [deepcopy(c) for c in iter(self.choices)]
        return duplicate


class Choice(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    Possible value constraints for an attribute.
    Note objects of this type are not versioned, as they are merely an
    extension of the IAttribute objects. So if the choice constraints
    are to be modified, a new version of the IAttribute object
    should be created.
    """

    __tablename__ = 'choice'

    attribute_id = Column(Integer, nullable=False,)

    attribute = relationship(
        Attribute,
        backref=backref(
            name='choices',
            order_by='Choice.order',
            collection_class=ordering_list('order'),
            cascade='all, delete, delete-orphan'),
        doc='The attribute this choice belongs to')

    order = Column(Integer, nullable=False, doc='Display order')

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['attribute_id'],
                refcolumns=['attribute.id'],
                name='fk_%s_attribute_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('attribute_id', 'name',
                             name='uq_%s_name' % cls.__tablename__),
            UniqueConstraint('attribute_id', 'order',
                             name='uq_%s_order' % cls.__tablename__))
            # XXX: this is alsmost impossible to do in a database-agnostic way
            #CheckConstraint("name ~ '^[0-9]+$'",
                            #name='ck_%s_numeric_name' % cls.__tablename__))

    def __copy__(self):
        keys = ('name', 'title', 'description', 'order')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        return copy(self)
