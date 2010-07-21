"""
Data Definifinion Library, in this case, SQLAlcchemy
Data store for objects. 
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
     
     
def setup_fia(engine):
    """
    """
    _setup_base(FIA, engine)
    
    
def setup_pii(engine):
    """
    """
    _setup_base(PII, engine)
    
# -----------------------------------------------------------------------------
# Personal Information
# -----------------------------------------------------------------------------

class Name(PII):
    """
    """
    __tablename__ = "name"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    ourid = sa.Column(sa.Integer, nullable=False, index=True)
    
    first = sa.Column(sa.Unicode, nullable=False, index=True)
    
    middle = sa.Column(sa.Unicode)
    
    last = sa.Column(sa.Unicode, nullable=False, index=True)
    
    sur = sa.Column(sa.Unicode)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)
    
    
class State(PII):
    """
    """
    __tablename__ = "state"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    abbreviation = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    name = sa.Column(sa.Unicode, nullable=False)
    
    
class Contact(PII):
    """
    """
    __tablename__ = "contact"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    ourid = sa.Column(sa.Integer, nullable=False, index=True)
    
    phone = sa.Column(sa.Unicode, index=True)
    
    address1 = sa.Column(sa.Unicode)
    
    address2 = sa.Column(sa.Unicode)
    
    city = sa.Column(sa.Unicode)

    state_id = sa.Column(sa.Integer, sa.ForeignKey("state.id"))
    
    zip = sa.Column(sa.Integer)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)
    
    
class Demographic(PII):
    """
    """
    __tablename__ = "demographic"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    ourid = sa.Column(sa.Integer, nullable=False, index=True)
    
    birthdate = sa.Column(sa.DateTime)

    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)


# -----------------------------------------------------------------------------
# Visit
# -----------------------------------------------------------------------------

class Subject(FIA):
    """
    """
    __tablename__ = "subject"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    
class Protocol(FIA):
    """
    """
    __tablename__ = "protocol"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    short = sa.Column(sa.Unicode, index=True)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    description = sa.Column(sa.Text)
    
    
class Enrollment(FIA): 
    """
    """
    __tablename__ = "enrollment"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    protocol_id = sa.Column(sa.Integer, sa.ForeignKey("protocol.id"), 
                            nullable=False)
    
    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subject.id"), 
                           nullable=False)
    
    
    serial = sa.Column(sa.Unicode, index=True )


visit_instance_table = sa.Table("visit_instance", FIA.metadata,
    sa.Column("visit_id", sa.ForeignKey("visit.id"), nullable=False),
    sa.Column("instance_id", sa.ForeignKey("instance.id"), nullable=False),
    sa.PrimaryKeyConstraint("visit_id", "instance_id")
    )


class Visit(FIA):
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

class Instance(FIA):
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
    

class Binary(FIA):
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


class Datetime(FIA):
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
    
    
class Integer(FIA):
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


class Real(FIA):
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
    
    
class Reference(FIA):
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

    
class String(FIA):
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

    
class Keyword(FIA):
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

protocol_form_table = sa.Table("protocol_form", FIA.metadata,
    sa.Column("protocol_id", sa.Integer, sa.ForeignKey("protocol.id"), 
              nullable=False),
    sa.Column("form_id", sa.Integer, sa.ForeignKey("form.id"), 
              nullable=False),
    sa.PrimaryKeyConstraint("protocol_id", "form_id")
    )


class Form(FIA):
    """
    """
    __tablename__ = "form"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                          nullable=False)
    
    prologue = sa.Column(sa.Text)
    
    epilogue = sa.Column(sa.Text)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)


class Hierarchy(FIA):
    """
    """
    __tablename__ = "hierarchy"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    parent_schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                                 nullable=False)

    child_schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"),
                                nullable=False)
    

class Schema(FIA):
    """
    """
    __tablename__ = "schema"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False)
    
    description = sa.Column(sa.Text, nullable=False)
    
    is_association = sa.Column(sa.Boolean, nullable=False, default=False)
    
    is_virtual = sa.Column(sa.Boolean, nullable=False, default=False)
    
    
class Symbol(FIA):
    """
    """
    __tablename__ = "symbol"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
         

class Attribute(FIA):
    """
    """
    __tablename__ = "attribute"
    
    id = sa.Column(sa.Integer, primary_key=True) 
    
    schema_id = sa.Column(sa.Integer, sa.ForeignKey("schema.id"), 
                          nullable=False)
    
    schema = orm.relation("Schema", uselist=False)
    
    symbol_id = sa.Column(sa.Integer, sa.ForeignKey("symbol.id"),
                          nullable=False)
    
    symbol = orm.relation("Symbol", uselist=False)
    
    field_id = sa.Column(sa.Integer, sa.ForeignKey("field.id"))
    
    field = orm.relation("Field", uselist=False)
    
    order = sa.Column(sa.Integer, nullable=False, default=1)
    
    createdate = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    
class Field(FIA):
    """
    """
    __tablename__ = "field"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False)
    
    description = sa.Column(sa.Text)
    
    type_id = sa.Column(sa.Integer, sa.ForeignKey("type.id"), nullable=False)
    
    type = orm.relation("Type", uselist=False)
    
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
    
    
class Type(FIA):
    """
    """
    __tablename__ = "type"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    title = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    description = sa.Column(sa.Text)
    
    
class Hint(FIA):
    """
    """
    __tablename__ = "hint"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    namespace = sa.Column(sa.Unicode, nullable=False, unique=True)
    
    
vocabulary_term_table = sa.Table("vocabulary_term", FIA.metadata,
    sa.Column("vocabulary_id", sa.Integer, sa.ForeignKey("vocabulary.id"),
              nullable=False),
    sa.Column("term_id", sa.Integer, sa.ForeignKey("term.id"),
              nullable=False),              
    sa.PrimaryKeyConstraint("vocabulary_id", "term_id")
    )

class Vocabulary(FIA):
    """
    """
    __tablename__ = "vocabulary"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    
class Term(FIA):    
    """
    """
    __tablename__ = "term"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    label = sa.Column(sa.Unicode)
    
    value = sa.Column(sa.Unicode, nullable=False)
    
    order = sa.Column(sa.Integer, nullable=False, default=1)

