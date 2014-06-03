"""
Metadata definitions
"""

from copy import copy, deepcopy
from datetime import datetime
import hashlib
import re

import six
from sqlalchemy import(
    cast,
    Table, Column,
    PrimaryKeyConstraint,
    CheckConstraint, UniqueConstraint, ForeignKeyConstraint, Index,
    Boolean, Enum, Date, Integer, String)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, validates
from sqlalchemy.orm.collections import attribute_mapped_collection

from . import DataStoreModel as Model
from .metadata import Referenceable, Describeable, Modifiable
from .auditing import Auditable
from ..utils.sql import CaseInsensitive


RE_VALID_NAME = re.compile(r'^[a-z][a-z0-9_]*$', re.I)


RESERVED_WORDS = frozenset(
    # Python keywords
    # https://docs.python.org/3.4/reference/lexical_analysis.html#keywords
    """
    False      class      finally    is         return
    None       continue   for        lambda     try
    True       def        from       nonlocal   while
    and        del        global     not        with
    as         elif       if         or         yield
    assert     else       import     pass
    break      except     in         raise
    """
    # Additional black-listed names
    """
    Data     Float     Int     Numeric     Oxphys
    array     close     float     int     input
    open     range     type     write     zeros
    acos     asin     atan     cos     e
    exp     fabs     floor     log     log10
    pi     sin     sqrt     tan
    """
    .split())


def checksum(*args):
    """
    Returns a checksum of the combined arguments
    """
    # Finds any unicode whitespace in a string
    rex = re.compile(r'\s+', re.MULTILINE | re.UNICODE)

    # Condense all whitespace and strip trailing whitespace
    def condense_whitespace(value):
        if not isinstance(value, six.string_types):
            value = str(value)
        return rex.sub(u' ', value).strip()

    nonnulls = six.moves.filter(lambda v: v is not None, args)
    strings = six.moves.map(condense_whitespace, nonnulls)

    # encode and generate checksum
    return hashlib.md5(u''.join(strings).encode('utf-8')).hexdigest()


def generateChecksum(attribute):
    """
    Creates a checksum for an attribute.
    """

    # This attribute has not been assigned a parent schema yet, let the
    # database handle this issue
    schema = attribute.schema or getattr(attribute.section, 'schema', None)
    if schema is None:
        return None

    values = [
        # Consider ONLY the schema name, as descriptions would create a new
        # checksum for all attributes
        schema.name,

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
        values.append(Attribute.is_collection.default.arg)
    else:
        values.append(attribute.is_collection)

    if attribute.is_required is None:
        values.append(Attribute.is_required.default.arg)
    else:
        values.append(attribute.is_required)

    # Consider choices as well, but order them alphabetically instead of
    # by order in case things were just rearranged, which apparently
    # should never affect the checksum
    for choice in sorted(six.itervalues(attribute.choices),
                         key=lambda c: c.order):
        values.extend([choice.name, choice.title])

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

    # Override for max length of 32 characters
    name = Column(String(32), nullable=False)

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
        doc="""
            How the generated objects will be stored. Storage methods are:
                eav - values are stored in a type-sharded set of tables;
                resource - the object exists in an external service;
                table - the object is stored in a conventional SQL table;
            """)

    publish_date = Column(
        Date,
        doc='The date the schema was published for data collection')

    retract_date = Column(Date)

    is_association = Column(
        Boolean,
        doc="""
            If set and True, the schema is an defines an association for
            multiple schemata.
            """)

    @hybrid_property
    def has_private(self):
        for attribute in self.attributes.values():
            if attribute.is_private:
                return True
        return False

    @validates('name')
    def valid_name(self, key, name):
        if not RE_VALID_NAME.match(name):
            raise ValueError('Invalid name: "%s"' % name)
        return name

    @declared_attr
    def __table_args__(cls):
        return (
            CheckConstraint(
                'publish_date <= retract_date',
                name='ck_%s_valid_publication' % cls.__tablename__),)

    def __copy__(self):
        keys = ('name', 'title', 'description', 'storage')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        duplicate.categories = set([c for c in self.categories])
        for section in six.itervalues(self.sections):
            duplicate.sections[section.name] = deepcopy(section)
        return duplicate

    @classmethod
    def from_json(cls, data):
        """
        Loads a schema from parsed JSON data

        Parameters:
        data -- parsed json data (i.e. a dict)
        """
        sections = data.pop('sections')

        schema = cls(**data)
        schema.publish_date = \
            datetime.strptime(data['publish_date'], '%Y-%m-%d').date()

        if sections:
            for key, section in six.iteritems(sections):
                schema.sections[key] = Section.from_json(section)
            schema.attributes.update(schema.sections[key].attributes)

        return schema

    def to_json(self):
        """
        Serializes to a JSON-ready dictionary
        """
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'storage': self.storage,
            'published': self.publish_date.isoformat(),
            'sections': dict([(s.name, s.to_json())
                             for s in six.itervalues(self.sections)])}


# __table_args__ is not accepting this constraint.
# Need to initiate the Index here for now...
Index(
    'uq_schema_version',
    CaseInsensitive(Schema.name),
    Schema.publish_date,
    unique=True)


section_attribute_table = Table(
    'section_attribute',
    Model.metadata,
    Column('section_id', Integer),
    Column('attribute_id', Integer),
    PrimaryKeyConstraint('section_id', 'attribute_id'),
    ForeignKeyConstraint(
        columns=['section_id'],
        refcolumns=['section.id'],
        name='fk_section_attribute_section_id',
        ondelete='CASCADE'),
    ForeignKeyConstraint(
        columns=['attribute_id'],
        refcolumns=['attribute.id'],
        name='fk_section_attribute_attribute_id',
        ondelete='CASCADE'),
    UniqueConstraint('attribute_id', name='uq_section_attribute_attribute_id'))


class Section(Model, Referenceable, Describeable, Modifiable, Auditable):

    __tablename__ = 'section'

    schema_id = Column(Integer, nullable=False)

    schema = relationship(
        Schema,
        backref=backref(
            name='sections',
            collection_class=attribute_mapped_collection('name'),
            order_by='Section.order',
            cascade='all, delete, delete-orphan'))

    order = Column(Integer, nullable=False)

    @validates('schema')
    def validate_attribute(self, key, schema):
        """
        Switches all attributes to the assigned schema
        """
        for attribute in six.itervalues(self.attributes):
            attribute.schema = schema
        return schema

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

    def __copy__(self):
        keys = ('name', 'title', 'description', 'order')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        for attribute in six.itervalues(self.attributes):
            duplicate.attributes[attribute.name] = deepcopy(attribute)
        return duplicate

    @classmethod
    def from_json(cls, data):
        """
        Loads a section from parsed JSON data

        Parameters:
        data -- parsed json data (i.e. a dict)
        """
        attributes = data.pop('attributes')

        section = cls(**data)

        if attributes:
            for key, attribute in six.iteritems(attributes):
                section.attributes[key] = Attribute.from_json(attribute)

        return section

    def to_json(self):
        """
        Serializes to a JSON-ready dictionary
        """
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'attributes': dict([(a.name, a.to_json())
                               for a in six.itervalues(self.attributes)])}


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

    # Overide for maximum character lenght of 20
    name = Column(String(20), nullable=False)

    schema_id = Column(Integer, nullable=False,)

    schema = relationship(
        Schema,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            cascade='all, delete, delete-orphan'),
        doc=u'The schema that this attribute belongs to')

    section = relationship(
        Section,
        secondary=section_attribute_table,
        uselist=False,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            single_parent=True,
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

    @validates('name')
    def validate_name(self, key, name):
        if not RE_VALID_NAME.match(name):
            raise ValueError('Invalid name: "%s"' % name)
        if name in RESERVED_WORDS:
            raise ValueError(
                'Cannot use reserved word as attribute name: %s' % name)
        return name

    @validates('section')
    def validate_section(self, key, section):
        """
        Sets the schema of the attribute to the assigned section
        This happens when a section is assigned directly to an attribute.
        Need to switch over to the section's schema.
        """
        self.schema = section.schema
        return section

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('schema_id', 'order',
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
        for choice in six.itervalues(self.choices):
            duplicate.choices[choice.name] = deepcopy(choice)
        return duplicate

    @classmethod
    def from_json(cls, data):
        """
        Loads a attribute from parsed JSON data

        Parameters:
        data -- parsed json data (i.e. a dict)
        """

        choices = data.pop('choices')

        attribute = cls(**data)

        if choices is not None:
            for key, choice in six.iteritems(choices):
                attribute.choices[key] = Choice.from_json(choice)

        return attribute

    def to_json(self):
        """
        Serializes to a JSON-ready dictionary
        """

        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'is_required': self.is_required,
            'is_collection': self.is_collection,
            'is_private': self.is_private,
            'checksum': self.checksum,
            'value_min': self.value_min,
            'value_max': self.value_max,
            'validator': self.validator,
            'collection_min': self.collection_min,
            'collection_max': self.collection_max,
            'order': self.order,
            'choices': dict([(c.name, c.to_json())
                            for c in six.itervalues(self.choices)])}


# __table_args__ is not accepting this constraint.
# Need to initiate the Index here for now...
Index(
    'uq_attribute_name',
    Attribute.schema_id,
    CaseInsensitive(Attribute.name),
    unique=True)


class Choice(Model, Referenceable, Describeable, Modifiable, Auditable):
    """
    Possible value constraints for an attribute.
    Note objects of this type are not versioned, as they are merely an
    extension of the IAttribute objects. So if the choice constraints
    are to be modified, a new version of the IAttribute object
    should be created.
    """

    __tablename__ = 'choice'

    # Override for maximum character lenght of 8
    name = Column(String(8), nullable=False)

    attribute_id = Column(Integer, nullable=False,)

    attribute = relationship(
        Attribute,
        backref=backref(
            name='choices',
            collection_class=attribute_mapped_collection('name'),
            order_by='Choice.order',
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

    def __copy__(self):
        keys = ('name', 'title', 'description', 'order')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        return copy(self)

    @classmethod
    def from_json(cls, data):
        """
        Loads a choice from parsed JSON data

        Parameters:
        data -- parsed json data (i.e. a dict)
        """
        return cls(**data)

    def to_json(self):
        """
        Serializes to a JSON-ready dictionary
        """
        return {
            'name': self.name,
            'title': self.title,
            'order': self.order}

CheckConstraint(cast(Choice.name, Integer), name='ck_choice_numeric_name')
