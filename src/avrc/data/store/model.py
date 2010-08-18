"""
Data Definition Library

The entities defined within this module are the foundation for the EAV/CR
framework implementation for use in the data store utility. Not that these
table definitions are independent of the interfaces defined by this package.
The reason for this is so that these models can be reused differently
in a separate script/application  if need be. Though, importing this module
can also result in circumventing the entire purpose of the package as well...
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
    """
    This method will setup the database models using the specified engine bind.
    This is simply a convenience method for creating the database tables as
    well as keeping this module self-contained

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
    """
    Used to associate multiple titles for an entity instance. The titles can
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
    __tablename__ = "keyword"

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False)

    instance = orm.relation("Instance", uselist=False)

    title = sa.Column(sa.Unicode, nullable=False, index=True)

    is_synonym = sa.Column(sa.Boolean, nullable=False, default=True)

class Instance(Model):
    """
    A bona fide instance of a schema.

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
    __tablename__ = "instance"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    schema = orm.relation("Schema", uselist=False)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    keywords = orm.relation("Keyword")

    description = sa.Column(sa.Unicode, nullable=False)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

class Binary(Model):
    """
    A binary EAV value.

    TODO: it's a bit unclear how this object will be used, extensions might be
          a little naive (perhaps store MIME types instead?)

    Attributes:
        instnace_id: (int) a reference to the instance
        instance: (Instance) relation to the target instance
        attribute_id: (int) a reference to the attribute this value is for
            (for validation purposes)
        attribute: (Attribute) relation to the target attribute
        extension: (str) the extension of the file being stored
        value: (binary) the physical value being stored
    """
    __tablename__ = "binary"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    extension = sa.Column(sa.Unicode)

    value = sa.Column(sa.BLOB, nullable=False)

class Datetime(Model):
    """
    A datetime EAV value.

    Attributes:
        instnace_id: (int) a reference to the instance
        instance: (Instance) relation to the target instance
        attribute_id: (int) a reference to the attribute this value is for
            (for validation purposes)
        attribute: (Attribute) relation to the target attribute
        value: (datetime) the physical value being stored
    """
    __tablename__ = "datetime"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value = sa.Column(sa.DateTime, nullable=False)

# Optimization for lookup
sa.Index("datetime_attribute_value", Datetime.attribute_id, Datetime.value)

class Integer(Model):
    """
    A integer EAV value.

    Attributes:
        instnace_id: (int) a reference to the instance
        instance: (Instance) relation to the target instance
        attribute_id: (int) a reference to the attribute this value is for
            (for validation purposes)
        attribute: (Attribute) relation to the target attribute
        value: (int) the physical value being stored
    """
    __tablename__ ="integer"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value = sa.Column(sa.Integer, nullable=False)

# Optimization for lookup
sa.Index("integer_attribute_value", Integer.attribute_id, Integer.value)

class Range(Model):
    """
    A range EAV value.

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
    __tablename__ = "range"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value_low = sa.Column(sa.Integer, nullable=False)

    value_high = sa.Column(sa.Integer, nullable=False)

    def _get_value(self):
        return (self.value_low, self.value_high)

    def _set_value(self, value):
        (self.value_low, self.value_high) = value

    value = orm.synonym('_value', descriptor=property(_get_value, _set_value))

# Optimization for lookup
sa.Index("range_attribute_value_low", Range.attribute_id, Range.value_low)
sa.Index("range_attribute_value_high", Range.attribute_id, Range.value_high)
sa.Index("range_attribute_value", Range.value_low, Range.value_high)

class Real(Model):
    """
    A real EAV value.

    Attributes:
        instnace_id: (int) a reference to the instance
        instance: (Instance) relation to the target instance
        attribute_id: (int) a reference to the attribute this value is for
            (for validation purposes)
        attribute: (Attribute) relation to the target attribute
        value: (int) the physical value being stored
    """
    __tablename__ ="real"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value = sa.Column(sa.Float, nullable=False)

# Optimization for lookup
sa.Index("real_attribute_value", Real.attribute_id, Real.value)

class Selection(Model):
    """
    A selection EAV value (into a vocabulary of choices)

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
    __tablename__ ="selection"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value = sa.Column(sa.Integer, sa.ForeignKey("term.id"), nullable=False)

# Optimization for lookup
sa.Index("selection_attribute_value", Real.attribute_id, Real.value)

class Object(Model):
    """
    An object EAV value.

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
    __tablename__ ="object"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance",
                            primaryjoin="Instance.id == Object.instance_id",
                            uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),)

    order = sa.Column(sa.Integer, nullable=False, default=1)

# Optimization for lookup
sa.Index("object_attribute_value", Object.attribute_id, Object.value)

class String(Model):
    """
    A string EAV value.

    Note that this model handles strings up to 1,024 characters

    Attributes:
        instnace_id: (int) a reference to the instance
        instance: (Instance) relation to the target instance
        attribute_id: (int) a reference to the attribute this value is for
            (for validation purposes)
        attribute: (Attribute) relation to the target attribute
        value: (str) the physical value being stored
    """
    __tablename__ ="string"

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)

    instance = orm.relation("Instance", uselist=False)

    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)

    attribute = orm.relation("Attribute", uselist=False)

    value = sa.Column(sa.Unicode, nullable=False)

# Optimization for lookup
sa.Index("string_attribute_value", String.attribute_id, String.value)

# -----------------------------------------------------------------------------
# Metadata specifications
# -----------------------------------------------------------------------------

# Joining table for base class representation
hierarchy_table = sa.Table("hierarchy", Model.metadata,
    sa.Column("parent_id", sa.ForeignKey("specification.id"), nullable=False),
    sa.Column("child_id", sa.ForeignKey("specification.id"), nullable=False),
    sa.PrimaryKeyConstraint("parent_id", "child_id")
    )

class Specification(Model):
    """
    Specification entity for class names. This is an independent model that
    keeps track of the name spaces for the available classes.

    Attributes:
        id: (int) machine generated id number
        bases: (list) list of bases classes this specification extends
        name: (str) the module name of the specification. It must be unique,
            client code should have a graceful way for duplicate names (perhaps
            append an instance number?)
        documentation: (str) documentation for the specification. this attribute
            is required, as it would be extremely useful to know what types of
            classes are being used in the data store.
        title: (str) the human-readable title of the class
        description: (str) the human-readable instructions for the class
        is_association: (bool) is the specification an association class?
        is_virtual: (bool) is the specification an virtual class? (i.e. a class
            without an instance, such as a medline)
        is_eav: (bool) is the specification EAV-only? If false, and entry
            should have a corresponding traditional table. (Currently
            unsupported)
        create_date: (datetime) the date this model instance was created
        modified_date: (datetime) the date this model instance was modified
    """
    __tablename__ = "specification"

    id = sa.Column(sa.Integer, primary_key=True)

    bases = orm.relation("Specification",
                         secondary=hierarchy_table,
                         primaryjoin=(id == hierarchy_table.c.child_id),
                         secondaryjoin=(id == hierarchy_table.c.parent_id),
                         foreign_keys=[hierarchy_table.c.parent_id,
                                       hierarchy_table.c.child_id,
                                       ]
                         )

    module = sa.Column(sa.Unicode, nullable=False, unique=True)

    documentation = sa.Column(sa.Unicode, nullable=False)

    title = sa.Column(sa.Unicode)

    description = sa.Column(sa.Text)

    is_association = sa.Column(sa.Boolean, nullable=False, default=False)

    is_virtual = sa.Column(sa.Boolean, nullable=False, default=False)

    is_eav = sa.Column(sa.Boolean, nullable=False, default=False)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

class Schema(Model):
    """
    The model where versioning takes place. This model uses a specification
    to define a version for it. Once this model is created, attributes and
    invariants can be associated with in order to represent a state of the
    schemata at a point in time.

    Note: the (specification, create_date) tuple is used as the unique
        version value.

    Attribute:
        id: (int) machine generated id number
        specification_id: (int) a reference to the specification this creates
            a versioned schema for.
        specification: (Specification) a relation to the specification model
        attributes: (list) a list of Attributes for this schema
        invariants: (list) a list of Invariants for this schema
        create_date: (datetime) the date this model instance was created
        modified_date: (datetime) the date this model instance was modified
    """
    __tablename__ = "schema"

    id = sa.Column(sa.Integer, primary_key=True)

    specification_id = sa.Column(sa.Integer, sa.ForeignKey("specification.id"),
                                 nullable=False)

    specification = orm.relation("Specification", uselist=False)

    attributes = orm.relation("Attribute", order_by="Attribute.order")

    invariants = orm.relation("Invariant")

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    __table_args = (
        sa.UniqueConstraint("specification_id", "create_date"),
        {})

class Invariant(Model):
    """
    An invariant definition for a class.

    Attributes:
        id: (int) machine generated id number
        schema_id: (int) a reference to the schema this invariant is for
        name: (str) the name of the invariant. Should not contain spaces.
    """
    __tablename__ = "invariant"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    name = sa.Column(sa.Unicode, nullable=False)


class Attribute(Model):
    """
    An attribute declaration.

    This is a special table in that it serves as a joining table between fields
    and schemata, but with extra meta data associated with the join.

    Attributes:
        id: (int) machine generated id number
        schema_id: (int) a reference to the schema this attribute belongs to
        field_id: (int) a reference to the field that contains metadata about
            this attribute.
        field: (Field) a relation to the field
        name: (str) the name of the attribute (i.e. the property name)
        order: (int) the order in which the attribute appears in the schema
        create_date: (datetime) the date this model instance was created
        modified_date: (datetime) the date this model instance was modified

    """
    __tablename__ = "attribute"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    field_id = sa.Column(sa.Integer, sa.ForeignKey("field.id"), nullable=False)

    field = orm.relation("Field", uselist=False)

    name = sa.Column(sa.Unicode, nullable=False)

    order = sa.Column(sa.Integer, nullable=False, default=1)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        sa.UniqueConstraint("schema_id", "name"),
        {})

class Field(Model):
    """
    Attribute display metadata (i.e. Field). Describes how the attribute
    should be used as well as useful constraint/validation meta data. Every
    time an attribute must define a new field (or removed for that matter),
    the source schema should be "versioned".

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
        is_repeatble: (bool) only applicable for associations. see paper...
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

    __tablename__ = "field"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False)

    description = sa.Column(sa.Unicode)

    documentation = sa.Column(sa.Unicode)

    type_id = sa.Column(sa.Integer, sa.ForeignKey("type.id"), nullable=False)

    type = orm.relation("Type", uselist=False)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"))

    schema = orm.relation("Schema", uselist=False)

    vocabulary_id = sa.Column(sa.Integer, sa.ForeignKey("vocabulary.id"))

    vocabulary = orm.relation("Vocabulary")

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
    """
    Represents a supported type.

    TODO: if more database vendors supported ENUM, this model would be
        unnesessary.

    Attributes:
        id: (int) machine generated id number
        title: (str) the human-reable name of this type
        description: (str) an optional description
    """
    __tablename__ = "type"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    description = sa.Column(sa.Text)

# Joining table for vocabulary terms
vocabulary_term_table = sa.Table("vocabulary_term", Model.metadata,
    sa.Column("vocabulary_id", sa.Integer, sa.ForeignKey("vocabulary.id"),
              nullable=False, primary_key=True),
    sa.Column("term_id", sa.Integer, sa.ForeignKey("term.id"),
              nullable=False, primary_key=True),
    )

class Vocabulary(Model):
    """
    A vocabulary.

    Attributes:
        id: (int) machine generated id number
        title: (str) the human-reable name of this vocabulary
        description: (str) an optional description
        terms: (list) the list of terms for this vocabulary
    """
    __tablename__ = "vocabulary"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, index=True)

    description = sa.Column(sa.Unicode)

    terms = orm.relation("Term", secondary=vocabulary_term_table)

class Term(Model):
    """
    An indivudal term for a vocabulary.

    Note: The way this is implemented could possibly override the whole concept
    of EAV itself, but we'll see after some testing...

    Attributes:
        id: (int) machine generated id number
        title: (str) the human-reable name of term
        token: (str) a one-to-one mapping token for the value
        value_*: the currently implemented way for the term value that seriously
            needs some reworking.
        value: (object) the value for this term
        description: (str) an optional description
        terms: (list) the list of terms for this vocabulary
    """
    __tablename__ = "term"

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

        if value is None:
            raise Exception("TERM ITEM NOT FOUND")

        return value

    def _set_value(self, value):
        """Sets the value to the paramter's value"""
        if isinstance(value, int):
            self.value_int = value
        elif isinstance(value, float):
            self.value_real = value
        elif isinstance(value, (str, unicode)):
            self.value_str = unicode(value)
        else:
            raise Exception("Unable to determine type: %s"  % value)

    value = property(_get_value, _set_value, None, "The value stored")

# -----------------------------------------------------------------------------
# Visit
# TODO: the following models are probably going to be obsolete when this
#       package is completed. The reason they were developed in the first
#       place is to help connect keep track of AVRC-specific components
#       with the EAV\CR model, but then these can just as easily be done
#       as associations.
# -----------------------------------------------------------------------------

class Curator(Model):
    """
    """
    __tablename__ = "curator"

    id = sa.Column(sa.Integer, primary_key=True)

class Subject(Model):
    """
    """
    __tablename__ = "subject"

    id = sa.Column(sa.Integer, primary_key=True)

    uid = sa.Column(sa.Integer, nullable=False, unique=True)

class Domain(Model):
    """
    """
    __tablename__ = "domain"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)


class Protocol(Model):
    """
    TODO: incomplete
    """
    __tablename__ = "protocol"

    id = sa.Column(sa.Integer, primary_key=True)

    domain_id = sa.Column(sa.Integer, sa.ForeignKey("domain.id"),
                          nullable=False)

class Enrollment(Model):
    """
    """
    __tablename__ = "enrollment"

    id = sa.Column(sa.Integer, primary_key=True)

    protocol_id = sa.Column(sa.Integer, sa.ForeignKey("protocol.id"),
                            nullable=False)

    protocol = orm.relation("Protocol", uselist=False)

    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subject.id"),
                           nullable=False)

    subject = orm.relation("Subject", uselist=False)

    start_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        sa.UniqueConstraint("protocol_id", "subject_id", "start_date"),
        {})

class Visit(Model):
    """
    """
    __tablename__ = "visit"

    id = sa.Column(sa.Integer, primary_key=True)

    enrollement_id = sa.Column(sa.Integer, sa.ForeignKey(Enrollment.id),
                               nullable=False)

    enrollement = orm.relation("Enrollment", uselist=False)

    visit_date = sa.Column(sa.Date, nullable=False)

visit_instance_table = sa.Table("visit_instance", Model.metadata,
    sa.Column("visit_id", sa.ForeignKey("visit.id"), nullable=False),
    sa.Column("instance_id", sa.ForeignKey("instance.id"), nullable=False),
    sa.PrimaryKeyConstraint("visit_id", "instance_id")
    )

domain_schema_table = sa.Table("domain_schema", Model.metadata,
    sa.Column("domain_id", sa.Integer, sa.ForeignKey("domain.id"),
              nullable=False),
    sa.Column("schema_id", sa.Integer, sa.ForeignKey("schema.id"),
              nullable=False),
    sa.PrimaryKeyConstraint("domain_id", "schema_id")
    )
