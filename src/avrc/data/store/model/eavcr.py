""" Entity-Attribute-Value with Class-Relationships Models

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

    Currently a combincation of both form and object definitions, which will
    be refactored later.

"""

from datetime import datetime

from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import Table
from sqlalchemy.schema import Index
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy import text

from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime as SADateTime
from sqlalchemy.types import Float
from sqlalchemy.types import Integer as SAInteger
from sqlalchemy.types import String as SAString
from sqlalchemy.types import Unicode
from sqlalchemy.types import UnicodeText
from sqlalchemy.types import Text

from sqlalchemy.orm import relation as Relationship

from avrc.data.store.model import Model

PY_NOW = datetime.now
SQL_NOW = text('CURRENT_TIMESTAMP')

__all__ = (
    'fieldset_fieldsetitem_table',
    'hierarchy_table',
    'include_table',
    'schema_fieldset_table',
    'Type',
    'Specification',
    'Schema',
    'Invariant',
    'Field',
    'Choice',
    'Attribute',
    'FieldsetItem',
    'Fieldset',
    'State',
    'Instance',
    'Keyword',
    'Datetime',
    'Integer',
    'Real',
    'Object',
    'String',
    )


fieldset_fieldsetitem_table = Table('fieldset_fieldsetitem', Model.metadata,
    Column('fieldset_id', ForeignKey('fieldset.id', ondelete='CASCADE')),
    Column('item_id', ForeignKey('fieldsetitem.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('fieldset_id', 'item_id')
    )

# Joining table for base class representation
hierarchy_table = Table('hierarchy', Model.metadata,
    Column('parent_id', ForeignKey('specification.id', ondelete='CASCADE')),
    Column('child_id', ForeignKey('specification.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('parent_id', 'child_id')
    )

# A hackish way to include additional schemata when a 'main' schemata is
# requested.
include_table = Table('include', Model.metadata,
    Column('main_id', ForeignKey('specification.id', ondelete='CASCADE')),
    Column('include_id', ForeignKey('specification.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('main_id', 'include_id')
    )

schema_fieldset_table = Table('schema_fieldset', Model.metadata,
    Column('schema_id', ForeignKey('schema.id', ondelete='CASCADE')),
    Column('fieldset_id', ForeignKey('fieldset.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('schema_id', 'fieldset_id')
    )


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

    id = Column(SAInteger, primary_key=True)

    title = Column(Unicode, nullable=False, unique=True)

    description = Column(Text)


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

    id = Column(SAInteger, primary_key=True)

    bases = Relationship(
        'Specification',
        secondary=hierarchy_table,
        primaryjoin=(id == hierarchy_table.c.child_id),
        secondaryjoin=(id == hierarchy_table.c.parent_id),
        foreign_keys=[hierarchy_table.c.parent_id, hierarchy_table.c.child_id, ]
        )

    children = Relationship(
        'Specification',
        secondary=hierarchy_table,
        primaryjoin=(id == hierarchy_table.c.parent_id),
        secondaryjoin=(id == hierarchy_table.c.child_id),
        foreign_keys=[hierarchy_table.c.child_id, hierarchy_table.c.parent_id, ]
        )

    includes = Relationship(
        'Specification',
        secondary=include_table,
        primaryjoin=(id == include_table.c.main_id),
        secondaryjoin=(id == include_table.c.include_id),
        foreign_keys=[include_table.c.main_id, include_table.c.include_id, ]
        )

    name = Column(Unicode, nullable=False, unique=True)

    documentation = Column(Unicode, nullable=False)

    title = Column(Unicode)

    description = Column(Text)

    is_tabable = Column(Boolean, nullable=False, default=False)

    is_association = Column(Boolean, nullable=False, default=False)

    is_virtual = Column(Boolean, nullable=False, default=False)

    is_eav = Column(Boolean, nullable=False, default=False)

    create_date = Column(SADateTime, nullable=False, default=PY_NOW)

    modify_date = Column(SADateTime, nullable=False, default=PY_NOW, onupdate=PY_NOW)


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

    id = Column(SAInteger, primary_key=True)

    specification_id = Column(
        ForeignKey(Specification.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    specification = Relationship('Specification')

    attributes = Relationship('Attribute', order_by='Attribute.order')

    invariants = Relationship('Invariant')

    fieldsets = Relationship(
        'Fieldset',
        secondary=schema_fieldset_table,
        order_by='Fieldset.order'
        )

    create_date = Column(SADateTime, nullable=False, default=PY_NOW)

    __table_args = (
        UniqueConstraint('specification_id', 'create_date'),
        {})


class Invariant(Model):
    """ An invariant definition for a class.

        Attributes:
            id: (int) machine generated id number
            schema_id: (int) a reference to the schema this invariant is for
            name: (str) the name of the invariant. Should not contain spaces.
    """
    __tablename__ = 'invariant'

    id = Column(SAInteger, primary_key=True)

    schema_id = Column(
        ForeignKey(Schema.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    name = Column(Unicode, nullable=False)


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

    id = Column(SAInteger, primary_key=True)

    # TODO: (mmartinez) uselist!?!
    attribute = Relationship('Attribute', uselist=False)

    title = Column(Unicode, nullable=False)

    description = Column(Unicode)

    documentation = Column(Unicode)

    type_id = Column(
        ForeignKey(Type.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    type = Relationship('Type')

    schema_id = Column(ForeignKey(Schema.id, ondelete='SET NULL'), index=True)

    schema = Relationship('Schema')

    choices = Relationship('Choice')

    default = Column(Unicode)

    is_list = Column(Boolean, nullable=False, default=False)

    is_readonly = Column(Boolean, nullable=False, default=False)

    is_searchable = Column(Boolean, nullable=False, default=False)

    is_required = Column(Boolean, nullable=False, default=False)

    is_inline_image = Column(Boolean)

    is_repeatable = Column(Boolean, nullable=False, default=False)

    minimum = Column(SAInteger)

    maximum = Column(SAInteger)

    width = Column(SAInteger)

    height = Column(SAInteger)

    url = Column(Unicode)

    directive_widget = Column(Unicode)

    directive_omitted = Column(Boolean)

    directive_no_ommit = Column(Unicode)

    directive_mode = Column(Unicode)

    directive_before = Column(Unicode)

    directive_after = Column(Unicode)

    directive_read = Column(Unicode)

    directive_write = Column(Unicode)

    create_date = Column(SADateTime, nullable=False, default=PY_NOW)

    modify_date = Column(SADateTime, nullable=False, default=PY_NOW, onupdate=PY_NOW)


class Choice(Model):
    """ Field choice constraint table.
        Specification: DS-1

        Contains a list of choice terms that a particular field/attribute
        is allowed to be set to.

        TODO: (mmartinez) rename to attribute_id when field is renamed.
    """

    __tablename__ = 'choice'

    id = Column('id', SAInteger, primary_key=True)

    field_id = Column(
        ForeignKey(Field.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    field = Relationship('Field')

    name = Column(SAString, nullable=False, index=True)

    title = Column(Unicode, nullable=False)

    description = Column(UnicodeText)

    value = Column(Unicode, nullable=False, index=True)

    order = Column(SAInteger, nullable=False, index=True)

    create_date = Column(SADateTime, nullable=False, server_default=SQL_NOW)

    create_user_id = Column(SAInteger)

    modify_date = Column(SADateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW)

    modify_user_id = Column(SAInteger)

    remove_date = Column(SADateTime, index=True)

    remove_user_id = Column(SAInteger)


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

    id = Column(SAInteger, primary_key=True)

    schema_id = Column(
        ForeignKey(Schema.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    schema = Relationship('Schema')

    field_id = Column(
        ForeignKey(Field.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    field = Relationship('Field')

    name = Column(Unicode, nullable=False)

    order = Column(SAInteger, nullable=False, default=1)

    create_date = Column(SADateTime, nullable=False, default=PY_NOW)

    __table_args__ = (
        UniqueConstraint('schema_id', 'name'),
        {})


class FieldsetItem(Model):
    """
    """
    __tablename__ = 'fieldsetitem'

    id = Column(SAInteger, primary_key=True)

    name = Column(Unicode, nullable=False)

    order = Column(SAInteger, nullable=False, default=1)


class Fieldset(Model):
    """
    """
    __tablename__ = 'fieldset'

    id = Column(SAInteger, primary_key=True)

    name = Column(Unicode, nullable=False)

    label = Column(Unicode, nullable=False)

    description = Column(Unicode)

    order = Column(SAInteger, nullable=False, default=1)

    fields = Relationship(
        'FieldsetItem',
        secondary=fieldset_fieldsetitem_table,
        order_by='FieldsetItem.order'
        )


class State(Model):
    """
    """

    __tablename__ = 'state'

    id = Column(SAInteger, primary_key=True)

    name = Column(Unicode, nullable=False, unique=True)

    title = Column(Unicode, nullable=False)

    description = Column(Unicode)

    is_default = Column(Boolean, nullable=False, default=False, index=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(SADateTime, nullable=False, default=PY_NOW)

    modify_date = Column(
        SADateTime,
        nullable=False,
        default=PY_NOW,
        onupdate=PY_NOW
        )


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

    id = Column(SAInteger, primary_key=True)

    schema_id = Column(
        ForeignKey(Schema.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    schema = Relationship('Schema')

    title = Column(Unicode, nullable=False, unique=True)

    keywords = Relationship('Keyword')

    description = Column(Unicode, nullable=False)

    state_id = Column(
        ForeignKey(State.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state = Relationship('State')

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(SADateTime, nullable=False, default=PY_NOW)

    modify_date = Column(
        SADateTime,
        nullable=False,
        default=PY_NOW,
        onupdate=PY_NOW
        )


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

    id = Column(SAInteger, primary_key=True)

    instance_id = Column(
        ForeignKey(Instance.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    instance = Relationship('Instance')

    title = Column(Unicode, nullable=False, index=True)

    is_synonym = Column(Boolean, nullable=False, default=True)


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

    id = Column(SAInteger, primary_key=True)

    instance_id = Column(
        ForeignKey(Instance.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    instance = Relationship('Instance')

    attribute_id = Column(
        ForeignKey(Attribute.id, ondelete='CASCADE'),
        nullable=False
        )

    attribute = Relationship('Attribute')

    value = Column(SADateTime, nullable=False)


# Optimization for lookup
Index('datetime_attribute_value', Datetime.attribute_id, Datetime.value)


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
    __tablename__ = 'integer'

    id = Column(SAInteger, primary_key=True)

    instance_id = Column(
        ForeignKey(Instance.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    instance = Relationship('Instance')

    attribute_id = Column(
        ForeignKey(Attribute.id, ondelete='CASCADE'),
        nullable=False
        )

    attribute = Relationship('Attribute')

    choice_id = Column(ForeignKey(Choice.id, ondelete='CASCADE'), index=True)

    choice = Relationship('Choice')

    value = Column(SAInteger, nullable=False)


# Optimization for lookup
Index('integer_attribute_value', Integer.attribute_id, Integer.value)


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
    __tablename__ = 'real'

    id = Column(SAInteger, primary_key=True)

    instance_id = Column(
        ForeignKey(Instance.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    instance = Relationship('Instance')

    attribute_id = Column(
        ForeignKey(Attribute.id, ondelete='CASCADE'),
        nullable=False
        )

    attribute = Relationship('Attribute')

    choice_id = Column(ForeignKey(Choice.id, ondelete='CASCADE'), index=True)

    choice = Relationship('Choice')

    value = Column(Float, nullable=False)


# Optimization for lookup
Index('real_attribute_value', Real.attribute_id, Real.value)


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
    __tablename__ = 'object'

    id = Column(SAInteger, primary_key=True)


    instance_id = Column(
        ForeignKey(Instance.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    instance = Relationship(
        'Instance',
        primaryjoin='Instance.id == Object.instance_id',
        uselist=False
        )

    attribute_id = Column(
        ForeignKey(Attribute.id, ondelete='CASCADE'),
        nullable=False
        )

    attribute = Relationship('Attribute')

    choice_id = Column(ForeignKey(Choice.id, ondelete='CASCADE'), index=True)

    choice = Relationship('Choice')

    # TODO: (mmartinez) make nullable=False
    value = Column(ForeignKey(Instance.id, ondelete='CASCADE'),)

    order = Column(SAInteger, nullable=False, default=1)


# Optimization for lookup
Index('object_attribute_value', Object.attribute_id, Object.value)


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
    __tablename__ = 'string'

    id = Column(SAInteger, primary_key=True)

    instance_id = Column(
        ForeignKey(Instance.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    instance = Relationship('Instance')

    attribute_id = Column(
        ForeignKey(Attribute.id, ondelete='CASCADE'),
        nullable=False
        )

    attribute = Relationship('Attribute')

    choice_id = Column(ForeignKey(Choice.id, ondelete='CASCADE'), index=True)

    choice = Relationship('Choice')

    value = Column(Unicode, nullable=False)


# Optimization for lookup
Index('string_attribute_value', String.attribute_id, String.value)
