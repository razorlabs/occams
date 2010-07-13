"""
Data Definifinion Library, in this case, SQLAlcchemy
Data store for objects. 
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Accessible = declarative_base()
Internal = declarative_base()

# -----------------------------------------------------------------------------
# Personal Information
# -----------------------------------------------------------------------------

class Name(Internal):
    """
    """
    __tablename__ = "name"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    first = sa.Column(sa.Unicode, nullable=False, index=True)
    
    middle = sa.Column(sa.Unicode)
    
    last = sa.Column(sa.Unicode, nullable=False, index=True)
    
    sur = sa.Column(sa.Unicode)
    
class State(Internal):
    """
    """
    __tablename__ = "state"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    abbreviation = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    name = sa.Column(sa.Unicode, nullable=False)
    
    
class Contact(Internal):
    """
    """
    __tablename__ = "contact"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    phone = sa.Column(sa.Unicode, index=True)
    
    address1 = sa.Column(sa.Unicode)
    
    address2 = sa.Column(sa.Unicode)
    
    city = sa.Column(sa.Unicode)

    state_id = sa.Column(sa.Integer, sa.ForeignKey("state.id"))
    
    zip = sa.Column(sa.Integer)
    
    
class Demographic(Internal):
    """
    """
    __tablename__ = "demographic"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    birthdate = sa.Column(sa.DateTime)


# -----------------------------------------------------------------------------
# Visit
# -----------------------------------------------------------------------------

class Subject(Accessible):
    """
    """
    __tablename__ = "subject"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    
class Protocol(Accessible):
    """
    """
    __tablename__ = "protocol"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    short = sa.Column(sa.Unicode, index=True)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    description = sa.Column(sa.Text)
    
    
class Enrollment(Accessible): 
    """
    """
    __tablename__ = "enrollment"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    protocol_id = sa.Column(sa.Integer, sa.ForeignKey("protocol.id"), 
                            nullable=False)
    
    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subject.id"), 
                           nullable=False)
    
    
    serial = sa.Column(sa.Unicode, index=True )


visit_instance_table = sa.Table("visit_instance", Accessible.metadata,
    sa.Column("visit_id", sa.ForeignKey("visit.id"), nullable=False),
    sa.Column("instance_id", sa.ForeignKey("instance.id"), nullable=False),
    sa.PrimaryKeyConstraint("visit_id", "instance_id")
    )


class Visit(Accessible):
    """
    """
    __tablename__ = "visit"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    enrollement_id = sa.Column(sa.Integer, sa.ForeignKey(Enrollment.id),
                               nullable=False)
    
    
    eventdate = sa.Column(sa.Date, nullable=False)

        
# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

class Instance(Accessible):
    """
    """
    __tablename__ = "instance"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"), 
                          nullable=False)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    description = sa.Column(sa.Text)
    
    createdate = sa.Column(sa.DateTime, nullable=False)
    
    modifydate = sa.Column(sa.DateTime, nullable=False)
    

class Binary(Accessible):
    """
    """
    
    __tablename__ = "binary"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    extension = sa.Column(sa.Unicode)
    
    value = sa.Column(sa.BLOB, nullable=False)


class Datetime(Accessible):
    """
    """
    __tablename__ = "datetime"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.DateTime, nullable=False)
    
    
sa.Index("datetime_attribute_value", Datetime.attribute_id, Datetime.value)
    
    
class Integer(Accessible):
    """
    """
    __tablename__ ="integer"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.Integer, nullable=False)
    
    
sa.Index("integer_attribute_value", Integer.attribute_id, Integer.value)


class Real(Accessible):
    """
    """
    __tablename__ ="real"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.Integer, nullable=False)
    
    
sa.Index("real_attribute_value", Real.attribute_id, Real.value)
    
    
class Reference(Accessible):
    """
    """
    __tablename__ ="reference"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                      nullable=False
                      )
    
    order = sa.Column(sa.Integer, nullable=False, default=1)
    
    
sa.Index("reference_attribute_value", Reference.attribute_id, Reference.value)

    
class String(Accessible):
    """
    """
    __tablename__ ="string"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.Unicode, nullable=False)
    
    order = sa.Column(sa.Integer, nullable=False, default=1)

    
sa.Index("string_attribute_value", String.attribute_id, String.value)

    
class Keyword(Accessible):
    """
    """
    __tablename__ = "keyword"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False)
    
    title = sa.Column(sa.Unicode, nullable=False, index=True)
    
    is_synonym = sa.Column(sa.Boolean, nullable=False, default=True)
    
    
# -----------------------------------------------------------------------------
# Metadata
# -----------------------------------------------------------------------------

protocol_form_table = sa.Table("protocol_form", Accessible.metadata,
    sa.Column("protocol_id", sa.Integer, sa.ForeignKey("protocol.id"), 
              nullable=False),
    sa.Column("form_id", sa.Integer, sa.ForeignKey("form.id"), 
              nullable=False),
    sa.PrimaryKeyConstraint("protocol_id", "form_id")
    )


class Form(Accessible):
    """
    """
    __tablename__ = "form"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)
    
    prologue = sa.Column(sa.Text)
    
    epilogue = sa.Column(sa.Text)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)


class Hierarchy(Accessible):
    """
    """
    __tablename__ = "hierarchy"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    parent_schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                                 nullable=False)

    child_schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                                nullable=False)
    

class Schema(Accessible):
    """
    """
    __tablename__ = "schema"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False)
    
    description = sa.Column(sa.Text, nullable=False)
    
    is_association = sa.Column(sa.Boolean, nullable=False, default=False)
    
    is_virtual = sa.Column(sa.Boolean, nullable=False, default=False)
    
    
class Symbol(Accessible):
    """
    """
    __tablename__ = "symbol"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
         

class Attribute(Accessible):
    """
    """
    __tablename__ = "attribute"
    
    id = sa.Column(sa.Integer, primary_key=True) 
    
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"), 
                          nullable=False)
    
    symbol_id = sa.Column(sa.Integer, sa.ForeignKey("symbol.id"),
                          nullable=False)
    
    field_id = sa.Column(sa.Integer, sa.ForeignKey("field.id"),
                         nullable=False)
    
    order = sa.Column(sa.Integer, nullable=False, default=1)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    
class Field(Accessible):
    """
    """
    __tablename__ = "field"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False)
    
    description = sa.Column(sa.Text)
    
    type_id = sa.Column(sa.Integer, sa.ForeignKey("type.id"), nullable=False)
    
    hint_id = sa.Column(sa.Integer, sa.ForeignKey("hint.id"))
    
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"))
    
    vocabulary_id = sa.Column(sa.Integer, sa.ForeignKey("vocabulary.id"))
    
    is_searchable = sa.Column(sa.Boolean, nullable=False, default=False)
    
    is_required = sa.Column(sa.Boolean, nullable=False, default=False)
    
    is_inline_image = sa.Column(sa.Boolean)
    
    is_repeatable = sa.Column(sa.Boolean)
    
    minimum = sa.Column(sa.Integer)
    
    maximum = sa.Column(sa.Integer)
    
    width = sa.Column(sa.Integer)
    
    height = sa.Column(sa.Integer)
    
    url = sa.Column(sa.Unicode)
    
    comment = sa.Column(sa.Text)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now) 
    
    
class Type(Accessible):
    """
    """
    __tablename__ = "type"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    description = sa.Column(sa.Text)
    
    
class Hint(Accessible):
    """
    """
    __tablename__ = "hint"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    namespace = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    
vocabulary_term_table = sa.Table("vocabulary_term", Accessible.metadata,
    sa.Column("vocabulary_id", sa.Integer, sa.ForeignKey("vocabulary.id"),
              nullable=False),
    sa.Column("term_id", sa.Integer, sa.ForeignKey("term.id"),
              nullable=False),              
    sa.PrimaryKeyConstraint("vocabulary_id", "term_id")
    )

class Vocabulary(Accessible):
    """
    """
    __tablename__ = "vocabulary"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    
class Term(Accessible):    
    """
    """
    __tablename__ = "term"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    label = sa.Column(sa.Unicode)
    
    value = sa.Column(sa.Unicode, nullable=False)
    
    order = sa.Column(sa.Integer, nullable=False, default=1)

