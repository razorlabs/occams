""" Data Definition Library

    The entities defined within this module are the foundation for the EAV/CR
    framework implementation for use in the data store utility. Not that these
    table definitions are independent of the interfaces defined by this package.
    The reason for this is so that these models can be reused differently
    in a separate script/application  if need be. Though, importing this module
    can also result in circumventing the entire purpose of the package as well.
    Thus, because the are not implementations of the the interfaces, they can
    be used freely in the utility implementations instead.

    More information on EAV/CR:
    http://www.ncbi.nlm.nih.gov/pmc/articles/PMC61391/

    Note that the models defined in this module are mapped to a database.
    Therefore, great care should be taken when updating this file, as it may
    cause live systems to fall out of sync.

    TODO: (mmartinez)
        * Cascade update/deletes
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

# Base class for declarative syntax on our models
Model = declarative_base()

def setup(engine):
    """ This method will setup the database models using the specified engine
        bind. This is simply a convenience method for creating the database
        tables as well as keeping this module self-contained

        Arguments:
            engine: A sqlalchemy engine object.

        Returns:
            N\A
    """
    Model.metadata.create_all(bind=engine, checkfirst=True)

# -----------------------------------------------------------------------------
# Value Storage
# -----------------------------------------------------------------------------

class Keyword(Model):
    """ Used to associate multiple titles for an entity instance. The titles can
        be shorthand alternate names or actual 'official' synonyms. The main
        purpose of this table is simply to make it more convenient for searching
        for instances with specific names.

        Note: keyword title uniqueness is not enforced, therefore multiple
              instances may have similar keywords.

        Attributes:
            id: (int) machine generated id number
            instance_id: (int) reference to the instance this keyword belongs to
            instance: (Instance) relation object to the Instnace model
            title: (str) alternate title or synonym.
            is_synonym: (bool) Flag indicating the type of keyword
    """
    __tablename__ = 'keyword'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    title = sa.Column(sa.Unicode, nullable=False, index=True)

    is_synonym = sa.Column(sa.Boolean, nullable=False, default=True)

class Instance(Model):
    """ A bona fide instance of a schema.

        Attributes:
            id: (int) machine generated id number
            schema_id: (int) reference to the schema this is an instance of
                (for verification/lookup purposes)
            schema: (Schema) relation object to the Schema model
            title: (str) a title for the instance. If none is suplied, the
                client application should generate one.
            keywords: (list) a relation list of Keywords
            description: (str) a  description of the instance
            is_active: (bool) if the instnace is marked as inactive, it should
                not display in any form of reporting.
            create_date: (datetime) the date this model instance was created
            modified_date: (datetime) the date this model instance was modified
    """
    __tablename__ = 'instance'

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey('schema.id'),
                          nullable=False)

    schema = orm.relation('Schema', uselist=False)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    keywords = orm.relation('Keyword')

    description = sa.Column(sa.Unicode, nullable=False)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

class Binary(Model):
    """ A binary EAV value.

        TODO: it's a bit unclear how this object will be used, extensions might
              be a little naive (perhaps store MIME types instead?)

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            extension: (str) the extension of the file being stored
            value: (binary) the physical value being stored
    """
    __tablename__ = 'binary'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    extension = sa.Column(sa.Unicode)

    value = sa.Column(sa.BLOB, nullable=False)

class Datetime(Model):
    """ A datetime EAV value.

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value: (datetime) the physical value being stored
    """
    __tablename__ = 'datetime'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    value = sa.Column(sa.DateTime, nullable=False)

# Optimization for lookup
sa.Index('datetime_attribute_value', Datetime.attribute_id, Datetime.value)

class Integer(Model):
    """ A integer EAV value.

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value: (int) the physical value being stored
    """
    __tablename__ ='integer'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    value = sa.Column(sa.Integer, nullable=False)

# Optimization for lookup
sa.Index('integer_attribute_value', Integer.attribute_id, Integer.value)

class Range(Model):
    """ A range EAV value.

        This model object is a built-in as a convenience feature for integer
        range values. Only integers are supported currently.

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value_min: (int) the low value
            value_max: (int) the high value
            value: (int) the range tuple being stored
    """
    __tablename__ = 'range'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    value_low = sa.Column(sa.Integer, nullable=False)

    value_high = sa.Column(sa.Integer, nullable=False)

    def _get_value(self):
        return (self.value_low, self.value_high)

    def _set_value(self, value):
        (self.value_low, self.value_high) = value

    value = orm.synonym('_value', descriptor=property(_get_value, _set_value))

# Optimization for lookup
sa.Index('range_attribute_value_low', Range.attribute_id, Range.value_low)
sa.Index('range_attribute_value_high', Range.attribute_id, Range.value_high)
sa.Index('range_attribute_value', Range.value_low, Range.value_high)

class Real(Model):
    """ A real EAV value.

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value: (int) the physical value being stored
    """
    __tablename__ ='real'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    value = sa.Column(sa.Float, nullable=False)

# Optimization for lookup
sa.Index('real_attribute_value', Real.attribute_id, Real.value)

class Selection(Model):
    """ A selection EAV value (into a vocabulary of choices)

        This type is simply a reference into a vocabulary list. This seriously
        needs to be re-thought, because if and entire network consists of lists,
        then the entire purpose of the EAV is circumvented. The reason, though
        this is needed is because we need to keep track of the selection made
        in order to keep track of a history.

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value: (int) a reference to the vocabulary item
    """
    __tablename__ ='selection'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    term_id = sa.Column('value', sa.Integer, sa.ForeignKey('term.id'),
                        nullable=False)

    value = orm.relation('Term', uselist=False)

# Optimization for lookup
sa.Index('selection_attribute_value', Real.attribute_id, Real.value)

class Object(Model):
    """ An object EAV value.

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value: (int) a reference to an Instance
            order: (int) for list of objects, this can be used for ordering them
                (seems to make more sense for associations?)
    """
    __tablename__ ='object'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance',
                            primaryjoin='Instance.id == Object.instance_id',
                            uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    value = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),)

    order = sa.Column(sa.Integer, nullable=False, default=1)

# Optimization for lookup
sa.Index('object_attribute_value', Object.attribute_id, Object.value)

class String(Model):
    """ A string EAV value.

        Note that this model handles strings up to 1,024 characters

        Attributes:
            instnace_id: (int) a reference to the instance
            instance: (Instance) relation to the target instance
            attribute_id: (int) a reference to the attribute this value is for
                (for validation purposes)
            attribute: (Attribute) relation to the target attribute
            value: (str) the physical value being stored
    """
    __tablename__ ='string'

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey('instance.id'),
                            nullable=False)

    instance = orm.relation('Instance', uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey('attribute.id'),
                            nullable=False)

    attribute = orm.relation('Attribute', uselist=False)

    value = sa.Column(sa.Unicode, nullable=False)

# Optimization for lookup
sa.Index('string_attribute_value', String.attribute_id, String.value)

# -----------------------------------------------------------------------------
# Metadata specifications
# -----------------------------------------------------------------------------

# Joining table for base class representation
hierarchy_table = sa.Table('hierarchy', Model.metadata,
    sa.Column('parent_id', sa.ForeignKey('specification.id'), nullable=False,
              primary_key=True),
    sa.Column('child_id', sa.ForeignKey('specification.id'), nullable=False,
              primary_key=True),
    )

# A hackish way to include additional schemata when a 'main' schemata is
# requested.
include_table = sa.Table('include', Model.metadata,
    sa.Column('main_id', sa.ForeignKey('specification.id'), nullable=False,
              primary_key=True),
    sa.Column('include_id', sa.ForeignKey('specification.id'), nullable=False,
              primary_key=True),
    )

class Specification(Model):
    """ Specification entity for class names. This is an independent model that
        keeps track of the name spaces for the available classes.

        Attributes:
            id: (int) machine generated id number
            bases: (list) list of bases classes this specification extends
            children: (list) a convenience attribute to also allow the retrieval
                of child classes
            name: (str) the module name of the specification. It must be unique,
                client code should have a graceful way for duplicate names
                (perhaps append an instance number?)
            documentation: (str) documentation for the specification. this
                attribute is required, as it would be extremely useful to know
                what types of classes are being used in the data store.
            title: (str) the human-readable title of the class
            description: (str) the human-readable instructions for the class
            is_association: (bool) is the specification an association class?
            is_virtual: (bool) is the specification an virtual class? (i.e. a
                class without an instance, such as a medline)
            is_eav: (bool) is the specification EAV-only? If false, and entry
                should have a corresponding traditional table. (Currently
                unsupported)
            create_date: (datetime) the date this model instance was created
            modified_date: (datetime) the date this model instance was modified
    """
    __tablename__ = 'specification'

    id = sa.Column(sa.Integer, primary_key=True)

    bases = orm.relation('Specification',
                         secondary=hierarchy_table,
                         primaryjoin=(id == hierarchy_table.c.child_id),
                         secondaryjoin=(id == hierarchy_table.c.parent_id),
                         foreign_keys=[hierarchy_table.c.parent_id,
                                       hierarchy_table.c.child_id,
                                       ]
                         )

    children = orm.relation('Specification',
                            secondary=hierarchy_table,
                            primaryjoin=(id == hierarchy_table.c.parent_id),
                            secondaryjoin=(id == hierarchy_table.c.child_id),
                            foreign_keys=[hierarchy_table.c.child_id,
                                          hierarchy_table.c.parent_id,
                                          ]
                            )

    includes = orm.relation('Specification',
                            secondary=include_table,
                            primaryjoin=(id == include_table.c.main_id),
                            secondaryjoin=(id == include_table.c.include_id),
                            foreign_keys=[include_table.c.main_id,
                                          include_table.c.include_id,
                                          ]
                            )

    name = sa.Column(sa.Unicode, nullable=False, unique=True)

    documentation = sa.Column(sa.Unicode, nullable=False)

    title = sa.Column(sa.Unicode)

    description = sa.Column(sa.Text)

    is_tabable = sa.Column(sa.Boolean, nullable=False, default=False)

    is_association = sa.Column(sa.Boolean, nullable=False, default=False)

    is_virtual = sa.Column(sa.Boolean, nullable=False, default=False)

    is_eav = sa.Column(sa.Boolean, nullable=False, default=False)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

fieldset_fieldsetitem_table = sa.Table('fieldset_fieldsetitem', Model.metadata,
    sa.Column('fieldset_id', sa.ForeignKey('fieldset.id'), nullable=False,
              primary_key=True),
    sa.Column('item_id', sa.ForeignKey('fieldsetitem.id'), nullable=False,
              primary_key=True),
    )

class FieldsetItem(Model):
    """
    """
    __tablename__ = 'fieldsetitem'

    id = sa.Column(sa.Integer, primary_key=True)

    name = sa.Column(sa.Unicode, nullable=False)

    order = sa.Column(sa.Integer, nullable=False, default=1)


class Fieldset(Model):
    """
    """
    __tablename__ = 'fieldset'

    id = sa.Column(sa.Integer, primary_key=True)

    name = sa.Column(sa.Unicode, nullable=False)

    label = sa.Column(sa.Unicode, nullable=False)

    description = sa.Column(sa.Unicode)

    order = sa.Column(sa.Integer, nullable=False, default=1)

    fields = orm.relation('FieldsetItem',
                          secondary=fieldset_fieldsetitem_table,
                          order_by='FieldsetItem.order')

schema_fieldset_table = sa.Table('schema_fieldset', Model.metadata,
    sa.Column('schema_id', sa.ForeignKey('schema.id'), nullable=False,
              primary_key=True),
    sa.Column('fieldset_id', sa.ForeignKey('fieldset.id'), nullable=False,
              primary_key=True),
    )

class Schema(Model):
    """ The model where versioning takes place. This model uses a specification
        to define a version for it. Once this model is created, attributes and
        invariants can be associated with in order to represent a state of the
        schemata at a point in time.

        Note: the (specification, create_date) tuple is used as the unique
            version value.

        Attribute:
            id: (int) machine generated id number
            specification_id: (int) a reference to the specification this
                creates a versioned schema for.
            specification: (Specification) a relation to the specification model
            attributes: (list) a list of Attributes for this schema
            invariants: (list) a list of Invariants for this schema
            create_date: (datetime) the date this model instance was created
            modified_date: (datetime) the date this model instance was modified
    """
    __tablename__ = 'schema'

    id = sa.Column(sa.Integer, primary_key=True)

    specification_id = sa.Column(sa.Integer, sa.ForeignKey('specification.id'),
                                 nullable=False)

    specification = orm.relation('Specification', uselist=False)

    attributes = orm.relation('Attribute', order_by='Attribute.order')

    invariants = orm.relation('Invariant')

    fieldsets = orm.relation('Fieldset',
                             secondary=schema_fieldset_table,
                             order_by='Fieldset.order')

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    __table_args = (
        sa.UniqueConstraint('specification_id', 'create_date'),
        {})

class Invariant(Model):
    """ An invariant definition for a class.

        Attributes:
            id: (int) machine generated id number
            schema_id: (int) a reference to the schema this invariant is for
            name: (str) the name of the invariant. Should not contain spaces.
    """
    __tablename__ = 'invariant'

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey('schema.id'),
                          nullable=False)

    name = sa.Column(sa.Unicode, nullable=False)


class Attribute(Model):
    """ An attribute declaration.

        This is a special table in that it serves as a joining table between
        fields and schemata, but with extra meta data associated with the join.

        Attributes:
            id: (int) machine generated id number
            schema_id: (int) a reference to the schema this attribute belongs to
            field_id: (int) a reference to the field that contains metadata
                about this attribute.
            field: (Field) a relation to the field
            name: (str) the name of the attribute (i.e. the property name)
            order: (int) the order in which the attribute appears in the schema
            create_date: (datetime) the date this model instance was created
            modified_date: (datetime) the date this model instance was modified

    """
    __tablename__ = 'attribute'

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey('schema.id'),
                          nullable=False)

    field_id = sa.Column(sa.Integer, sa.ForeignKey('field.id'), nullable=False)

    field = orm.relation('Field', uselist=False)

    name = sa.Column(sa.Unicode, nullable=False)

    order = sa.Column(sa.Integer, nullable=False, default=1)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        sa.UniqueConstraint('schema_id', 'name'),
        {})

class Field(Model):
    """ Attribute display metadata (i.e. Field). Describes how the attribute
        should be used as well as useful constraint/validation meta data. Every
        time an attribute must define a new field (or removed for that matter),
        the source schema should be 'versioned'.

        Attributes:
            id: (int) machine generated id number
            title: (str) human readable title (for forms)
            description: (str) human readable description (for forms)
            documentation: (str) comments about this field
            type_id: (int) a reference to the type for this field.
            type: (Type) a relation to the type
            schema_id: (int) a reference to a schema (only applicable for object
                types) and used for enforcing the schema type for an object.
            schema: (Schema) a relation to the schema enforcement
            vocabulary_id: (int) a reference to a vocabulary of possible answer
                choices
            vocabulary: (Vocabulary) a relation to the vocabulary
            is_searchable: (bool) True if the attribute should be added to
                the appliations search form. (Only if applicable)
            is_required: (bool) True if required value in a form display
            is_inline_image: (bool) ?!!? see paper...
            is_repeatable: (bool) only applicable for associations. see paper...
            minimum: (int) depending on the context, this attribute may be
                used for storing the mininum length of a string, size of an int,
                or number of instances, etc.
            maximum: (int) depending on the context, this attribute may be
                used for storing the maximum length of a string, size of an int,
                or number of instances, etc.
            width: (int) display widget parameter for width
            height: (int) display widget parameter for height
            url: (str) a url query string for virtual classes.
            directive_*: these are inteded for direct use in plone.directives...
                TODO: these need to go away somehow....
            create_date: (datetime) the date this model instance was created
            modified_date: (datetime) the date this model instance was modified
    """

    __tablename__ = 'field'

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False)

    description = sa.Column(sa.Unicode)

    documentation = sa.Column(sa.Unicode)

    type_id = sa.Column(sa.Integer, sa.ForeignKey('type.id'), nullable=False)

    type = orm.relation('Type', uselist=False)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey('schema.id'))

    schema = orm.relation('Schema', uselist=False)

    vocabulary_id = sa.Column(sa.Integer, sa.ForeignKey('vocabulary.id'))

    vocabulary = orm.relation('Vocabulary')

    default = sa.Column(sa.Unicode)

    is_list = sa.Column(sa.Boolean, nullable=False, default=False)

    is_readonly = sa.Column(sa.Boolean, nullable=False, default=False)

    is_searchable = sa.Column(sa.Boolean, nullable=False, default=False)

    is_required = sa.Column(sa.Boolean, nullable=False, default=False)

    is_inline_image = sa.Column(sa.Boolean)

    is_repeatable = sa.Column(sa.Boolean, nullable=False, default=False)

    minimum = sa.Column(sa.Integer)

    maximum = sa.Column(sa.Integer)

    width = sa.Column(sa.Integer)

    height = sa.Column(sa.Integer)

    url = sa.Column(sa.Unicode)

    directive_widget = sa.Column(sa.Unicode)

    directive_omitted = sa.Column(sa.Boolean)

    directive_no_ommit = sa.Column(sa.Unicode)

    directive_mode = sa.Column(sa.Unicode)

    directive_before = sa.Column(sa.Unicode)

    directive_after = sa.Column(sa.Unicode)

    directive_read = sa.Column(sa.Unicode)

    directive_write = sa.Column(sa.Unicode)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

class Type(Model):
    """ Represents a supported type.

        TODO: if more database vendors supported ENUM, this model would be
            unnesessary.

        Attributes:
            id: (int) machine generated id number
            title: (str) the human-reable name of this type
            description: (str) an optional description
    """
    __tablename__ = 'type'

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    description = sa.Column(sa.Text)

# Joining table for vocabulary terms
vocabulary_term_table = sa.Table('vocabulary_term', Model.metadata,
    sa.Column('vocabulary_id', sa.Integer, sa.ForeignKey('vocabulary.id'),
              nullable=False, primary_key=True),
    sa.Column('term_id', sa.Integer, sa.ForeignKey('term.id'),
              nullable=False, primary_key=True),
    )

class Vocabulary(Model):
    """ A vocabulary.

        Attributes:
            id: (int) machine generated id number
            title: (str) the human-reable name of this vocabulary
            description: (str) an optional description
            terms: (list) the list of terms for this vocabulary
    """
    __tablename__ = 'vocabulary'

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, index=True)

    description = sa.Column(sa.Unicode)

    terms = orm.relation('Term', secondary=vocabulary_term_table)

class Term(Model):
    """ An indivudal term for a vocabulary.

        Note: The way this is implemented could possibly override the whole
            concept of EAV itself, but we'll see after some testing...

        Attributes:
            id: (int) machine generated id number
            title: (str) the human-reable name of term
            token: (str) a one-to-one mapping token for the value
            value_*: the currently implemented way for the term value that
                seriously needs some reworking.
            value: (object) the value for this term
            description: (str) an optional description
            terms: (list) the list of terms for this vocabulary
    """
    __tablename__ = 'term'

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode)

    token = sa.Column(sa.Unicode, nullable=False, index=True)

    value_str = sa.Column(sa.Unicode)

    value_int = sa.Column(sa.Integer)

    value_real = sa.Column(sa.Float)

    value_range_low = sa.Column(sa.Integer)

    value_range_high = sa.Column(sa.Integer)

    order = sa.Column(sa.Integer, nullable=False, default=1)

    def _get_value(self):
        """Determines the correct value and returns it"""
        value = self.value_int is not None and self.value_int or \
                self.value_real is not None and self.value_real or \
                self.value_str is not None and self.value_str or \
                None

        if self.value_range_low and self.value_range_high:
            value = (self.value_range_low, self.value_range_high)

        if value is None:
            raise Exception('TERM ITEM NOT FOUND')

        return value

    def _set_value(self, value):
        """Sets the value to the paramter's value"""
        if isinstance(value, int):
            self.value_int = value
        elif isinstance(value, float):
            self.value_real = value
        elif isinstance(value, (str, unicode)):
            self.value_str = unicode(value)
        elif isinstance(value, tuple) and len(tuple) == 2:
            (self.value_range_low, self.value_range_high) = value
        else:
            raise Exception('Unable to determine type: %s'  % value)

    value = property(_get_value, _set_value, None, 'The value stored')

# -----------------------------------------------------------------------------
# Domains and Subjects
# -----------------------------------------------------------------------------

class Curator(Model):
    """ A person curating the data (i.e. manager) """
    __tablename__ = 'curator'

    id = sa.Column(sa.Integer, primary_key=True)

subject_instance_table = sa.Table('subject_instance', Model.metadata,
    sa.Column('subject_id', sa.ForeignKey('subject.id'), nullable=False,
              primary_key=True),
    sa.Column('instance_id', sa.ForeignKey('instance.id'), nullable=False,
              primary_key=True),
    )

class Subject(Model):
    """ We keep track of subjects here and reference them throughout the
        database using an internal identifier.

        Attributes:
            id: (int) machine generated id number
            uid: (int) an external reference number
    """
    __tablename__ = 'subject'

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, nullable=False, unique=True)

    uid = sa.Column(sa.Integer, nullable=False, index=True)

    nurse_email = sa.Column(sa.Unicode)

    aeh = sa.Column(sa.Unicode, index=True)

    instances = orm.relation('Instance', secondary=subject_instance_table)

class Enrollment(Model):
    """ Links a Subject to a Domain.

        Attributes:
            id: (int) machine generated id
            domain_id: (int) reference to the domain table of the enrollment
            domain: (Domain) relation to the Domain object
            subject_id: (int) referene to the subject that is being enrolled
            subject: (Subject) relation to the Subject object
            start_date: (date) date that the subject was enrolled
            consent_date: (date) date the the subject updated their consent (not
                necessarily the start date)
            stop_date: (date) date the subject ended enrollment
            eid: (str) a special index number to keep track of custom
                identifiers for the enrollment itself
            create_date: (datetime) date object is create
            modify_date: (datetime) date object is modified
    """
    __tablename__ = 'enrollment'

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, nullable=False, unique=True)

    domain_id = sa.Column(sa.Integer, sa.ForeignKey('domain.id'),
                            nullable=False)

    domain = orm.relation('Domain', uselist=False)

    subject_id = sa.Column(sa.Integer, sa.ForeignKey('subject.id'),
                           nullable=False)

    subject = orm.relation('Subject', uselist=False)

    start_date = sa.Column(sa.Date, nullable=False)

    consent_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    eid = sa.Column(sa.Unicode, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    __table_args__ = (
        sa.UniqueConstraint('domain_id', 'subject_id', 'start_date'),
        {})

visit_protocol_table = sa.Table('visit_protocol', Model.metadata,
    sa.Column('visit_id', sa.ForeignKey('visit.id'), nullable=False,
              primary_key=True),
    sa.Column('protocol_id', sa.ForeignKey('protocol.id'), nullable=False,
              primary_key=True),
    )

visit_enrollment_table = sa.Table('visit_enrollment', Model.metadata,
    sa.Column('visit_id', sa.ForeignKey('visit.id'), nullable=False,
              primary_key=True),
    sa.Column('enrollment_id', sa.ForeignKey('enrollment.id'), nullable=False,
              primary_key=True),
    )

visit_instance_table = sa.Table('visit_instance', Model.metadata,
    sa.Column('visit_id', sa.ForeignKey('visit.id'), nullable=False,
              primary_key=True),
    sa.Column('instance_id', sa.ForeignKey('instance.id'), nullable=False,
              primary_key=True),
    )

class Visit(Model):
    """ Attributes:
            id: (int) machine generated id
            enrollments: (list) relation list to Enrollments that indicate the
                domains this visit is associated with
            protocols: (list) relation list to Protocols that indicate the
                progress
                of the visit
            visit_date: (date) the date the visit occured
    """
    __tablename__ = 'visit'

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, nullable=False, unique=True)

    enrollments = orm.relation('Enrollment', secondary=visit_enrollment_table)

    protocols = orm.relation('Protocol', secondary=visit_protocol_table)

    instances = orm.relation('Instance', secondary=visit_instance_table)

    visit_date = sa.Column(sa.Date, nullable=False)

domain_schema_table = sa.Table('domain_schema', Model.metadata,
    sa.Column('domain_id', sa.Integer, sa.ForeignKey('domain.id'),
              nullable=False, primary_key=True),
    sa.Column('schema_id', sa.Integer, sa.ForeignKey('schema.id'),
              nullable=False, primary_key=True)
    )

class Domain(Model):
    """ Attributes:
            id: (int) machine generated id number
            code: (unicode) the domain's short hand code (indexed)
            title: (unicode) the domains' human readble title (unique)
            consent_date: (date) the date of the new consent
            schemata: (list) available schemata
    """
    __tablename__ = 'domain'

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, nullable=False, unique=True)

    code = sa.Column(sa.Unicode, nullable=False, index=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    consent_date = sa.Column(sa.Date, nullable=False)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    schemata = orm.relation('Schema', secondary=domain_schema_table)

protocol_schema_table = sa.Table('protocol_schema', Model.metadata,
    sa.Column('protocol_id', sa.Integer, sa.ForeignKey('protocol.id'),
              nullable=False, primary_key=True),
    sa.Column('schema_id', sa.Integer, sa.ForeignKey('schema.id'),
              nullable=False, primary_key=True)
    )

class Protocol(Model):
    """ Required schemata for a particular cycle in a domain.

        Attributes:
            id: (int) machine generated id number
            domain_id: (int) reference to domain this protocol belongs to
            domain: (Domain) relation to Domain object
            schemata: (list) Schema objects that are required
            cycle: (int) week number
            threshold: (int) future-proof field for exempting cycles
            is_active: (bool) if set, indicates the entry is in active use
            create_date: (datetime) date object is create
            modify_date: (datetime) date object is modified
    """
    __tablename__ = 'protocol'

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, nullable=False, unique=True)

    domain_id = sa.Column(sa.Integer, sa.ForeignKey('domain.id'),
                          nullable=False)

    domain = orm.relation('Domain', uselist=False)

    schemata = orm.relation('Schema', secondary=protocol_schema_table)

    cycle = sa.Column(sa.Integer, nullable=False)

    threshold = sa.Column(sa.Integer)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

# -----------------------------------------------------------------------------
# Specimen and Aliquots
# -----------------------------------------------------------------------------

# TODO: (mmartinez) Perhaps in the future, we'll integrate this into the
#     EAV once it's optimized to handle the large bulk of data this table will
#     contain.

class SpecimenAliquotTerm(Model):
    """
    . . .
    """
    __tablename__ = 'specimen_aliquot_term'

    id = sa.Column(sa.Integer, primary_key=True)

    vocabulary_name = sa.Column(sa.Unicode, nullable=False, index=True)

    title = sa.Column(sa.Unicode)

    token = sa.Column(sa.Unicode, nullable=False)

    value = sa.Column(sa.Unicode, nullable=False)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    __table_args = (
        sa.UniqueConstraint('vocabulary_name', 'token', 'value'),
        {})

class Specimen(Model):
    """ Speccialized table for specimen data. Note that only one specimen can be
        drawn from a patient/protocol/type.

        Attributes:
            id: (int) machine generated primary key
            subject_id: (int) reference to the subject this specimen was
                drawn from
            subject: (object) the relation to the subject
            protocol_id: (int) reference to the protocol this specimen was
                drawn for
            protocol: (object) the relation to the protocol
            state: (str) current state of the specimen
            collect_date: (datetime) the date/time said specimen was collected
            type: (str) the type of specimen
            destination: (str) the destination of where the specimen is sent to.
            tubes: (int) number of tubes collected (optional, if applicable)
            volume_per_tube: (int) volume of each tube (optional, if applicable)
            notes: (str) optinal notes that can be entered by users (optional)
            aliquot: (list) convenience relation to the aliquot parts generated
                from this speciemen
            is_active: (bool) internal marker to indicate this entry is
                being used.
            create_date: (datetime) internal metadata of when entry was created
            modify_date: (datetime) internal metadata of when entry was modified
    """
    __tablename__ = 'specimen'

    id = sa.Column(sa.Integer, primary_key=True)

    subject_id = sa.Column(sa.Integer, sa.ForeignKey('subject.id'),
                           nullable=False)

    subject = orm.relation('Subject', uselist=False)

    protocol_id = sa.Column(sa.Integer, sa.ForeignKey('protocol.id'),
                            nullable=False)

    protocol = orm.relation('Protocol', uselist=False)

    state_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    state = orm.relation('SpecimenAliquotTerm',
                         uselist=False,
                         primaryjoin=state_id == SpecimenAliquotTerm.id
                         )

    collect_date = sa.Column(sa.Date)

    collect_time = sa.Column(sa.Time)

    type_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    type = orm.relation('SpecimenAliquotTerm',
                        uselist=False,
                        primaryjoin=type_id == SpecimenAliquotTerm.id
                        )

    destination_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    destination = orm.relation('SpecimenAliquotTerm',
                               uselist=False,
                               primaryjoin=
                                destination_id == SpecimenAliquotTerm.id
                               )

    tubes = sa.Column(sa.Integer)

    tupe_type_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    tube_type = orm.relation('SpecimenAliquotTerm',
                             uselist=False,
                             primaryjoin=tupe_type_id == SpecimenAliquotTerm.id
                             )

    notes = sa.Column(sa.Unicode)

    aliquot = orm.relation('Aliquot')

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    __table_args = (
        sa.UniqueConstraint('subject_id', 'protocol_id', 'type'),
        {})

sa.Index('specimen_subject_id', Specimen.subject_id)
sa.Index('specimen_protocol_id', Specimen.protocol_id)
sa.Index('specimen_state_id', Specimen.state_id)
sa.Index('specimen_type_id', Specimen.type_id)
sa.Index('specimen_destination_id', Specimen.destination_id)
sa.Index('specimen_tube_type_id', Specimen.tupe_type_id)

class AliquotHistory(Model):
    """ Keeps track of aliquot state history. """
    __tablename__ = 'aliquot_history'

    id = sa.Column(sa.Integer, primary_key=True)

    aliquot_id = sa.Column(sa.Integer, sa.ForeignKey('aliquot.id'),
                           nullable=False)

    state_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    state = orm.relation('SpecimenAliquotTerm',
                         uselist=False,
                         primaryjoin=state_id == SpecimenAliquotTerm.id
                         )


    action_date = sa.Column(sa.DateTime, nullable=False)

    to = sa.Column(sa.Unicode, nullable=False)

class Aliquot(Model):
    """ Specialized table for aliquot parts generated from a specimen.

        Attributes:
            id: (int) machine generated primary key
            specimen_id: (int) the specimen this aliquot was generated from
    """
    __tablename__ = 'aliquot'

    id = sa.Column(sa.Integer, primary_key=True)

    specimen_id = sa.Column(sa.Integer, sa.ForeignKey('specimen.id'),
                            nullable=False)

    specimen = orm.relation('Specimen', uselist=False)

    type_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    type = orm.relation('SpecimenAliquotTerm',
                        uselist=False,
                        primaryjoin=type_id == SpecimenAliquotTerm.id
                        )

    volume = sa.Column(sa.Float)

    cell_amount = sa.Column(sa.Float)

    state_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    state = orm.relation('SpecimenAliquotTerm',
                         uselist=False,
                         primaryjoin=state_id == SpecimenAliquotTerm.id
                         )

    store_date = sa.Column(sa.Date)

    freezer = sa.Column(sa.Unicode)

    rack = sa.Column(sa.Unicode)

    box = sa.Column(sa.Unicode)

    storage_site_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    storage_site = orm.relation('SpecimenAliquotTerm',
                                uselist=False,
                                primaryjoin=\
                                    storage_site_id == SpecimenAliquotTerm.id
                                )

    thawed_num = sa.Column(sa.Integer)

    analysis_status_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    analysis_status = orm.relation('SpecimenAliquotTerm',
                                   uselist=False,
                                   primaryjoin=\
                                    analysis_status_id == SpecimenAliquotTerm.id
                                   )

    sent_date = sa.Column(sa.Date)

    sent_name = sa.Column(sa.Unicode)

    notes = sa.Column(sa.Unicode)

    special_instruction_id = sa.Column(sa.Integer,
                              sa.ForeignKey('specimen_aliquot_term.id'),
                              nullable=False
                              )

    special_instruction = orm.relation('SpecimenAliquotTerm',
                                uselist=False,
                                primaryjoin=\
                                    special_instruction_id == SpecimenAliquotTerm.id
                                )


    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


sa.Index('aliquot_specimen_id', Aliquot.specimen_id)
sa.Index('aliquot_type_id', Aliquot.type_id)
sa.Index('aliquot_state_id', Aliquot.state_id)
sa.Index('aliquot_storage_site_id', Aliquot.storage_site_id)
sa.Index('aliquot_analysis_status_id', Aliquot.analysis_status_id)
sa.Index('aliquot_special_instruction_id', Aliquot.special_instruction_id)


class Drug(Model):
    """ A known drug.
    """

    __tablename__ = 'drug'

    id = sa.Column(sa.Integer, primary_key=True)

    code = sa.Column(sa.Unicode, nullable=False, unique=True)

    recommended_dose = sa.Column(sa.Float)

    drug_category_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('drug_category.id'),
        nullable=False,
        index=True
        )

    category = orm.relation('DrugCategory', uselist=False)

    drug_status_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('drug_status.id'),
        nullable=False,
        index=True
        )

    status = orm.relation('DrugStatus', uselist=False)

    names = orm.relation(
        'DrugName',
        primaryjoin='and_(Drug.id==DrugName.drug_id, DrugName.is_active==True)',
        order_by='desc(DrugName.value)'
        )

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class DrugName(Model):
    """ Child table of drug.
        This will contain known names of the drug.
    """

    __tablename__ = 'drug_name'

    id = sa.Column(sa.Integer, primary_key=True)

    drug_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('drug.id'),
        nullable=False,
        index=True
        )

    drug = orm.relation('Drug', uselist=False)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class DrugCategory(Model):
    """ A lookup table for drug category values.
        These will be assigned to a specific drug.
    """

    __tablename__ = 'drug_category'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class DrugStatus(Model):
    """ A lookup table for drug statuses.
    """

    __tablename__ = 'drug_status'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class Medication(Model):
    """ A period of time in which the subject is taking a drug.
    """

    __tablename__ = 'medication'

    id = sa.Column(sa.Integer, primary_key=True)

    subject_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('subject.id'),
        nullable=False,
        index=True
        )

    subject = orm.relation('Subject', uselist=False)

    visit_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('visit.id'),
        index=True
        )

    visit = orm.relation('Visit', uselist=False)

    drug_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('drug.id'),
        nullable=False,
        index=True
        )

    drug = orm.relation('Drug', uselist=False)

    start_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    dose = sa.Column(sa.Float)

    notes = sa.Column(sa.Unicode)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class SymptomType(Model):
    """
    """

    __tablename__ = 'symptom_type'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class SymptomStatus(Model):
    """
    """

    __tablename__ = 'symptom_status'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class Symptom(Model):
    """
    """

    __tablename__ = 'symptom'

    id = sa.Column(sa.Integer, primary_key=True)

    subject_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('subject.id'),
        nullable=False,
        index=True
        )

    subject = orm.relation('Subject', uselist=False)

    symptom_type_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('symptom_type.id'),
        nullable=False,
        index=True
        )

    type = orm.relation('SymptomType', uselist=False)

    symptom_status_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('symptom_status.id'),
        nullable=False,
        index=True
        )

    status = orm.relation('SymptomStatus', uselist=False)

    start_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    notes = sa.Column(sa.Unicode)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


# Joining table for partner to EAV entries
partner_instance_table = sa.Table('partner_instance', Model.metadata,
    sa.Column('partner_id', sa.Integer, sa.ForeignKey('partner.id'),
              nullable=False, primary_key=True),
    sa.Column('instance_id', sa.Integer, sa.ForeignKey('instance.id'),
              nullable=False, primary_key=True)
    )


class Partner(Model):
    """ An annotation table for the number of partners a subject has.

        Attributes:
            id: (int) database id
            subject_id: (int) the subject id reference of which the entry
                is a partner of
            subject: (obj) the object representation of the subject
            enrolled_subject_id: (int) the id reference of the subject this
                entry represents (if available)
            enrolled_subject_id: (obj) the object representation of the parter
                as a subject
    """

    __tablename__ = 'partner'

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, unique=True, nullable=False)

    subject_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('subject.id'),
        nullable=False,
        index=True
        )

    subject = orm.relation(
        'Subject',
        uselist=False,
        primaryjoin='Partner.subject_id == Subject.id'
        )

    enrolled_subject_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('subject.id'),
        index=True
        )

    enrolled_subject = orm.relation(
        'Subject',
        uselist=False,
        primaryjoin='Partner.enrolled_subject_id == Subject.id'
        )

    visit_date = sa.Column(
        sa.Date,
        nullable=False,
        index=True
        )

    instances = orm.relation('Instance', secondary=partner_instance_table)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)
