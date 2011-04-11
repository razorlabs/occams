""" Clinical Models
"""

from datetime import datetime

from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import Table
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.types import Boolean
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode

from sqlalchemy.orm import relation as Relationship

from avrc.data.store.model import Model

__all__ = (
    'domain_schema_table',
    'enrollment_instance_table',
    'partner_instance_table',
    'protocol_schema_table',
    'visit_protocol_table',
    'subject_instance_table',
    'visit_instance_table',
    'Subject',
    'Partner',
    'Domain',
    'Protocol',
    'Enrollment',
    'Visit',
    )

#
# Joining tables
#

domain_schema_table = Table('domain_schema', Model.metadata,
    Column('domain_id', ForeignKey('domain.id', ondelete='CASCADE')),
    Column('schema_id', ForeignKey('schema.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('domain_id', 'schema_id')
    )

protocol_schema_table = Table('protocol_schema', Model.metadata,
    Column('protocol_id', ForeignKey('protocol.id', ondelete='CASCADE')),
    Column('schema_id', ForeignKey('schema.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('protocol_id', 'schema_id')
    )

visit_protocol_table = Table('visit_protocol', Model.metadata,
    Column('visit_id', ForeignKey('visit.id', ondelete='CASCADE')),
    Column('protocol_id', ForeignKey('protocol.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('visit_id', 'protocol_id')
    )

# For object/eav assocation tables, the eav data needs to be deleted first
# before the contextual object is removed.

subject_instance_table = Table('subject_instance', Model.metadata,
    Column('subject_id', ForeignKey('subject.id', ondelete='RESTRICT')),
    Column('instance_id', ForeignKey('instance.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('subject_id', 'instance_id')
    )

partner_instance_table = Table('partner_instance', Model.metadata,
    Column('partner_id', ForeignKey('partner.id', ondelete='RESTRICT')),
    Column('instance_id', ForeignKey('instance.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('partner_id', 'instance_id')
    )

enrollment_instance_table = Table('enrollment_instance', Model.metadata,
    Column('enrollment_id', ForeignKey('enrollment.id', ondelete='RESTRICT')),
    Column('instance_id', ForeignKey('instance.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('enrollment_id', 'instance_id')
    )

visit_instance_table = Table('visit_instance', Model.metadata,
    Column('visit_id', ForeignKey('visit.id', ondelete='RESTRICT')),
    Column('instance_id', ForeignKey('instance.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('visit_id', 'instance_id')
    )

#
# Entity tables
#

class Subject(Model):
    """ We keep track of subjects here and reference them throughout the
        database using an internal identifier.

        Attributes:
            id: (int) machine generated id number
            uid: (int) an external reference number
    """
    __tablename__ = 'subject'

    id = Column(Integer, primary_key=True)

    zid = Column(Integer, nullable=False, unique=True)

    uid = Column(Integer, nullable=False, index=True)

    nurse_email = Column(Unicode)

    aeh = Column(Unicode, index=True)

    our = Column(Unicode, unique=True)

    enrollments = Relationship('Enrollment')

    instances = Relationship(
        'Instance',
        secondary=subject_instance_table,
        )

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
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

    id = Column(Integer, primary_key=True)

    zid = Column(Integer, unique=True, nullable=False)

    subject_id = Column(
        ForeignKey(Subject.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship(
        'Subject',
        primaryjoin='Partner.subject_id == Subject.id'
        )

    enrolled_subject_id = Column(
        ForeignKey(Subject.id, ondelete='SET NULL'),
        index=True
        )

    enrolled_subject = Relationship(
        'Subject',
        primaryjoin='Partner.enrolled_subject_id == Subject.id'
        )

    visit_date = Column(Date, nullable=False, index=True)

    instances = Relationship(
        'Instance',
        secondary=partner_instance_table,
        )

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
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

    id = Column(Integer, primary_key=True)

    zid = Column(Integer, nullable=False, unique=True)

    code = Column(Unicode, nullable=False, index=True)

    title = Column(Unicode, nullable=False, unique=True)

    consent_date = Column(Date, nullable=False)

    schemata = Relationship('Schema', secondary=domain_schema_table)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
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

    id = Column(Integer, primary_key=True)

    zid = Column(Integer, nullable=False, unique=True)

    domain_id = Column(
        ForeignKey(Domain.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    domain = Relationship('Domain')

    cycle = Column(Integer)

    threshold = Column(Integer)

    schemata = Relationship(
        'Schema',
        secondary=protocol_schema_table,
        )

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )


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

    id = Column(Integer, primary_key=True)

    zid = Column(Integer, nullable=False, unique=True)

    domain_id = Column(
        ForeignKey(Domain.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    domain = Relationship('Domain')

    subject_id = Column(
        ForeignKey(Subject.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship('Subject')

    start_date = Column(Date, nullable=False)

    consent_date = Column(Date, nullable=False)

    stop_date = Column(Date)

    instances = Relationship(
        'Instance',
        secondary=enrollment_instance_table
        )

    eid = Column(Unicode, index=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )

    __table_args__ = (
        UniqueConstraint('domain_id', 'subject_id', 'start_date'),
        {})


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

    id = Column(Integer, primary_key=True)

    zid = Column(Integer, nullable=False, unique=True)

    subject_id = Column(
        ForeignKey(Subject.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship('Subject')

    protocols = Relationship('Protocol', secondary=visit_protocol_table)

    instances = Relationship('Instance', secondary=visit_instance_table)

    visit_date = Column(Date, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )
