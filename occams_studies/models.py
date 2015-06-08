from datetime import datetime, timedelta
import os
import re
import uuid

from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from occams_datastore.models import (  # NOQA
    ModelClass,
    Auditable,
    Referenceable, Describeable, Modifiable, HasEntities,
    Category,
    User, Schema, Attribute, Choice, State, Entity, Context)
from occams_datastore.utils.sql import JSON

from . import Session, log


Base = ModelClass(u'Base')


class groups:
    """
    Generates the OCCAMS-compatble group names that distinguaish site-level
    permissions.

    There are "dynamic" constants.

    The purpose of this utility is that there are no silent errors if the
    site/group names are mispelled (instead we'll get a synax error).
    """

    @staticmethod
    def principal(site=None, group=None):
        """
        Generates the principal name used internally by this application
        Supported keyword parameters are:
            site --  The site code
            group -- The group name
        """
        return site.name + ':' + group if site else group

    @staticmethod
    def administrator():
        return groups.principal(group='administrator')

    @staticmethod
    def manager(site=None):
        return groups.principal(site=site, group='manager')

    @staticmethod
    def reviewer(site=None):
        return groups.principal(site=site, group='reviewer')

    @staticmethod
    def enterer(site=None):
        return groups.principal(site=site, group='enterer')

    @staticmethod
    def consumer(site=None):
        return groups.principal(site=site, group='consumer')

    @staticmethod
    def member(site=None):
        return groups.principal(site=site, group='member')


class RootFactory(dict):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request


class StudyFactory(object):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, groups.manager(), ('view', 'add')),
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            study = Session.query(Study).filter_by(name=key).one()
        except orm.exc.NoResultFound:
            raise KeyError
        study.__parent__ = self
        return study


# Configured forms for the study
study_schema_table = sa.Table(
    'study_schema',
    Base.metadata,
    sa.Column(
        'study_id',
        sa.Integer(),
        sa.ForeignKey(
            'study.id',
            name='fk_study_schema_study_id',
            ondelete='CASCADE'),
        primary_key=True),
    sa.Column(
        'schema_id',
        sa.Integer(),
        sa.ForeignKey(
            Schema.id,
            name='fk_study_schema_schema_id',
            ondelete='CASCADE'),
        primary_key=True))


# Configured forms for the cycle
cycle_schema_table = sa.Table(
    'cycle_schema',
    Base.metadata,
    sa.Column(
        'cycle_id',
        sa.Integer(),
        sa.ForeignKey(
            'cycle.id',
            name='fk_cycle_schema_cycle_id',
            ondelete='CASCADE'),
        primary_key=True),
    sa.Column(
        'schema_id',
        sa.Integer(),
        sa.ForeignKey(
            Schema.id,
            name='fk_cycle_schema_schema_id',
            ondelete='CASCADE'),
        primary_key=True))


class Study(Base, Referenceable, Describeable, Modifiable, Auditable):

    __tablename__ = 'study'

    @property
    def __name__(self):
        return self.name

    @property
    def __acl__(self):
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'edit', 'delete')),
            (Allow, Authenticated, 'view')
        ]

    short_title = sa.Column(sa.Unicode, nullable=False)

    code = sa.Column(
        sa.String,
        nullable=False,
        doc='The Code for this study. Multiple studies may share the same '
            'code, if they are different arms of the same study.')

    consent_date = sa.Column(
        sa.Date,
        nullable=False,
        doc='The date that the latest consent was produced for this study.')

    is_randomized = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.false(),
        doc='Flag indicating that this study is randomized')

    randomization_schema_id = sa.Column(sa.Integer())

    randomization_schema = orm.relationship(
        Schema,
        foreign_keys=[randomization_schema_id])

    termination_schema_id = sa.Column(sa.Integer())

    termination_schema = orm.relationship(
        Schema,
        foreign_keys=[termination_schema_id])

    is_blinded = sa.Column(
        sa.Boolean,
        doc='Flag for randomized studies to indicate that '
            'they are also blinded')

    is_locked = sa.Column(
        sa.Boolean(),
        server_default=sa.sql.false(),
        doc='If set, data for this study cannot me modified anymore')

    start_date = sa.Column(
        sa.Date(),
        doc='If set, this study is available for data entry on or '
            'after this date')

    end_date = sa.Column(
        sa.Date(),
        doc='If set, data can only be entered before or after this date')

    reference_pattern = sa.Column(
        sa.Unicode,
        doc='Reference number pattern regular expresssion')

    reference_hint = sa.Column(
        sa.Unicode,
        doc='UI reference hint without regular expression syntax')

    # cycles backref'd from cycle

    # enrollments backref'd from enrollment

    # strata backref'd from stratum

    # arms backref'd from arms

    schemata = orm.relationship(
        Schema,
        secondary=study_schema_table,
        collection_class=set)

    def __getitem__(self, key):
        if key == 'cycles':
            return CycleFactory(self)

    def check(self, reference_number):
        if not self.reference_pattern:
            return True
        else:
            match = re.match(self.reference_pattern, reference_number)
            return match is not None

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            sa.Index('ix_%s_code' % cls.__tablename__, 'code'),
            sa.ForeignKeyConstraint(
                columns=['randomization_schema_id'],
                refcolumns=[Schema.id],
                name='fk_%s_randomization_schema_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.Index('ix_%s_randomization_schema_id',
                     'randomization_schema_id'),
            sa.ForeignKeyConstraint(
                columns=['termination_schema_id'],
                refcolumns=[Schema.id],
                name='fk_%s_termination_schema_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.Index('ix_%s_termination_schema_id', 'termination_schema_id'),
            sa.CheckConstraint(
                """
                (NOT is_randomized AND randomization_schema_id IS NULL)
                OR
                (is_randomized AND randomization_schema_id IS NOT NULL)
                """,
                name='ck_%s_randomization_schema_id' % cls.__tablename__),
            sa.CheckConstraint(
                """
                start_date <= consent_date
                AND (
                    end_date IS NULL
                    OR consent_date <= end_date)
                """,
                name='ck_%s_lifespan' % cls.__tablename__))


class CycleFactory(object):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, groups.manager(), ('view', 'add')),
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, parent):
        self.__parent__ = parent

    def __getitem__(self, key):
        try:
            cycle = Session.query(Cycle).filter_by(name=key).one()
        except orm.exc.NoResultFound:
            raise KeyError
        cycle.__parent__ = self
        return cycle


class Cycle(Base, Referenceable, Describeable, Modifiable, Auditable):
    """
    Study schedule represented as week cycles
    """

    __tablename__ = 'cycle'

    study_id = sa.Column(sa.Integer, nullable=False)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='cycles',
            lazy='dynamic',
            order_by='Cycle.week.asc().nullsfirst()',
            cascade='all, delete-orphan'))

    week = sa.Column(sa.Integer, doc='Week number')

    # future-proof field for exempting cycles
    threshold = sa.Column(
        sa.Integer,
        doc='The outer limit, in days, that this cycle may follow the '
            'previous schema before it is skipped as a missed visit.')

    is_interim = sa.Column(sa.Boolean, server_default=sa.sql.false())

    # visits backref'd from visit

    schemata = orm.relationship(
        Schema,
        secondary=cycle_schema_table,
        collection_class=set)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['study_id'],
                refcolumns=['study.id'],
                name='fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.UniqueConstraint(
                'study_id',
                'name',
                name='uq_%s_name' %
                cls.__tablename__),
            sa.UniqueConstraint(
                'study_id',
                'week',
                name='uq_%s_week' %
                cls.__tablename__))


class Arm(Base, Referenceable, Describeable,  Modifiable, Auditable):
    """
    A group of study strata
    """

    __tablename__ = 'arm'

    study_id = sa.Column(sa.Integer, nullable=False)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='arms',
            cascade='all,delete-orphan'),
        doc='The study theis pool belongs to')

    # strata backref'd from stratum

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=[cls.study_id],
                refcolumns=[Study.id],
                name=u'fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.UniqueConstraint(
                'study_id',
                'name',
                name=u'uq_%s_name' %
                cls.__tablename__))


class PatientFactory(object):

    @property
    def __acl__(self):
        acl = [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'add'))
        ]

        # Grant access to any member of any site and
        # filter patients within the view listing based
        # on which sites the user has access.
        for site in Session.query(Site):
            acl.extend([
                (Allow, groups.enterer(site), ('view', 'add')),
                (Allow, groups.reviewer(site), ('view',)),
                (Allow, groups.consumer(site), ('view',)),
                (Allow, groups.member(site), ('view',)),
            ])

        acl.extend([(Allow, Authenticated, 'view')])

        return acl

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            patient = (
                Session.query(Patient)
                .options(orm.joinedload('site'))
                .filter_by(pid=key)
                .one())
        except orm.exc.NoResultFound:
            raise KeyError

        # We do not specifically set the __parent__ attribute in this case
        # because we want users to be able to view the "/patients" URL
        # (with site-specific filtered results), but we do not want children
        # to inherit the permissions. Otherwise it allows
        # users of different sites to "view" the patient because of the
        # view permission on this node of hierarchy.

        return patient


class SiteFactory(object):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),

        # Authenticated users can access the resource,
        # but individual items will be filterd by access
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            site = Session.query(Site).filter_by(name=key).one()
        except orm.exc.NoResultFound:
            raise KeyError
        site.__parent__ = self
        return site


class Site(Base, Referenceable, Describeable, Modifiable, Auditable):
    """
    A facility within an organization
    """

    __tablename__ = 'site'

    @property
    def __name__(self):
        return self.name

    @property
    def __acl__(self):
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'edit', 'delete')),
            (Allow, groups.enterer(self), ('view',)),
            (Allow, groups.consumer(self), ('view',)),
            (Allow, groups.reviewer(self), ('view',)),
            (Allow, groups.member(self), 'view'),
            ]

    # patients backref'd from patient

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint(
                'name', name='uq_%s_name' % cls.__tablename__),)


# Configured forms to add to a patient (globally)
patient_schema_table = sa.Table(
    'patient_schema',
    Base.metadata,
    sa.Column(
        'schema_id',
        sa.Integer(),
        sa.ForeignKey(
            Schema.id,
            name='fk_patient_schema_schema_id',
            ondelete='CASCADE'),
        primary_key=True))


class Patient(Base, Referenceable, Modifiable, HasEntities, Auditable):

    __tablename__ = 'patient'

    @property
    def __name__(self):
        return self.pid

    @property
    def __acl__(self):
        site = self.site
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'edit', 'delete')),
            (Allow, groups.reviewer(site), ('view',)),
            (Allow, groups.enterer(site), ('view', 'edit')),
            (Allow, groups.consumer(site), 'view'),
            (Allow, groups.member(site), 'view')
            ]

    site_id = sa.Column(sa.Integer, nullable=False)

    site = orm.relationship(
        Site,
        backref=orm.backref(
            name='patients',
            cascade='all, delete-orphan',
            lazy=u'dynamic'),
        doc='The facility that the patient is visiting')

    pid = sa.Column(
        sa.Unicode,
        nullable=False,
        doc='Patient identification number.')

    initials = sa.Column(sa.Unicode)

    nurse = sa.Column(sa.Unicode)

    # references backref'd from patientreferences

    # partners backref'd from partner

    # enrollments backref'd from enrollment

    # strata backref'd from stratum

    # visits backref'd from visit

    def __getitem__(self, key):
        if key == 'enrollments':
            return EnrollmentFactory(self)
        elif key == 'visits':
            return VisitFactory(self)
        elif key == 'forms':
            return FormFactory(self)
        raise KeyError

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['site_id'],
                refcolumns=['site.id'],
                name='fk_%s_site_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.UniqueConstraint('pid', name='uq_%s_pid' % cls.__tablename__),
            sa.Index('ix_%s_site_id' % cls.__tablename__, 'site_id'),
            sa.Index('ix_%s_initials' % cls.__tablename__, 'initials'))


class ReferenceTypeFactory(object):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            reference_type = (
                Session.query(ReferenceType).filter_by(name=key).one())
        except orm.exc.NoResultFound:
            raise KeyError
        reference_type.__parent__ = self
        return reference_type


class ReferenceType(Base, Referenceable, Describeable, Modifiable):
    """
    Reference type sources
    """

    __tablename__ = 'reference_type'

    reference_pattern = sa.Column(
        sa.Unicode,
        doc='Reference number pattern regular expresssion')

    reference_hint = sa.Column(
        sa.Unicode,
        doc='UI reference hint without regular expression syntax')

    def check(self, reference_number):
        if not self.reference_pattern:
            return True
        else:
            match = re.match(self.reference_pattern, reference_number)
            return match is not None

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            )


class PatientReference(Base, Referenceable, Modifiable, Auditable):
    """
    References to a studies subject from other sources
    """

    __tablename__ = 'patient_reference'

    patient_id = sa.Column(sa.Integer, nullable=False)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='references',
            cascade='all, delete-orphan'))

    reference_type_id = sa.Column(sa.Integer, nullable=False)

    reference_type = orm.relationship(ReferenceType)

    reference_number = sa.Column(sa.String, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['reference_type_id'],
                refcolumns=['reference_type.id'],
                name='fk_%s_reference_type_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            sa.Index(
                'ix_%s_reference_number' % cls.__tablename__,
                'reference_number'),
            sa.UniqueConstraint(
                'patient_id',
                'reference_type_id',
                'reference_number',
                name=u'uq_%s_reference' % cls.__tablename__))


class Partner(Base, Referenceable, Modifiable, HasEntities, Auditable):
    """
    A subject's partner.
    """

    __tablename__ = 'partner'

    patient_id = sa.Column(sa.Integer, nullable=False)

    patient = orm.relationship(
        Patient,
        primaryjoin=(patient_id == Patient.id),
        backref=orm.backref(
            name='partners',
            cascade='all, delete-orphan'),
        doc=u'The Patient that reported this partner.')

    enrolled_patient_id = sa.Column(sa.Integer)

    # One-way ORM orm.relationship
    enrolled_patient = orm.relationship(
        Patient,
        primaryjoin=(enrolled_patient_id == Patient.id),
        # Setup the backref for back-populate cascade
        backref=orm.backref(name='from_partners'),
        doc=u'This partner is also a patient; This property references that'
            u'patient entry')

    # The date upon which the data was reported
    report_date = sa.Column(
        sa.Date,
        nullable=False,
        doc=u'The date that the reporting patient reported this partner')

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            sa.ForeignKeyConstraint(
                columns=['enrolled_patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_enrolled_patient_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            sa.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            sa.Index(
                'ix_%s_enrolled_patient_id' % cls.__tablename__,
                'enrolled_patient_id'),
            sa.Index('ix_%s_report_date' % cls.__tablename__, 'report_date'))


class EnrollmentFactory(object):

    @property
    def __acl__(self):
        site = self.__parent__.site
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'add')),
            (Allow, groups.reviewer(site), ('view')),
            (Allow, groups.enterer(site), ('view', 'add')),
            (Allow, groups.consumer(site), 'view'),
            ]

    def __init__(self, parent):
        self.__parent__ = parent

    def __getitem__(self, key):
        try:
            enrollment = (
                Session.query(Enrollment)
                .options(orm.joinedload('patient').joinedload('site'))
                .filter_by(id=key).one())
        except orm.exc.NoResultFound:
            raise KeyError
        enrollment.__parent__ = self
        return enrollment


# Configured forms for termination
termination_schema_table = sa.Table(
    'termination_schema',
    Base.metadata,
    sa.Column(
        'schema_id',
        sa.Integer(),
        sa.ForeignKey(
            Schema.id,
            name='fk_termination_schema_schema_id',
            ondelete='CASCADE'),
        primary_key=True))


class Enrollment(Base,  Referenceable, Modifiable, HasEntities, Auditable):
    """
    A patient's participation in a study.
    """

    __tablename__ = 'enrollment'

    @property
    def __name__(self):
        return str(self.id)

    @property
    def __acl__(self):
        site = self.patient.site
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'edit', 'delete', 'randomize', 'terminate')),  # NOQA
            (Allow, groups.reviewer(site), ('view')),  # NOQA
            (Allow, groups.enterer(site), ('view', 'edit', 'terminate')),  # NOQA
            (Allow, groups.consumer(site), 'view')
            ]

    patient_id = sa.Column(sa.Integer, nullable=False,)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='enrollments',
            cascade='all, delete-orphan',
            lazy='dynamic',
            order_by='Enrollment.consent_date.desc()'))

    study_id = sa.Column(sa.Integer, nullable=False,)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='enrollments',
            # The list of enrollments from the study perspective can get quite
            # long, so we implement as query to allow filtering/limit-offset
            lazy='dynamic',
            cascade='all, delete-orphan'))

    # First consent date (i.e. date of enrollment)
    consent_date = sa.Column(sa.Date, nullable=False)

    # Latest consent date
    # Note that some consent dates may be acqured AFTER the patient has
    # terminated
    latest_consent_date = sa.Column(
        sa.Date,
        nullable=False,
        default=lambda c: c.current_parameters['consent_date'])

    # Termination date
    termination_date = sa.Column(sa.Date)

    # A reference specifically for this enrollment (blinded studies, etc)
    reference_number = sa.Column(
        sa.Unicode,
        doc='Identification number within study')

    # stratum backref'd from straum

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['study_id'],
                refcolumns=['study.id'],
                name='fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            sa.Index('ix_%s_study_id' % cls.__tablename__, 'study_id'),
            # A patient may enroll only once in the study per day
            sa.UniqueConstraint('patient_id', 'study_id', 'consent_date'),
            sa.Index(
                'ix_%s_reference_number' % cls.__tablename__,
                'reference_number'),
            sa.CheckConstraint(
                """
                consent_date <= latest_consent_date
                AND (
                    termination_date IS NULL
                    OR latest_consent_date <= termination_date)
                """,
                name='ck_%s_lifespan' % cls.__tablename__))


class Stratum(Base, Referenceable, Modifiable, HasEntities, Auditable):
    """
    A possible study enrollment assignement.
    Useful for enrolling randomized patients.
    """

    __tablename__ = 'stratum'

    study_id = sa.Column(sa.Integer, nullable=False)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='strata',
            lazy='dynamic',
            cascade='all,delete-orphan'))

    arm_id = sa.Column(sa.Integer, nullable=False)

    arm = orm.relationship(
        Arm,
        backref=orm.backref(
            name='strata',
            lazy='dynamic',
            cascade='all,delete-orphan'))

    label = sa.Column(sa.Unicode)

    block_number = sa.Column(sa.Integer, nullable=False)

    # Rename to randid
    reference_number = sa.Column(
        sa.String,
        nullable=False,
        doc='A pregenerated value assigned to the patient per-study. '
            'This is not a Study ID, this is only for statistician. ')

    randid = hybrid_property(
        lambda self: self.reference_number,
        lambda self, value: setattr(self, 'reference_number', value))

    patient_id = sa.Column(sa.Integer)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='strata'))

    enrollments = orm.relationship(
        Enrollment,
        viewonly=True,
        primaryjoin=(
            study_id == Enrollment.study_id) & (
            patient_id == Enrollment.patient_id),
        foreign_keys=[Enrollment.study_id, Enrollment.patient_id],
        backref=orm.backref(
            name='stratum',
            uselist=False,
            viewonly=True))

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=[cls.study_id],
                refcolumns=[Study.id],
                name=u'fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=[cls.arm_id],
                refcolumns=[Arm.id],
                name=u'fk_%s_arm_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=[cls.patient_id],
                refcolumns=[Patient.id],
                name=u'fk_%s_patient_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.UniqueConstraint(
                cls.study_id, cls.reference_number,
                name=u'uq_%s_reference_number' % cls.__tablename__),
            sa.UniqueConstraint(
                cls.study_id, cls.patient_id,
                name=u'uq_%s_patient_id' % cls.__tablename__),
            sa.Index(
                'ix_%s_block_number' % cls.__tablename__, cls.block_number),
            sa.Index(
                'ix_%s_patient_id' % cls.__tablename__, cls.block_number),
            sa.Index('ix_%s_arm_id' % cls.__tablename__, cls.arm_id))


class VisitFactory(object):

    @property
    def __acl__(self):
        site = self.__parent__.site
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'add')),
            (Allow, groups.reviewer(site), ('view')),
            (Allow, groups.enterer(site), ('view', 'add')),
            (Allow, groups.consumer(site), 'view'),
        ]

    def __init__(self, parent):
        self.__parent__ = parent

    def __getitem__(self, key):
        try:
            key = datetime.strptime(key, '%Y-%m-%d').date()
        except ValueError:
            raise KeyError
        try:
            visit = (
                Session.query(Visit)
                .options(orm.joinedload('patient').joinedload('site'))
                .filter_by(patient=self.__parent__)
                .filter_by(visit_date=key)
                .one())
        except orm.exc.NoResultFound:
            raise KeyError
        visit.__parent__ = self
        return visit


visit_cycle_table = sa.Table(
    'visit_cycle',
    Base.metadata,
    sa.Column(
        'visit_id',
        sa.Integer,
        sa.ForeignKey(
            'visit.id',
            name='fk_visit_cycle_visit_id',
            ondelete='CASCADE'),
        primary_key=True),
    sa.Column(
        'cycle_id',
        sa.Integer,
        sa.ForeignKey(
            'cycle.id',
            name='fk_visit_cycle_cycle_id',
            ondelete='CASCADE'),
        primary_key=True))


class Visit(Base, Referenceable, Modifiable, HasEntities, Auditable):

    __tablename__ = 'visit'

    @property
    def __name__(self):
        return self.visit_date.isoformat()

    @property
    def __acl__(self):  #
        site = self.patient.site
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'edit', 'delete')),  # NOQA
            (Allow, groups.reviewer(site), ('view')),  # NOQA
            (Allow, groups.enterer(site), ('view', 'edit')),  # NOQA
            (Allow, groups.consumer(site), 'view')
            ]

    patient_id = sa.Column(sa.Integer, nullable=False)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='visits',
            cascade='all, delete-orphan',
            lazy='dynamic',
            order_by='Visit.visit_date.desc()'))

    cycles = orm.relationship(
        Cycle,
        secondary=visit_cycle_table,
        order_by='Cycle.title.asc()',
        backref=orm.backref(
            name='visits',
            lazy='dynamic'))

    visit_date = sa.Column(sa.Date, nullable=False)

    def __getitem__(self, key):
        if key == 'forms':

            return FormFactory(self)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=[Patient.id],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.Index('ix_%s_patient' % cls.__tablename__, 'patient_id'),
            sa.UniqueConstraint(
                'patient_id', 'visit_date',
                name='uq_%s_patient_id_visit_date' % cls.__tablename__))


class FormFactory(object):

    @property
    def __acl__(self):
        if isinstance(self.__parent__, (Enrollment, Visit)):
            site = self.__parent__.patient.site
        elif isinstance(self.__parent__, Patient):
            site = self.__parent__.site
        else:
            raise Exception('Unable to determiine patient')

        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'add')),
            (Allow, groups.enterer(site), ('view', 'add')),
            (Allow, groups.consumer(site), 'view')
            ]

    def __init__(self, parent):
        self.__parent__ = parent

    def __getitem__(self, key):
        try:
            entity = (
                Session.query(Entity)
                .options(orm.joinedload('state'))
                .filter_by(id=key)
                .one())
        except orm.exc.NoResultFound:
            raise KeyError

        # Force a state for now until we implement customizable workflows
        # Side-effect: will commit state change to the database
        # XXX: This is really bad form as we're applying
        # side-effects to a GET request, but there is no time
        # to make this look prety...
        if not entity.state:
            entity.state = (
                Session.query(State)
                .filter_by(name='pending-entry')
                .one())

        entity.__parent__ = self

        return entity


def _entity_acl(self):
    factory = self.__parent__
    study_item = factory.__parent__
    if isinstance(study_item, Patient):
        site = study_item.site
    elif isinstance(study_item, Enrollment) or isinstance(study_item, Visit):
        site = study_item.patient.site
    else:
        Exception(u'Cannot find site for entity')

    # We used to restrict view based on whether the user
    # could view PHI, but now we make everyone pass a HIPAA compliance
    # course

    return [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, groups.manager(), ('view', 'edit', 'delete', 'transition')),
        (Allow, groups.reviewer(site), ('view', 'transition')),
        (Allow, groups.enterer(site), ('view', 'edit', 'delete')),
        (Allow, groups.consumer(site), 'view')
    ]

Entity.__acl__ = property(_entity_acl)


class ExportFactory(object):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, groups.manager(), ('view', 'add')),
        (Allow, groups.consumer(), 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            export = (
                Session.query(Export)
                .options(orm.joinedload('owner_user'))
                .filter_by(id=key)
                .one())
        except orm.exc.NoResultFound:
            raise KeyError
        export.__parent__ = self
        return export


class Export(Base, Referenceable, Modifiable, Auditable):
    """
    Metadata about an export, such as file contents and experation date.
    """

    __tablename__ = 'export'

    @property
    def __name__(self):
        return str(self.id)

    @property
    def __acl__(self):
        return [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, self.owner_user.key, ('view', 'edit', 'delete')),
            ]

    name = sa.Column(
        sa.String,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        doc='System name, useful for keep track of asynchronous progress')

    owner_user_id = sa.Column(sa.Integer, nullable=False)

    owner_user = orm.relationship(User, foreign_keys=[owner_user_id])

    expand_collections = sa.Column(sa.Boolean, nullable=False, default=False)

    use_choice_labels = sa.Column(sa.Boolean, nullable=False, default=False)

    notify = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        doc='If set, notify the user that the export has completed')

    status = sa.Column(
        sa.Enum('failed', 'pending', 'complete', name='export_status'),
        nullable=False,
        default='pending')

    contents = sa.Column(
        JSON,
        nullable=False,
        doc="""
            A snapshot of the contents of this export with some metadata.
            Since we do not want to pollute a whole other table with
            meaninless names. This also helps preserve file names
            if tables/schemata change names, and keeps names preserved
            AT THE TIME this export was generated.
            """)

    @property
    def path(self):
        """
        Virtual attribute that returns the export's path in the filesystem
        """
        # XXX: This might come back and haunt us if Session is not configured
        export_dir = Session.info['settings']['studies.export.dir']
        return os.path.join(export_dir, self.name)

    @property
    def file_size(self):
        """
        Virtual attribute that returns export's file size (if complete)
        """
        if self.status == 'complete':
            return os.path.getsize(self.path)

    @property
    def expire_date(self):
        """
        Virtual attribute that returns the export's expiration date (if avail)
        """
        # XXX: This might come back and haunt us if Session is not configured
        delta = Session.info['settings'].get('studies.export.expire')
        if delta:
            return self.modify_date + timedelta(delta)

    @property
    def redis_key(self):
        return self.__tablename__ + ':' + self.name

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=[cls.owner_user_id],
                refcolumns=[User.id],
                name=u'fk_%s_owner_user_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.UniqueConstraint(
                cls.name, name=u'uq_%s_name' % cls.__tablename__),
            sa.Index(
                'ix_%s_owner_user_id' % cls.__tablename__,
                cls.owner_user_id))
