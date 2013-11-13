"""
Clinical Models

SQL Database persisted clinical data that will become the heart of this module
as we transition towards a SQL-driven application.
"""

import datetime
import re
import time

from pyramid.threadlocal import get_current_request
from sqlalchemy import orm, schema, sql, types
from sqlalchemy.ext import declarative, hybrid

from occams import roster

# import everything so we can also use DS models from this module
from occams.datastore.model import (
        Auditable,
        AutoNamed, Referenceable, Describeable, Modifiable,
        Category,
        HasEntities,
        ModelClass, DataStoreSession,
        User,
        Schema)


RE_WS = re.compile('\s+')
RE_NON_ASCII = re.compile('[^a-z0-9_-]', re.I)

def get_user():
    # This might be called from a process that is not a request,
    # we need to figure out a way to reliable determine the user...
    request = get_current_request()
    user = getattr(request, 'user', None)
    email = getattr(user, 'email', None)
    return email if email else 'bitcore@ucsd.edu'


Session = orm.scoped_session(orm.sessionmaker(
        user=get_user,
        class_=DataStoreSession))


# roster depends on ZCA, so we have to kindof monkeypatch it...
RosterSession = orm.scoped_session(orm.sessionmaker())
roster.Session = RosterSession

ClinicalModel = ModelClass(u'ClinicalModel')

NOW = sql.text('CURRENT_TIMESTAMP')


def tokenize(value):
    """ Converts the value into a vocabulary token value """
    return RE_NON_ASCII.sub('', RE_WS.sub('-', str(value).strip().lower()))


def serialize(record, deep=False):
    """ Converts a database record to a dictionary """
    # TODO: actually inspect the object and serialize all the values
    # possibly using SQ 0.8 inspect() method
    return dict([(k, record.__dict__[k]) for k in sorted(record.__dict__) if '_sa_' != k[:4]])


def apply(record, data):
    """ Applies a dictionary of values to database record """
    # not allowed to change the id
    data.pop('id')
    map(lambda k: setattr(record, k, data[k]), data.iterkeys())
    return record


visit_cycle_table = schema.Table('visit_cycle', ClinicalModel.metadata,
    schema.Column(
        'visit_id',
        types.Integer,
        schema.ForeignKey('visit.id', name='fk_visit_cycle_visit_id', ondelete='CASCADE',),
        primary_key=True
        ),
    schema.Column(
        'cycle_id',
         types.Integer,
         schema.ForeignKey('cycle.id', name='fk_visit_cycle_cycle_id', ondelete='CASCADE',),
         primary_key=True
         ),
    )

class Zopeable(object):

    zid = schema.Column(types.Integer, nullable=False, unique=True, default=lambda: int(time.time()))


class Study(ClinicalModel, AutoNamed, Referenceable, Describeable,  Auditable, Modifiable, Zopeable):

    short_title = schema.Column(types.Unicode, nullable=False)

    code = schema.Column(types.Unicode, nullable=False)

    consent_date = schema.Column(types.Date, nullable=False)

    is_blinded = schema.Column(types.Boolean)

    @property
    def duration(self):
        Session = orm.object_session(self)
        query = (
            Session.query(Cycle)
            .filter((Cycle.study == self))
            .order_by(
                (Cycle.week != None).desc(), # Nulls last (vendor-agnostic)
                Cycle.week.desc()
                )
            .limit(1)
            )
        try:
            cycle = query.one()
        except orm.exc.NoResultFound:
            # There are no results, so this study has no length
            duration = datetime.timedelta()
        else:
            # No exception thrown, process result
            if cycle.week >= 0:
                duration = datetime.timedelta(cycle.week * 7)
            else:
                # No valid week data, give a lot of time
                duration = datetime.timedelta.max
        return duration

    # cycles is backref'ed in the Cycle class

    # enrollments is backrefed in the Enrollment class

    # TODO: verify why this is nullable if the add event handler sets this anyway
    category_id = schema.Column(types.Integer)

    category = orm.relationship(
        Category,
        single_parent=True,
        cascade='all,delete-orphan',
        primaryjoin=(category_id == Category.id)
        )

    # BBB: nullable because category_id is nullable
    log_category_id = schema.Column(types.Integer)

    log_category = orm.relationship(
        Category,
        single_parent=True,
        cascade='all,delete-orphan',
        primaryjoin=(log_category_id == Category.id)
        )

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['category_id'],
                refcolumns=[Category.id],
                name='fk_%s_category_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),

            schema.ForeignKeyConstraint(
                columns=['log_category_id'],
                refcolumns=[Category.id],
                name='fk_%s_log_category_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),

            # One category per table
            schema.UniqueConstraint('category_id', name='uq_%s_category_id' % cls.__tablename__,),

            schema.UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            schema.Index('ix_%s_code' % cls.__tablename__, 'code'),
            schema.Index('ix_%s_category_id' % cls.__tablename__, 'category_id'),
            schema.Index('ix_%s_log_category_id' % cls.__tablename__, 'log_category_id'),
            )


class Cycle(ClinicalModel, AutoNamed, Referenceable, Describeable,  Auditable, Modifiable, Zopeable):

    study_id = schema.Column(types.Integer, nullable=False)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='cycles',
            lazy='dynamic',
            cascade='all, delete-orphan'))

    # week number
    week = schema.Column(types.Integer)

    # future-proof field for exempting cycles
    threshold = schema.Column(types.Integer)

    # visits is backref'ed in the Visit class

    category_id = schema.Column(types.Integer)

    category = orm.relationship(
        Category,
        single_parent=True,
        cascade='all,delete-orphan',
        )

    @declarative.declared_attr
    def __table_args__(cls):
        return  (
            schema.ForeignKeyConstraint(
                columns=['study_id'],
                refcolumns=['study.id'],
                name='fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.ForeignKeyConstraint(
                columns=['category_id'],
                refcolumns=[Category.id],
                name='fk_%s_category_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),

            schema.Index('ix_%s_study_id' % cls.__tablename__, 'study_id'),

            # One category per table
            schema.UniqueConstraint('category_id', name='uq_%s_category_id' % cls.__tablename__),

            # Names and weeks are unique within a cycle
            schema.UniqueConstraint('study_id', 'name', name='uq_%s_name' % cls.__tablename__),
            schema.UniqueConstraint('study_id', 'week', name='uq_%s_week' % cls.__tablename__),
        )


class Site(ClinicalModel, AutoNamed, Referenceable, Describeable,  Auditable, Modifiable, Zopeable):

    # patients is backref'ed in the Patient class

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            )


class Patient(ClinicalModel, AutoNamed, Referenceable,  Auditable, Modifiable, HasEntities, Zopeable):

    # Read-only OUR# alias that will be useful for traversal
    name = hybrid.hybrid_property(lambda self: self.our)

    title = hybrid.hybrid_property(lambda self: self.our)

    site_id = schema.Column(types.Integer, nullable=False)

    site = orm.relationship(
        Site,
        backref=orm.backref(
            name='patients',
            cascade='all, delete-orphan',
            lazy=u'dynamic',
            )
        )

    our = schema.Column(types.Unicode, nullable=False)

    pid = orm.synonym('our')

    # A secondary reference, to help people verify they are viewing the correct patient
    initials = schema.Column(types.Unicode)

    legacy_number = schema.Column(types.Unicode)

    nurse = schema.Column(types.Unicode)

    # partners is backref'ed in the Partner class

    # enrollments is backref'ed in the Enrollment class

    # visits is backref'ed in the Visit class

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['site_id'],
                refcolumns=['site.id'],
                name='fk_%s_site_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.UniqueConstraint('our', name='uq_%s_our' % cls.__tablename__),
            # Ideally this should be unique, but due to inevitably legacy
            # issues with ANYTHING, we'll just keep this indexed.
            schema.Index('ix_%s_legacy_number' % cls.__tablename__, 'legacy_number'),
            schema.Index('ix_%s_site_id' % cls.__tablename__, 'site_id'),
            schema.Index('ix_%s_initials' % cls.__tablename__, 'initials'),
            )


class RefType(ClinicalModel, AutoNamed, Referenceable, Describeable, Modifiable):

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.UniqueConstraint(u'name', name=u'uq_%s_name' % cls.__tablename__),
        )


class PatientReference(ClinicalModel, AutoNamed, Referenceable, Auditable, Modifiable):

    patient_id = schema.Column(types.Integer, nullable=False,)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='reference_numbers',
            cascade='all, delete-orphan',
            ),
        primaryjoin=(patient_id == Patient.id)
        )

    reftype_id = schema.Column(types.Integer, nullable=False,)

    reftype = orm.relationship(
        RefType,
        primaryjoin=(reftype_id == RefType.id)
        )

    reference_number = schema.Column(types.Unicode, nullable=False,)

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.ForeignKeyConstraint(
                columns=['reftype_id'],
                refcolumns=['reftype.id'],
                name='fk_%s_reftype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            schema.Index('ix_%s_reference_number' % cls.__tablename__, 'reference_number'),
            schema.UniqueConstraint('patient_id', 'reftype_id', 'reference_number', name=u'uq_%s_reference'),
        )


class Enrollment(ClinicalModel, AutoNamed, Referenceable,  Auditable, Modifiable, HasEntities, Zopeable):

    patient_id = schema.Column(types.Integer, nullable=False,)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='enrollments',
            cascade='all, delete-orphan',
            lazy='dynamic'))

    study_id = schema.Column(types.Integer, nullable=False,)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='enrollments',
            # The list of enrollments from the study perspective can get quite long,
            # so we implement as query to allow filtering/limit-offset
            lazy='dynamic',
            cascade='all, delete-orphan',
            ),
        )

    # First consent date (i.e. date of enrollment)
    consent_date = schema.Column(types.Date, nullable=False)

    # Latest consent date
    # Note that some consent dates may be acqured AFTER the patient has terminated
    latest_consent_date = schema.Column(
        types.Date,
        nullable=False,
        default=lambda c: c.current_parameters['consent_date']
        )

    # Termination date
    termination_date = schema.Column(types.Date)

    # A reference specifically for this enrollment (blinded studies, etc)
    reference_number = schema.Column(types.Unicode)

    @property
    def is_consent_overdue(self):
        return (
            self.termination_date is None
            and self.latest_consent_date < self.study.consent_date
            )

    @property
    def is_termination_overdue(self):
        return (
            self.termination_date is None
            and self.consent_date + self.study.duration < datetime.date.today())

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            schema.ForeignKeyConstraint(
                columns=['study_id'],
                refcolumns=['study.id'],
                name='fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE'),
            schema.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            schema.Index('ix_%s_study_id' % cls.__tablename__, 'study_id'),
            # A patient may enroll only once in the study per day
            schema.UniqueConstraint('patient_id', 'study_id', 'consent_date'),
            schema.Index('ix_%s_reference_number' % cls.__tablename__, 'reference_number'),
        )


class Visit(ClinicalModel, AutoNamed, Referenceable,  Auditable, Modifiable, HasEntities, Zopeable):

    patient_id = schema.Column(types.Integer, nullable=False)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='visits',
            cascade='all, delete-orphan',
            lazy='dynamic'))

    cycles = orm.relationship(
        Cycle,
        secondary=visit_cycle_table,
        backref=orm.backref(
            name='visits',
            lazy='dynamic'))

    visit_date = schema.Column(types.Date, nullable=False)

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.Index('ix_%s_patient' % cls.__tablename__, 'patient_id'),
            )


class Arm(ClinicalModel, AutoNamed, Referenceable, Describeable, Auditable, Modifiable):

    study_id = schema.Column(types.Integer, nullable=False)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='arms',
            cascade='all,delete-orphan'))

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=[cls.study_id],
                refcolumns=[Study.id],
                name=u'fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.UniqueConstraint('study_id', 'name', name=u'uq_%s_name' % cls.__tablename__),
            )


class Stratum(ClinicalModel, AutoNamed, Referenceable, Auditable, Modifiable, HasEntities):

    study_id = schema.Column(types.Integer, nullable=False)

    study = orm.relationship(
        Study,
        backref=orm.backref(
            name='strata',
            lazy='dynamic',
            cascade='all,delete-orphan',
            )
        )

    arm_id = schema.Column(types.Integer, nullable=False)

    arm = orm.relationship(
        Arm,
        backref=orm.backref(
            name='strata',
            lazy='dynamic',
            cascade='all,delete-orphan',
            )
        )

    label = schema.Column(types.Unicode)

    block_number = schema.Column(types.Integer, nullable=False)

    reference_number = schema.Column(types.Unicode, nullable=False)

    patient_id = schema.Column(types.Integer)

    patient = orm.relationship(
        Patient,
        backref=orm.backref(
            name='strata',
            )
        )

    enrollments = orm.relationship(
        Enrollment,
        viewonly=True,
        primaryjoin=(study_id == Enrollment.study_id) & (patient_id == Enrollment.patient_id),
        foreign_keys=[Enrollment.study_id, Enrollment.patient_id],
        backref=orm.backref(
            name='stratum',
            uselist=False,
            viewonly=True,
            )
        )

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=[cls.study_id],
                refcolumns=[Study.id],
                name=u'fk_%s_study_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.ForeignKeyConstraint(
                columns=[cls.arm_id],
                refcolumns=[Arm.id],
                name=u'fk_%s_arm_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.ForeignKeyConstraint(
                columns=[cls.patient_id],
                refcolumns=[Patient.id],
                name=u'fk_%s_patient_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            schema.UniqueConstraint(
                cls.study_id, cls.reference_number,
                name=u'uq_%s_reference_number' % cls.__tablename__,
                ),
            schema.UniqueConstraint(
                cls.study_id, cls.patient_id,
                name=u'uq_%s_patient_id' % cls.__tablename__
                ),
            schema.Index('ix_%s_block_number' % cls.__tablename__, cls.block_number),
            schema.Index('ix_%s_patient_id' % cls.__tablename__, cls.block_number),
            schema.Index('ix_%s_arm_id' % cls.__tablename__, cls.arm_id),
            )


export_schema_table = schema.Table('export_schema', ClinicalModel.metadata,
    schema.Column(
        'export_id',
        types.Integer,
        schema.ForeignKey(
            'export.id',
            name='fk_export_schema_export_id',
            ondelete='CASCADE'),
        primary_key=True),
    schema.Column(
        'schema_id',
         types.Integer,
         schema.ForeignKey(
            Schema.id,
            name='fk_export_schema_schema_id',
            ondelete='CASCADE'),
         primary_key=True))


class Export(ClinicalModel, Referenceable, Auditable, Modifiable):
    """
    Metadata about an export, such as file contents and experation date.
    """

    __tablename__ = 'export'

    owner_user_id = schema.Column(types.Integer, nullable=False)

    owner_user = orm.relationship(User, foreign_keys=[owner_user_id])

    expire_date = schema.Column(types.DateTime, nullable=False)

    notify = schema.Column(types.Boolean, nullable=False, default=False)

    status = schema.Column(
        types.Enum('failed', 'pending', 'complete', name='export_status'),
        nullable=False,
        default='pending')

    schemata = orm.relationship(Schema, secondary=export_schema_table)

    @declarative.declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=[cls.owner_user_id],
                refcolumns=[User.id],
                name=u'fk_%s_owner_user_id' % cls.__tablename__,
                ondelete='CASCADE'),
            schema.Index('ix_%s_owner_user_id' % cls.__tablename__, cls.owner_user_id))

