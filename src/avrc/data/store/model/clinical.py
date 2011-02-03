""" Clinical Models
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store.model import Model


domain_schema_table = sa.Table('domain_schema', Model.metadata,
    sa.Column('domain_id', sa.ForeignKey('domain.id'), primary_key=True),
    sa.Column('schema_id', sa.ForeignKey('schema.id'), primary_key=True)
    )


enrollment_instance_table = sa.Table('enrollment_instance', Model.metadata,
    sa.Column('enrollment_id', sa.ForeignKey('enrollment.id'), primary_key=True),
    sa.Column('instance_id', sa.ForeignKey('instance.id'),  primary_key=True),
    )


partner_instance_table = sa.Table('partner_instance', Model.metadata,
    sa.Column('partner_id', sa.ForeignKey('partner.id'), primary_key=True),
    sa.Column('instance_id', sa.ForeignKey('instance.id'), primary_key=True)
    )


protocol_schema_table = sa.Table('protocol_schema', Model.metadata,
    sa.Column('protocol_id', sa.ForeignKey('protocol.id'), primary_key=True),
    sa.Column('schema_id',sa.ForeignKey('schema.id'), primary_key=True)
    )


subject_instance_table = sa.Table('subject_instance', Model.metadata,
    sa.Column('subject_id', sa.ForeignKey('subject.id'), primary_key=True),
    sa.Column('instance_id', sa.ForeignKey('instance.id'), primary_key=True),
    )


visit_protocol_table = sa.Table('visit_protocol', Model.metadata,
    sa.Column('visit_id', sa.ForeignKey('visit.id'), primary_key=True),
    sa.Column('protocol_id', sa.ForeignKey('protocol.id'), primary_key=True),
    )


visit_enrollment_table = sa.Table('visit_enrollment', Model.metadata,
    sa.Column('visit_id', sa.ForeignKey('visit.id'), primary_key=True),
    sa.Column('enrollment_id', sa.ForeignKey('enrollment.id'), primary_key=True),
    )


visit_instance_table = sa.Table('visit_instance', Model.metadata,
    sa.Column('visit_id', sa.ForeignKey('visit.id'), primary_key=True),
    sa.Column('instance_id', sa.ForeignKey('instance.id'), primary_key=True),
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

    our = sa.Column(sa.Unicode, unique=True)

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

    domain_id = sa.Column(sa.ForeignKey('domain.id'), nullable=False)

    domain = orm.relation('Domain', uselist=False)

    subject_id = sa.Column(sa.ForeignKey('subject.id'), nullable=False)

    subject = orm.relation('Subject', uselist=False)

    start_date = sa.Column(sa.Date, nullable=False)

    consent_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    instances = orm.relation('Instance', secondary=enrollment_instance_table)

    eid = sa.Column(sa.Unicode, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    __table_args__ = (
        sa.UniqueConstraint('domain_id', 'subject_id', 'start_date'),
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

    id = sa.Column(sa.Integer, primary_key=True)

    zid = sa.Column(sa.Integer, nullable=False, unique=True)

    enrollments = orm.relation('Enrollment', secondary=visit_enrollment_table)

    protocols = orm.relation('Protocol', secondary=visit_protocol_table)

    instances = orm.relation('Instance', secondary=visit_instance_table)

    visit_date = sa.Column(sa.Date, nullable=False)


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

    domain_id = sa.Column(sa.ForeignKey('domain.id'), nullable=False)

    domain = orm.relation('Domain', uselist=False)

    schemata = orm.relation('Schema', secondary=protocol_schema_table)

    cycle = sa.Column(sa.Integer)

    threshold = sa.Column(sa.Integer)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


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

    subject_id = sa.Column(sa.ForeignKey('subject.id'), nullable=False, index=True)

    subject = orm.relation(
        'Subject',
        uselist=False,
        primaryjoin='Partner.subject_id == Subject.id'
        )

    enrolled_subject_id = sa.Column(sa.ForeignKey('subject.id'), index=True)

    enrolled_subject = orm.relation(
        'Subject',
        uselist=False,
        primaryjoin='Partner.enrolled_subject_id == Subject.id'
        )

    visit_date = sa.Column(sa.Date, nullable=False, index=True)

    instances = orm.relation('Instance', secondary=partner_instance_table)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)
