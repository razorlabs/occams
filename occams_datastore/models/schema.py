"""
Metadata definitions
"""

from copy import copy, deepcopy
from datetime import datetime
from itertools import chain
import re

from six import iterkeys, iteritems, itervalues
from sqlalchemy import(
    cast,
    sql,
    Table, Column,
    PrimaryKeyConstraint,
    CheckConstraint, UniqueConstraint, ForeignKeyConstraint, Index,
    Boolean, Enum, Date, Integer, String, Unicode, UnicodeText)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, validates
from sqlalchemy.orm.collections import attribute_mapped_collection

from . import DataStoreModel as Model
from .metadata import Referenceable, Describeable, Modifiable
from .auditing import Auditable
from ..utils.sql import CaseInsensitive


RE_VALID_NAME = re.compile(r"""
    ^
    [a-z]               # Must start with character
    [a-z0-9_]*          # Can contains letters digits and underscores
    $
    """, re.I | re.VERBOSE)


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
    name = Column(String, nullable=False)

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

    def itertraverse(self):
        """
        Useful for iterating through attributes as a hierarchy
        """
        for attribute in sorted(itervalues(self.attributes),
                                key=lambda a: a.order):
            if attribute.parent_attribute is None:
                yield attribute

    def iterleafs(self):
        """
        Lists all attributes flattened without their sections
        """
        for attribute in sorted(itervalues(self.attributes),
                                key=lambda a: a.order):
            if attribute.type != 'section':
                yield attribute

    def iterlist(self):
        """
        Flattens the schema into a sorted list of all children
        """
        return chain.from_iterable(a.iterlist() for a in self.itertraverse())

    def __copy__(self):
        keys = ('name', 'title', 'description', 'storage')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        duplicate.categories = set([c for c in self.categories])
        for attribute in self.itertraverse():
            duplicate.attributes[attribute.name] = deepcopy(attribute)
        return duplicate

    @classmethod
    def from_json(cls, data):
        """
        Loads a schema from parsed JSON data

        Parameters:
        data -- parsed json data (i.e. a dict)
        """
        attributes = data.pop('attributes', None)

        schema = cls(**data)

        if data.get('publish_date'):
            schema.publish_date = \
                datetime.strptime(data['publish_date'], '%Y-%m-%d').date()

        if data.get('retract_date'):
            schema.retract_date = \
                datetime.strptime(data['retract_date'], '%Y-%m-%d').date()

        if attributes:
            for key, attribute in iteritems(attributes):
                schema.attributes[key] = Attribute.from_json(attribute)

        return schema

    def to_json(self, deep=False):
        """
        Serializes to a JSON-ready dictionary
        """
        data = {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'storage': self.storage,
            'publish_date': (
                self.publish_date and self.publish_date.isoformat()),
            'retract_date': (
                self.retract_date and self.retract_date.isoformat())}
        if deep:
            data['attributes'] = \
                dict([(a.name, a.to_json(deep)) for a in self.itertraverse()])
        return data


# __table_args__ is not accepting this constraint.
# Need to initiate the Index here for now...
Index(
    'uq_schema_name',
    CaseInsensitive(Schema.name),
    Schema.publish_date,
    unique=True)


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
    name = Column(String(100), nullable=False)

    # Overide for nullable=True
    title = Column(Unicode, nullable=True)

    schema_id = Column(Integer, nullable=False,)

    schema = relationship(
        Schema,
        backref=backref(
            name='attributes',
            collection_class=attribute_mapped_collection('name'),
            order_by='Attribute.order',
            cascade='all, delete, delete-orphan'),
        doc=u'The schema that this attribute belongs to')

    parent_attribute_id = Column(Integer)

    attributes = relationship(
        'Attribute',
        collection_class=attribute_mapped_collection('name'),
        order_by='Attribute.order',
        cascade='all, delete',
        backref=backref(
            name='parent_attribute',
            remote_side='Attribute.id'))

    type = Column(
        Enum(*sorted(['number', 'choice',
                      'date', 'datetime',
                      'string', 'text', 'section',
                      'blob']),
             name='attribute_type'),
        nullable=False)

    is_collection = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql.false(),
        doc='Single or Multiple choice answers')

    is_shuffled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql.false(),
        doc='Display answer choices in random order')

    is_required = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql.false(),
        doc='Forces attribute value to be required')

    is_private = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql.false(),
        doc='Stores Personnally Identifiable Information (PII).')

    is_system = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql.false(),
        doc='Is a variable that can only be managed by underlying system')

    is_readonly = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql.false(),
        doc='The user may not modify this variable')

    widget = Column(
        Enum(*sorted(['checkbox', 'email', 'radio', 'select',
                      'phone']),
             name='attribute_widget'))

    value_min = Column(Integer, doc='Minimum length or value')

    value_max = Column(Integer, doc='Maximum length or value')

    collection_min = Column(Integer, doc='Minimum list length')

    collection_max = Column(Integer, doc='Maximum list length')

    pattern = Column(String, doc='String format regular expression')

    decimal_places = Column(Integer)

    constraint_logic = Column(UnicodeText)

    skip_logic = Column(UnicodeText)

    order = Column(Integer, nullable=False, doc='Display order')

    @validates('name')
    def validate_name(self, key, name):
        if not RE_VALID_NAME.match(name):
            raise ValueError('Invalid name: "%s"' % name)
        if name in RESERVED_WORDS:
            raise ValueError(
                'Cannot use reserved word as attribute name: %s' % name)
        return name

    @validates('schema')
    def validate_schema(self, key, schema):
        """
        Cascade schema setting to children (SA won't do this)
        """
        if self.type == 'section':
            for subattribute in itervalues(self.attributes):
                subattribute.schema = schema
        return schema

    @validates('parent_attribute')
    def validate_parent_attribute(self, key, parent_attribute):
        """
        Pass the schema if being set as a subattribute (SA won't do this)
        """
        if parent_attribute:
            self.schema = parent_attribute.schema
        return parent_attribute

    def itertraverse(self):
        """
        Useful for iterating through attributes as a hierarchy
        """
        return iter(sorted(itervalues(self.attributes), key=lambda a: a.order))

    def iterlist(self):
        """
        Flattens the current attribute into an sorted list with all children
        """
        yield self
        if self.type == 'section':
            for a in chain.from_iterable(
                    a.iterlist() for a in self.itertraverse()):
                yield a

    def iterchoices(self):
        """
        Useful for iterating through attributes in order
        """
        # TODO: Maybe apply shuffling here?
        return iter(sorted(itervalues(self.choices), key=lambda c: c.order))

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['parent_attribute_id'],
                refcolumns=['attribute.id'],
                name='fk_%s_attribute_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('schema_id', 'order',
                             name='uq_%s_order' % cls.__tablename__,
                             deferrable=True,
                             initially='DEFERRED'),
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
                name='ck_%s_valid_value' % cls.__tablename__),
            CheckConstraint(
                "CASE WHEN type != 'number' THEN decimal_places IS NULL END",
                name='ck_%s_number_decimal_places' % cls.__tablename__),
            CheckConstraint(
                """
                CASE
                    WHEN widget IS NOT NULL THEN
                        CASE type
                            WHEN 'string' THEN widget IN ('phone', 'email')
                            WHEN 'choice' THEN
                                CASE
                                    WHEN is_collection
                                        THEN widget IN ('select', 'checkbox')
                                    ELSE widget IN ('select', 'radio')
                                END
                        END
                END
                """,
                name='ck_%s_type_widget' % cls.__tablename__))

    def __copy__(self):
        keys = (
            'name', 'title', 'description', 'type', 'is_collection',
            'is_required', 'is_system', 'is_readonly', 'is_shuffled',
            'widget', 'skip_logic', 'constraint_logic',
            'decimal_places',
            'collection_min', 'collection_max', 'value_min', 'value_max',
            'pattern', 'order')
        return self.__class__(**dict([(k, getattr(self, k)) for k in keys]))

    def __deepcopy__(self, memo):
        duplicate = copy(self)
        for choice in itervalues(self.choices):
            duplicate.choices[choice.name] = deepcopy(choice)
        for attribute in itervalues(self.attributes):
            duplicate.attributes[attribute.name] = deepcopy(attribute)
        return duplicate

    @classmethod
    def from_json(cls, data):
        """
        Loads a attribute from parsed JSON data

        Parameters:
        data -- parsed json data (i.e. a dict)
        """

        attributes = data.pop('attributes', None)
        choices = data.pop('choices', None)

        attribute = cls(**data)

        if attributes:
            for key, sub in iteritems(attributes):
                attribute.attributes[key] = Attribute.from_json(sub)

        if choices:
            for key, choice in iteritems(choices):
                attribute.choices[key] = Choice.from_json(choice)

        return attribute

    def to_json(self, deep=False):
        """
        Serializes to a JSON-ready dictionary
        """

        data = {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'is_required': self.is_required,
            'is_collection': self.is_collection,
            'is_private': self.is_private,
            'is_system': self.is_system,
            'is_readonly': self.is_readonly,
            'is_shuffled': self.is_shuffled,
            'value_min': self.value_min,
            'value_max': self.value_max,
            'pattern': self.pattern,
            'decimal_places': self.decimal_places,
            'constraint_logic': self.constraint_logic,
            'skip_logic': self.skip_logic,
            'collection_min': self.collection_min,
            'collection_max': self.collection_max,
            'order': self.order,
        }

        if deep:
            data['attributes'] = \
                dict([(a.name, a.to_json(deep))
                     for a in itervalues(self.attributes)])
            data['choices'] = \
                dict([(c.name, c.to_json(deep))
                     for c in itervalues(self.choices)])

        return data

    def apply(self, data):
        self.name = data['name']
        self.title = data['title']
        self.description = data['description']
        self.type = data['type']

        if self.type != 'section':
            self.is_required = data['is_required']
            self.is_private = data['is_private']
            self.is_readonly = data['is_readonly']
            self.is_system = data['is_system']

        if self.type in ('string', 'number', 'choice'):
            self.value_min = data['value_min']
            self.value_max = data['value_max']

        if self.type == 'number':
            self.decimal_places = data['decimal_places']

        if self.type == 'string':
            self.pattern = data['pattern']

        if self.type == 'choice':
            self.is_collection = data['is_collection']
            self.is_shuffled = data['is_shuffled']

            new_codes = set(c['name'] for c in data['choices'])
            old_codes = list(iterkeys(self.choices))

            for code in old_codes:
                if code not in new_codes:
                    del self.choices[code]

            for i, choice_data in enumerate(data['choices']):
                name = choice_data['name']
                if name in self.choices:
                    choice = self.choices[name]
                else:
                    self.choices[name] = choice = Choice(name=name)
                choice.title = choice_data['title']
                choice.order = i


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
                             name='uq_%s_order' % cls.__tablename__,
                             deferrable=True,
                             initially='DEFERRED'),)

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

    def to_json(self, deep=False):
        """
        Serializes to a JSON-ready dictionary
        """
        return {
            'name': self.name,
            'title': self.title,
            'order': self.order}


# It's OK if this errors out in PG since that means the constraint failed
CheckConstraint(cast(Choice.name, Integer) != sql.null(),
                name='ck_choice_numeric_name')
