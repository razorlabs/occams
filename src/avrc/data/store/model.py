"""
Data Definition Library

Note that the entities defined in this module are mapped to a database.
Therefore, great care should be taken when updating this file, as it may
cause live systems to fall out of sync.
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

Entity = declarative_base()

def setup(engine):
    """
    """
    Entity.metadata.create_all(bind=engine, checkfirst=True)

# -----------------------------------------------------------------------------
# Visit
# -----------------------------------------------------------------------------

class Curator(Entity):
    """
    """
    __tablename__ = "curator"

    id = sa.Column(sa.Integer, primary_key=True)

class Subject(Entity):
    """
    """
    __tablename__ = "subject"

    id = sa.Column(sa.Integer, primary_key=True)

    uid = sa.Column(sa.Integer, nullable=False, unique=True)

class Domain(Entity):
    """
    """
    __tablename__ = "domain"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)


class Protocol(Entity):
    """
    TODO: incomplete
    """
    __tablename__ = "protocol"

    id = sa.Column(sa.Integer, primary_key=True)

    domain_id = sa.Column(sa.Integer, sa.ForeignKey("domain.id"),
                          nullable=False)

class Enrollment(Entity):
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

class Visit(Entity):
    """
    """
    __tablename__ = "visit"

    id = sa.Column(sa.Integer, primary_key=True)

    enrollement_id = sa.Column(sa.Integer, sa.ForeignKey(Enrollment.id),
                               nullable=False)

    enrollement = orm.relation("Enrollment", uselist=False)

    visit_date = sa.Column(sa.Date, nullable=False)

visit_instance_table = sa.Table("visit_instance", Entity.metadata,
    sa.Column("visit_id", sa.ForeignKey("visit.id"), nullable=False),
    sa.Column("instance_id", sa.ForeignKey("instance.id"), nullable=False),
    sa.PrimaryKeyConstraint("visit_id", "instance_id")
    )

domain_schema_table = sa.Table("domain_schema", Entity.metadata,
    sa.Column("domain_id", sa.Integer, sa.ForeignKey("domain.id"),
              nullable=False),
    sa.Column("schema_id", sa.Integer, sa.ForeignKey("schema.id"),
              nullable=False),
    sa.PrimaryKeyConstraint("domain_id", "schema_id")
    )

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

class Keyword(Entity):
    """
    """
    __tablename__ = "keyword"

    id = sa.Column(sa.Integer, primary_key=True)

    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False)

    instance = orm.relation("Instance", uselist=False)

    title = sa.Column(sa.Unicode, nullable=False, index=True)

    is_synonym = sa.Column(sa.Boolean, nullable=False, default=True)

    __table_args__ = (
        sa.UniqueConstraint("instance_id", "title"),
        {})

class Instance(Entity):
    """
    TODO, the title doesn't really make much sense in our situation, making
    it optional for now...
    """
    __tablename__ = "instance"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    schema = orm.relation("Schema", uselist=False)

    title = sa.Column(sa.Unicode, unique=True)

    description = sa.Column(sa.Unicode)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

class Binary(Entity):
    """
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

class Datetime(Entity):
    """
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

sa.Index("datetime_attribute_value", Datetime.attribute_id, Datetime.value)


class Integer(Entity):
    """
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

sa.Index("integer_attribute_value", Integer.attribute_id, Integer.value)

class Range(Entity):
    """
    Built-in type to represent min/max values (only integers)
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

    value_min = sa.Column(sa.Integer, nullable=False)

    value_max = sa.Column(sa.Integer, nullable=False)

    def _get_value(self):
        return self._some_attr
    def _set_value(self, value):
        (self.value_min, self.value_max) = value

    value = orm.synonym('_value', descriptor=property(_get_value, _set_value))

sa.Index("range_attribute_value_min", Range.attribute_id, Range.value_min)
sa.Index("range_attribute_value_max", Range.attribute_id, Range.value_max)
sa.Index("range_attribute_value", Range.value_min, Range.value_max)

class Real(Entity):
    """
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

sa.Index("real_attribute_value", Real.attribute_id, Real.value)

class Selection(Entity):
    """
    This type is simply a reference into a vocabulary list
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

sa.Index("selection_attribute_value", Real.attribute_id, Real.value)

class Object(Entity):
    """
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

sa.Index("object_attribute_value", Object.attribute_id, Object.value)

class String(Entity):
    """
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

sa.Index("string_attribute_value", String.attribute_id, String.value)

# -----------------------------------------------------------------------------
# Metadata
# -----------------------------------------------------------------------------

# Joining table for base class representation
hierarchy_table = sa.Table("hierarchy", Entity.metadata,
    sa.Column("parent_id", sa.ForeignKey("specification.id"), nullable=False),
    sa.Column("child_id", sa.ForeignKey("specification.id"), nullable=False),
    sa.PrimaryKeyConstraint("parent_id", "child_id")
    )

class Specification(Entity):
    """
    Specification entity for class names
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

    # The unique module name for this spec.
    #
    # TODO: graceful recovery for duplicate name schemata?
    #
    module = sa.Column(sa.Unicode, nullable=False, unique=True)

    # Enforce  documentation so we know what the heck people are making...
    documentation = sa.Column(sa.Unicode, nullable=False)

    # Human readable title
    title = sa.Column(sa.Unicode)

    # Human readable description
    description = sa.Column(sa.Text)

    # Association flag for specifications that act as a line in a network
    is_association = sa.Column(sa.Boolean, nullable=False, default=False)

    # A class without instances. For external references (e.g. medline)
    is_virtual = sa.Column(sa.Boolean, nullable=False, default=False)

    # If this entity is not in eav, it should define a corresponding table
    is_eav = sa.Column(sa.Boolean, nullable=False, default=False)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

class Invariant(Entity):
    """
    """
    __tablename__ = "invariant"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    name = sa.Column(sa.Unicode, nullable=False)

class Schema(Entity):
    """
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

class Attribute(Entity):
    """
    This is a special table in that it serves as a joining table between fields
    and schemata, but with extra meta data associated with the join.
    """
    __tablename__ = "attribute"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    field_id = sa.Column(sa.Integer, sa.ForeignKey("field.id"), nullable=False)

    field = orm.relation("Field", uselist=False)

    # Property name of the class
    name = sa.Column(sa.Unicode, nullable=False)

    order = sa.Column(sa.Integer, nullable=False, default=1)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        sa.UniqueConstraint("schema_id", "name"),
        {}
        )

class Field(Entity):
    """
    A field details entries. Note that this module is not tied to anything
    as it can be reused by an attribute, etc. Note that if the attribute using
    this must properly "version" the change though...
    """

    __tablename__ = "field"

    id = sa.Column(sa.Integer, primary_key=True)

    # Human readable title
    title = sa.Column(sa.Unicode, nullable=False)

    # Human readable description
    description = sa.Column(sa.Text)

    # Internal notes about this field
    documentation = sa.Column(sa.Text)

    # The field's type
    type_id = sa.Column(sa.Integer, sa.ForeignKey("type.id"), nullable=False)

    type = orm.relation("Type", uselist=False)

    # Can be used to enforce a class type as a valid value
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"))

    schema = orm.relation("Schema", uselist=False)

    vocabulary_id = sa.Column(sa.Integer, sa.ForeignKey("vocabulary.id"))

    vocabulary = orm.relation("Vocabulary")

    # Should be added to the application's search form? Only if this applies...
    is_searchable = sa.Column(sa.Boolean, nullable=False, default=False)

    is_required = sa.Column(sa.Boolean, nullable=False, default=False)

    is_inline_image = sa.Column(sa.Boolean)

    is_repeatable = sa.Column(sa.Boolean, nullable=False, default=False)

    # Min/max depending on the type
    minimum = sa.Column(sa.Integer)

    maximum = sa.Column(sa.Integer)

    # These values are intended as parameters for the corresponding widget
    width = sa.Column(sa.Integer)

    height = sa.Column(sa.Integer)

    # URL template for values (this applies mostly to virtual classes)
    url = sa.Column(sa.Unicode)

    # OMFG these need to go away
    directive_widget = sa.Column(sa.Unicode)

    directive_omitted = sa.Column(sa.Boolean)

    directive_no_ommit = sa.Column(sa.Unicode)

    directive_mode = sa.Column(sa.Unicode)

    directive_before = sa.Column(sa.Unicode)

    directive_after = sa.Column(sa.Unicode)

    directive_read = sa.Column(sa.Unicode)

    directive_write = sa.Column(sa.Unicode)
    # /END GO AWAY

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

class Type(Entity):
    """
    """
    __tablename__ = "type"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    description = sa.Column(sa.Text)

vocabulary_term_table = sa.Table("vocabulary_term", Entity.metadata,
    sa.Column("vocabulary_id", sa.Integer, sa.ForeignKey("vocabulary.id"),
              nullable=False, primary_key=True),
    sa.Column("term_id", sa.Integer, sa.ForeignKey("term.id"),
              nullable=False, primary_key=True),
    )

class Vocabulary(Entity):
    """
    """
    __tablename__ = "vocabulary"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, index=True)

    terms = orm.relation("Term", secondary=vocabulary_term_table)

def get(value, default=None):
    return value is not None and value or default

class Term(Entity):
    """
    The way this is implemented could possibly override the whole cocept of
    EAV itself, but we'll see after some testing...
    """
    __tablename__ = "term"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode)

    token = sa.Column(sa.Unicode, nullable=False, index=True)

    # OMG this again...
    value_str = sa.Column(sa.Unicode)

    value_int = sa.Column(sa.Integer)

    value_real = sa.Column(sa.Float)

#    value_object = sa.Column(sa.Integer)

    value_range_low = sa.Column(sa.Integer)

    value_range_high = sa.Column(sa.Integer)

    order = sa.Column(sa.Integer, nullable=False, default=1)

    @property
    def value(self):
        value = get(self.value_int) or \
                get(self.value_real) or \
                get(self.value_str)

        if value is None:
            raise Exception("TERM ITEM NOT FOUND")

        return value

    @value.setter
    def value(self, value):
        if isinstance(value, int):
            self.value_int = value
        elif isinstance(value, float):
            self.value_real = value
        elif isinstance(value, (str, unicode)):
            self.value_str = unicode(value)
        else:
            raise Exception("Unable to determine type: %s"  % value)