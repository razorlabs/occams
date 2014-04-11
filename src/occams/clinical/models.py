"""
Clinical Models

SQL Database persisted clinical data that will become the heart of this module
as we transition towards a SQL-driven application.
"""

from __future__ import absolute_import
from datetime import date, timedelta
import os
import uuid

from six import u
from sqlalchemy import (
    engine_from_config,
    Table, Column,
    ForeignKey, ForeignKeyConstraint, UniqueConstraint, Index,
    Boolean, Date, Enum, Integer, Unicode)
from sqlalchemy.orm import object_session, backref, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

# import everything so we can also use DS models from this module
from occams.datastore.models import (  # NOQA
    Auditable,
    Referenceable, Describeable, Modifiable,
    Category,
    HasEntities,
    ModelClass,
    User,
    Schema, Section, Attribute, Choice, State, Entity, Context)
from occams.datastore.utils.sql import JSON

from . import log, Session


Base = ModelClass(u'Base')


def includeme(config):
    settings = config.registry.settings
    Session.configure(bind=engine_from_config(settings, 'app.db.'))
    log.debug('Clinical connected to: "%s"' % repr(Session.bind.url))
    Base.metadata.info['settings'] = settings


visit_cycle_table = Table(
    'visit_cycle',
    Base.metadata,
    Column('visit_id',
           Integer,
           ForeignKey('visit.id',
                      name='fk_visit_cycle_visit_id',
                      ondelete='CASCADE'),
           primary_key=True),
    Column('cycle_id',
           Integer,
           ForeignKey('cycle.id',
                      name='fk_visit_cycle_cycle_id',
                      ondelete='CASCADE'),
           primary_key=True))


class Study(Base, Referenceable, Describeable, Modifiable, Auditable):

    __tablename__ = 'study'

    short_title = Column(Unicode, nullable=False)

    code = Column(
        Unicode,
        nullable=False,
        doc='The Code for this study. Multiple studies may share the same '
            'code, if they are different arms of the same study.')

    consent_date = Column(
        Date,
        nullable=False,
        doc='The date that the latest consent was produced for this study.')

    is_blinded = Column(
        Boolean,
        doc='Flag for randomized studies to indicate that '
            'they are also blinded')

    # TODO: add is_randomized

    @property
    def duration(self):
        Session = object_session(self)
        query = (
            Session.query(Cycle)
            .filter((Cycle.study == self))
            .order_by(
                # Nulls last (vendor-agnostic)
                (Cycle.week is not None).desc(),
                Cycle.week.desc())
            .limit(1))
        try:
            cycle = query.one()
        except NoResultFound:
            # There are no results, so this study has no length
            duration = timedelta()
        else:
            # No exception thrown, process result
            if cycle.week >= 0:
                duration = timedelta(cycle.week * 7)
            else:
                # No valid week data, give a lot of time
                duration = timedelta.max
        return duration

    # cycles is backref'ed in the Cycle class

    # enrollments is backrefed in the Enrollment class

    # TODO: verify why this is nullable if the add event handler sets this
    # anyway
    category_id = Column(Integer)

    category = relationship(
        Category,
        single_parent=True,
        cascade='all,delete-orphan',
        primaryjoin=(category_id == Category.id))

    # BBB: nullable because category_id is nullable
    log_category_id = Column(Integer)

    log_category = relationship(
        Category,
        single_parent=True,
        cascade='all,delete-orphan',
        primaryjoin=(log_category_id == Category.id))

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['category_id'],
                refcolumns=[Category.id],
                name='fk_%s_category_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['log_category_id'],
                refcolumns=[Category.id],
                name='fk_%s_log_category_id' % cls.__tablename__,
                ondelete='SET NULL'),
            # One category per table
            UniqueConstraint(
                'category_id',
                name='uq_%s_category_id' %
                cls.__tablename__,),
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            Index('ix_%s_code' % cls.__tablename__, 'code'),
            Index('ix_%s_category_id' % cls.__tablename__, 'category_id'),
            Index('ix_%s_log_category_id' % cls.__tablename__,
                  'log_category_id'))


class Cycle(Base, Referenceable, Describeable, Modifiable, Auditable):
    """
    Study schedule represented as week cycles
    """

    __tablename__ = 'cycle'

    study_id = Column(Integer, nullable=False)

    study = relationship(
        Study,
        backref=backref(
            name='cycles',
            lazy='dynamic',
            cascade='all, delete-orphan'))

    week = Column(Integer, doc='Week number')

    # future-proof field for exempting cycles
    threshold = Column(
        Integer,
        doc='The outer limit, in days, that this cycle may follow the '
            'previous schema before it is skipped as a missed visit.')

    # visits is backref'ed in the Visit class

    category_id = Column(Integer)

    category = relationship(
        Category,
        single_parent=True,
        cascade='all,delete-orphan')

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['study_id'],
                refcolumns=['study.id'],
                name='fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['category_id'],
                refcolumns=[Category.id],
                name='fk_%s_category_id' % cls.__tablename__,
                ondelete='SET NULL'),

            Index('ix_%s_study_id' % cls.__tablename__, 'study_id'),

            # One category per table
            UniqueConstraint(
                'category_id',
                name='uq_%s_category_id' %
                cls.__tablename__),

            # Names and weeks are unique within a cycle
            UniqueConstraint(
                'study_id',
                'name',
                name='uq_%s_name' %
                cls.__tablename__),
            UniqueConstraint(
                'study_id',
                'week',
                name='uq_%s_week' %
                cls.__tablename__))


class Site(Base,  Referenceable, Describeable, Modifiable, Auditable):
    """
    A facility within an organization
    """

    __tablename__ = 'site'

    # patients is backref'ed in the Patient class

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),)


class Patient(Base, Referenceable, Modifiable, HasEntities, Auditable):

    __tablename__ = 'patient'

    # Read-only OUR# alias that will be useful for traversal
    name = hybrid_property(lambda self: self.our)

    title = hybrid_property(lambda self: self.our)

    site_id = Column(Integer, nullable=False)

    site = relationship(
        Site,
        backref=backref(
            name='patients',
            cascade='all, delete-orphan',
            lazy=u'dynamic'),
        doc='The facility that the patient is visiting')

    # This is the old way and should be renamed to PID to make it
    # applicable to other organizations.
    # In the future we should have PID generators
    our = Column(
        Unicode,
        nullable=False,
        doc='Patient identification number.')

    pid = hybrid_property(
        lambda self: self.our,
        lambda self, value: setattr(self, 'our', value))

    # A secondary reference, to help people verify they are viewing the
    # correct patient
    initials = Column(Unicode)

    legacy_number = Column(Unicode)

    nurse = Column(Unicode)

    # partners is backref'ed in the Partner class

    # enrollments is backref'ed in the Enrollment class

    # visits is backref'ed in the Visit class

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['site_id'],
                refcolumns=['site.id'],
                name='fk_%s_site_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('our', name='uq_%s_our' % cls.__tablename__),
            # Ideally this should be unique, but due to inevitably legacy
            # issues with ANYTHING, we'll just keep this indexed.
            Index('ix_%s_legacy_number' % cls.__tablename__, 'legacy_number'),
            Index('ix_%s_site_id' % cls.__tablename__, 'site_id'),
            Index('ix_%s_initials' % cls.__tablename__, 'initials'))


class RefType(Base, Referenceable, Describeable, Modifiable):
    """
    Reference type sources
    """

    __tablename__ = 'reftype'

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),)


class PatientReference(Base, Referenceable, Modifiable, Auditable):
    """
    References to a clinical subject from other sources
    """

    __tablename__ = 'patientreference'

    patient_id = Column(Integer, nullable=False)

    patient = relationship(
        Patient,
        backref=backref(
            name='reference_numbers',
            cascade='all, delete-orphan'),
        primaryjoin=(patient_id == Patient.id))

    reftype_id = Column(Integer, nullable=False,)

    reftype = relationship(
        RefType,
        primaryjoin=(reftype_id == RefType.id))

    reference_number = Column(Unicode, nullable=False,)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['reftype_id'],
                refcolumns=['reftype.id'],
                name='fk_%s_reftype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            Index('ix_%s_reference_number' % cls.__tablename__,
                  'reference_number'),
            UniqueConstraint(
                'patient_id',
                'reftype_id',
                'reference_number',
                name=u'uq_%s_reference'))


class Enrollment(Base,  Referenceable, Modifiable, HasEntities, Auditable):
    """
    A patient's participation in a study.
    """
    __tablename__ = 'enrollment'

    patient_id = Column(Integer, nullable=False,)

    patient = relationship(
        Patient,
        backref=backref(
            name='enrollments',
            cascade='all, delete-orphan',
            lazy='dynamic'))

    study_id = Column(Integer, nullable=False,)

    study = relationship(
        Study,
        backref=backref(
            name='enrollments',
            # The list of enrollments from the study perspective can get quite
            # long, so we implement as query to allow filtering/limit-offset
            lazy='dynamic',
            cascade='all, delete-orphan'))

    # First consent date (i.e. date of enrollment)
    consent_date = Column(Date, nullable=False)

    # Latest consent date
    # Note that some consent dates may be acqured AFTER the patient has
    # terminated
    latest_consent_date = Column(
        Date,
        nullable=False,
        default=lambda c: c.current_parameters['consent_date'])

    # Termination date
    termination_date = Column(Date)

    # A reference specifically for this enrollment (blinded studies, etc)
    reference_number = Column(
        Unicode,
        doc='Identification number within study')

    @property
    def is_consent_overdue(self):
        return (
            self.termination_date is None
            and self.latest_consent_date < self.study.consent_date)

    @property
    def is_termination_overdue(self):
        return (self.termination_date is None
                and self.consent_date + self.study.duration < date.today())

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['study_id'],
                refcolumns=['study.id'],
                name='fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            Index('ix_%s_study_id' % cls.__tablename__, 'study_id'),
            # A patient may enroll only once in the study per day
            UniqueConstraint('patient_id', 'study_id', 'consent_date'),
            Index('ix_%s_reference_number' % cls.__tablename__,
                  'reference_number'))


class Visit(Base, Referenceable, Modifiable, HasEntities, Auditable):

    __tablename__ = 'visit'

    patient_id = Column(Integer, nullable=False)

    patient = relationship(
        Patient,
        backref=backref(
            name='visits',
            cascade='all, delete-orphan',
            lazy='dynamic'))

    cycles = relationship(
        Cycle,
        secondary=visit_cycle_table,
        backref=backref(
            name='visits',
            lazy='dynamic'))

    visit_date = Column(Date, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            Index('ix_%s_patient' % cls.__tablename__, 'patient_id'))


class Arm(Base, Referenceable, Describeable,  Modifiable, Auditable):
    """
    A group of study strata
    """

    __tablename__ = 'arm'

    study_id = Column(Integer, nullable=False)

    study = relationship(
        Study,
        backref=backref(
            name='arms',
            cascade='all,delete-orphan'),
        doc='The study theis pool belongs to')

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=[cls.study_id],
                refcolumns=[Study.id],
                name=u'fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint(
                'study_id',
                'name',
                name=u'uq_%s_name' %
                cls.__tablename__))


class Stratum(Base, Referenceable, Modifiable, HasEntities, Auditable):
    """
    A possible study enrollment assignement.
    Useful for enrolling randomized patients.
    """

    __tablename__ = 'stratum'

    study_id = Column(Integer, nullable=False)

    study = relationship(
        Study,
        backref=backref(
            name='strata',
            lazy='dynamic',
            cascade='all,delete-orphan'))

    arm_id = Column(Integer, nullable=False)

    arm = relationship(
        Arm,
        backref=backref(
            name='strata',
            lazy='dynamic',
            cascade='all,delete-orphan'))

    label = Column(Unicode)

    block_number = Column(Integer, nullable=False)

    # Rename to randid
    reference_number = Column(
        Unicode,
        nullable=False,
        doc='A pregenerated value assigned to the patient per-study. '
            'This is not a Study ID, this is only for statistician. ')

    randid = hybrid_property(
        lambda self: self.reference_number,
        lambda self, value: setattr(self, 'reference_number', value))

    patient_id = Column(Integer)

    patient = relationship(
        Patient,
        backref=backref(
            name='strata'))

    enrollments = relationship(
        Enrollment,
        viewonly=True,
        primaryjoin=(
            study_id == Enrollment.study_id) & (
            patient_id == Enrollment.patient_id),
        foreign_keys=[Enrollment.study_id, Enrollment.patient_id],
        backref=backref(
            name='stratum',
            uselist=False,
            viewonly=True))

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=[cls.study_id],
                refcolumns=[Study.id],
                name=u'fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=[cls.arm_id],
                refcolumns=[Arm.id],
                name=u'fk_%s_arm_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=[cls.patient_id],
                refcolumns=[Patient.id],
                name=u'fk_%s_patient_id' % cls.__tablename__,
                ondelete='SET NULL'),
            UniqueConstraint(
                cls.study_id, cls.reference_number,
                name=u'uq_%s_reference_number' % cls.__tablename__),
            UniqueConstraint(
                cls.study_id, cls.patient_id,
                name=u'uq_%s_patient_id' % cls.__tablename__),
            Index('ix_%s_block_number' % cls.__tablename__, cls.block_number),
            Index('ix_%s_patient_id' % cls.__tablename__, cls.block_number),
            Index('ix_%s_arm_id' % cls.__tablename__, cls.arm_id))


class Export(Base, Referenceable, Modifiable, Auditable):
    """
    Metadata about an export, such as file contents and experation date.
    """

    __tablename__ = 'export'

    name = Column(
        Unicode,
        nullable=False,
        default=lambda: u(str(uuid.uuid4())),
        doc='System name, useful for keep track of asynchronous progress')

    owner_user_id = Column(Integer, nullable=False)

    owner_user = relationship(User, foreign_keys=[owner_user_id])

    expand_collections = Column(Boolean, nullable=False, default=False)

    use_choice_labels = Column(Boolean, nullable=False, default=False)

    notify = Column(
        Boolean,
        nullable=False,
        default=False,
        doc='If set, notify the user that the export has completed')

    status = Column(
        Enum('failed', 'pending', 'complete', name='export_status'),
        nullable=False,
        default='pending')

    contents = Column(
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
        export_dir = self.metadata.info['settings']['app.export.dir']
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
        delta = self.metadata.info['settings'].get('app.export.expire')
        if delta:
            return self.modify_date - timedelta(delta)

    @property
    def redis_key(self):
        return self.__tablename__ + ':' + self.name

    def __repr__(self):
        return '<{0}(id={o.id}, owner_user={o.owner_user.key})>'.format(
            self.__module__ + '.' + self.__class__.__name__,
            o=self)

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=[cls.owner_user_id],
                refcolumns=[User.id],
                name=u'fk_%s_owner_user_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint(cls.name, name=u'uq_%s_name' % cls.__tablename__),
            Index('ix_%s_owner_user_id' % cls.__tablename__,
                  cls.owner_user_id))
