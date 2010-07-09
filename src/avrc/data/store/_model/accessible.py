"""
Data store for objects. 
"""

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Accessible = declarative_base()

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
    __tablename__ = "visit"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    protocol_id = sa.Column(sa.Integer, sa.ForeignKey("protocol.id"), 
                            nullable=False)
    
    subject_id = sa.Column(sa.Integer, sa.ForeignKey("subject.id"), 
                           nullable=False)
    
    
    serial = sa.Column(sa.Unicode, index=True )


visit_instance_table = sa.Table("visit_instance", Accessible.meta,
    sa.Column("visit_id", sa.ForeignKey("visit.id"), nullable=False),
    sa.Column("instance_id", sa.ForeignKey("instance.id"), nullable=False),
    sa.PrimaryKeyConstraint("visit_id", "instance_id")
    )


class Visit(Accessible):
    """
    """
    
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
    
    name = sa.Column(sa.Unicode, nullable=False, unique=True)
    
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
    
    __table_args__ = (sa.Index("value", "attribute_id", "value"),{})
    
    
class Integer(Accessible):
    """
    """
    ___tablename__ ="integer"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.Integer, nullable=False, index=True)
    
    __table_args__ = (sa.Index("value", "attribute_id", "value"),{})
    

class Real(Accessible):
    """
    """
    ___tablename__ ="integer"
    
    instance_id = sa.Column(sa.Integer, sa.ForeignKey("instance.id"),
                            nullable=False,
                            primary_key=True)
    
    attribute_id = sa.Column(sa.Integer, sa.ForeignKey("attribute.id"),
                            nullable=False,
                            primary_key=True)
    
    value = sa.Column(sa.Integer, nullable=False, index=True)
    
    __table_args__ = (sa.Index("value", "attribute_id", "value"),{})
    
    