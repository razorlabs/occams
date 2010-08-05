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

FIA = declarative_base()
PII = declarative_base()

def _setup_base(base, engine):
    """
    """
    base.metadata.create_all(bind=engine, checkfirst=True)

def setup(fia_engine, pii_engine=None):
    _setup_base(FIA, fia_engine)
    _setup_base(PII, pii_engine and pii_engine or fia_engine)

# -----------------------------------------------------------------------------
# Personal Information
# -----------------------------------------------------------------------------

class Name(PII):
    """
    """
    __tablename__ = "name"

    id = sa.Column(sa.Integer, primary_key=True)

    first = sa.Column(sa.Unicode, nullable=False, index=True)

    middle = sa.Column(sa.Unicode)

    last = sa.Column(sa.Unicode, nullable=False, index=True)

    sur = sa.Column(sa.Unicode)

class Address(PII):
    """
    """
    __tablename__ = "address"

    id = sa.Column(sa.Integer, primary_key=True)

    phone = sa.Column(sa.Unicode, index=True)

    line_1 = sa.Column(sa.Unicode)

    line_2 = sa.Column(sa.Unicode)

    city = sa.Column(sa.Unicode)

    state_id = sa.Column(sa.Integer, sa.ForeignKey("state.id"))

    zip = sa.Column(sa.Integer)

class State(PII):
    """
    """
    __tablename__ = "state"

    id = sa.Column(sa.Integer, primary_key=True)

    country_id = sa.Column(sa.Integer, sa.ForeignKey("country.id"),
                           nullable=False)

    abbreviation = sa.Column(sa.Unicode, nullable=False)

    name = sa.Column(sa.Unicode, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("country_id", "name"),
        {})

class Country(PII):
    """
    """
    __tablename__ = "country"

    id = sa.Column(sa.Integer, primary_key=True)

    abbreviation = sa.Column(sa.Unicode, nullable=False, unique=True)

    name = sa.Column(sa.Unicode, nullable=False, unique=True)

class Phone(PII):
    """
    """
    __tablename__ = "phone"

    id = sa.Column(sa.Integer, primary_key=True)

    location_id = sa.Column(sa.Integer, sa.ForeignKey("location.id"),
                            nullable=False)

    location = orm.relation("Location", uselist=False)

    value = sa.Column(sa.Unicode, nullable=False)

class Email(PII):
    """
    """
    __tablename__ = "email"

    id = sa.Column(sa.Integer, primary_key=True)

    location_id = sa.Column(sa.Integer, sa.ForeignKey("location.id"),
                            nullable=False)

    location = orm.relation("Location", uselist=False)

    value = sa.Column(sa.Unicode, nullable=False)

class Location(PII):
    """
    """
    __tablename__ = "location"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False)

class Demographic(PII):
    """
    """
    __tablename__ = "demographic"

    id = sa.Column(sa.Integer, primary_key=True)

    birth_date = sa.Column(sa.DateTime)

class Physique(PII):
    """
    """
    __tablename__ = "physique"

    id = sa.Column(sa.Integer, primary_key=True)

# -----------------------------------------------------------------------------
# Visit
# -----------------------------------------------------------------------------

class Curator(FIA):
    """
    """
    __tablename__ = "curator"

    id = sa.Column(sa.Integer, primary_key=True)

class Subject(FIA):
    """
    """
    __tablename__ = "subject"

    id = sa.Column(sa.Integer, primary_key=True)

    uid = sa.Column(sa.Integer, nullable=False, unique=True)

class Domain(FIA):
    """
    """
    __tablename__ = "domain"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)


class Protocol(FIA):
    """
    TODO: incomplete
    """
    __tablename__ = "protocol"

    id = sa.Column(sa.Integer, primary_key=True)

    domain_id = sa.Column(sa.Integer, sa.ForeignKey("domain.id"),
                          nullable=False)

class Enrollment(FIA):
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

class Visit(FIA):
    """
    """
    __tablename__ = "visit"

    id = sa.Column(sa.Integer, primary_key=True)

    enrollement_id = sa.Column(sa.Integer, sa.ForeignKey(Enrollment.id),
                               nullable=False)

    enrollement = orm.relation("Enrollment", uselist=False)

    visit_date = sa.Column(sa.Date, nullable=False)

visit_instance_table = sa.Table("visit_instance", FIA.metadata,
    sa.Column("visit_id", sa.ForeignKey("visit.id"), nullable=False),
    sa.Column("instance_id", sa.ForeignKey("instance.id"), nullable=False),
    sa.PrimaryKeyConstraint("visit_id", "instance_id")
    )

domain_schema_table = sa.Table("domain_schema", FIA.metadata,
    sa.Column("domain_id", sa.Integer, sa.ForeignKey("domain.id"),
              nullable=False),
    sa.Column("schema_id", sa.Integer, sa.ForeignKey("schema.id"),
              nullable=False),
    sa.PrimaryKeyConstraint("domain_id", "schema_id")
    )

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

class Keyword(FIA):
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

class Instance(FIA):
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

class Binary(FIA):
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

class Datetime(FIA):
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


class Integer(FIA):
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

class Real(FIA):
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

    value = sa.Column(sa.Integer, nullable=False)

sa.Index("real_attribute_value", Real.attribute_id, Real.value)

class Object(FIA):
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

class String(FIA):
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
hierarchy_table = sa.Table("hierarchy", FIA.metadata,
    sa.Column("parent_id", sa.ForeignKey("specification.id"), nullable=False),
    sa.Column("child_id", sa.ForeignKey("specification.id"), nullable=False),
    sa.PrimaryKeyConstraint("parent_id", "child_id")
    )

class Specification(FIA):
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

    # The unique module name for this spec. Doesn't necessarily have to
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

class Invariant(FIA):
    """
    """
    __tablename__ = "invariant"

    id = sa.Column(sa.Integer, primary_key=True)

    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)

    name = sa.Column(sa.Unicode, nullable=False)

class Schema(FIA):
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

class Attribute(FIA):
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

class Field(FIA):
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

    directive = orm.relation("Directive", uselist=False)

    # Can be used to enforce a class type as a valid value
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"))

    schema = orm.relation("Schema", uselist=False)

#    vocabulary_id = sa.Column(sa.Integer, sa.ForeignKey("vocabulary.id"))
#
#    vocabulary = orm.relation("Vocabulary")

    # Should be added to the application's search form? Only if this applies...
    is_searchable = sa.Column(sa.Boolean, nullable=False, default=False)

    is_required = sa.Column(sa.Boolean, nullable=False, default=False)

    is_inline_image = sa.Column(sa.Boolean)

    is_repeatable = sa.Column(sa.Boolean)

    # Min/max depending on the type
    minimum = sa.Column(sa.Integer)

    maximum = sa.Column(sa.Integer)

    # These values are intended as parameters for the corresponding widget
    width = sa.Column(sa.Integer)

    height = sa.Column(sa.Integer)

    # URL template for values (this applies mostly to virtual classes)
    url = sa.Column(sa.Unicode)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

class Directive(FIA):
    """
    For plone.directives.form compatibility
    """
    __tablename__ = "directive"

    id = sa.Column(sa.Integer, primary_key=True)

    field_id = sa.Column(sa.Integer, sa.ForeignKey("field.id"),
                         nullable=False)

    widget = sa.Column(sa.Unicode)

    omitted = sa.Column(sa.Boolean)

    no_ommit = sa.Column(sa.Unicode)

    mode = sa.Column(sa.Unicode)

    order_before = sa.Column(sa.Unicode)

    order_after = sa.Column(sa.Unicode)

    read_permission = sa.Column(sa.Unicode)

    write_persmission = sa.Column(sa.Unicode)

class Type(FIA):
    """
    """
    __tablename__ = "type"

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(sa.Unicode, nullable=False, unique=True)

    description = sa.Column(sa.Text)
