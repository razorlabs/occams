""" Contains how to: domain and protocol
"""

from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.interface import implements

from avrc.data.store._manager import AbstractEAVContainerManager
from avrc.data.store._item import AbstractItem
from avrc.data.store.interfaces import Schema
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISubject
from avrc.data.store.interfaces import IPartner
from avrc.data.store.interfaces import IEnrollment
from avrc.data.store.interfaces import IVisit
from avrc.data.store.interfaces import IPartnerManager
from avrc.data.store.interfaces import ISubjectManager
from avrc.data.store.interfaces import IEnrollmentManager
from avrc.data.store.interfaces import IVisitManager
from avrc.data.store import model
from avrc.data.store import MessageFactory as _


class Subject(AbstractItem):
    """ See `ISubject`
    """
    implements(ISubject)

    zid = FieldProperty(ISubject['zid'])
    uid = FieldProperty(ISubject['uid'])
    nurse_email = FieldProperty(ISubject['nurse_email'])
    aeh = FieldProperty(ISubject['aeh'])
    our = FieldProperty(ISubject['our'])


class Partner(AbstractItem):
    """ See `IPartner`
    """
    implements(IPartner)

    zid = FieldProperty(IPartner['zid'])
    subject_zid = FieldProperty(IPartner['subject_zid'])
    enrolled_subject_zid = FieldProperty(IPartner['enrolled_subject_zid'])
    visit_date = FieldProperty(IPartner['visit_date'])


class Enrollment(AbstractItem):
    """ See `IEnrollment`
    """
    implements(IEnrollment)

    subject_zid = FieldProperty(IVisit['subject_zid'])
    start_date = FieldProperty(IEnrollment['start_date'])
    consent_date = FieldProperty(IEnrollment['consent_date'])
    stop_date = FieldProperty(IEnrollment['stop_date'])
    eid = FieldProperty(IEnrollment['eid'])


class Visit(AbstractItem):
    """ See `IVisit`
    """
    implements(IVisit)

    zid = FieldProperty(IVisit['zid'])
    subject_zid = FieldProperty(IVisit['subject_zid'])
    protocol_zids = FieldProperty(IVisit['protocol_zids'])
    visit_date = FieldProperty(IVisit['visit_date'])


class DatastoreSubjectManager(AbstractEAVContainerManager):
    adapts(IDatastore)
    implements(ISubjectManager)

    _model = model.Subject
    _type = Subject

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        rslt.zid = source.zid
        rslt.uid = source.uid
        rslt.nurse_email = source.nurse_email
        rslt.aeh = source.aeh
        rslt.our = source.our


class DatastorePartnerManager(AbstractEAVContainerManager):
    """ See `IPartnerManager`
    """
    adapts(IDatastore)
    implements(IPartnerManager)

    _model = model.Partner
    _type = Partner

    def putProperties(self, rslt, source):
        Session = self._datastore.getScopedSession()

        subject = Session.query(model.Subject)\
            .filter_by(zid=source.subject_zid)\
            .first()

        enrolled_subject = Session.query(model.Subject)\
            .filter_by(zid=source.enrolled_subject_zid)\
            .first()

        rslt.zid = source.zid
        rslt.subject = subject
        rslt.enrollment_subject = enrolled_subject
        rslt.visit_date = source.visit_date


class DatastoreEnrollmentManager(AbstractEAVContainerManager):
    adapts(IDatastore)
    implements(IEnrollmentManager)

    _model = model.Enrollment
    _type = Enrollment

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        Session = self._datastore.getScopedSession()

        domain = Session.query(model.Domain)\
                      .filter_by(zid=source.domain_zid)\
                      .first()

        subject =  Session.query(model.Subject)\
                      .filter_by(zid = source.subject_zid)\
                      .first()

        rslt.subject = subject
        rslt.domain = domain
        rslt.start_date = source.start_date
        rslt.consent_date = source.consent_date
        rslt.stop_date = source.stop_date
        rslt.eid = getattr(source, 'eid', None)


    def get_objects_by_eid(self, eid, iface=None):
        """ Utility method for retrieving objects based on the enrollment and
            (optionally) based on when it was collected.
        """
        Session = self._datastore.getScopedSession()

        enrollment = Session.query(model.Enrollment).filter_by(eid=unicode(eid)).first()

        search_q = Session.query(model.Instance.id)\
                .join(model.visit_instance_table)\
                .join(model.Visit)\
                .filter(model.Visit.subject == enrollment.subject)\
                .filter(model.Visit.visit_date >= enrollment.start_date)

        if enrollment.stop_date is not None:
                search_q = search_q\
                    .filter(model.Visit.visit_date <= enrollment.stop_date)

        if iface is not None:
            iface_name = ''
            iface_version = None

            if isinstance(iface, (str, unicode)):
                if len(iface):
                    iface_name = unicode(iface)
                else:
                    raise Exception('Empty schema name specified for search')
            elif iface.extends(Schema):
                iface_name = iface.__name__
                iface_version = iface.__version__
            else:
                raise Exception('Invalid schema for search: %s' % iface)

            search_q = search_q.join(model.Schema)\
                        .join(model.Specification)\
                        .filter(model.Specification.name == iface_name)

            if iface_version:
                exp_q = model.Schema.create_date == iface_version
                search_q = search_q.filter(exp_q)

        rows = search_q.all()

        return [self._datastore.get(row.id) for row in rows]


class DatastoreVisitManager(AbstractEAVContainerManager):
    adapts(IDatastore)
    implements(IVisitManager)

    _model = model.Visit
    _type = Visit

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        Session = self._datastore.getScopedSession()

        subject =  Session.query(model.Subject)\
          .filter_by(zid=source.subject_zid)\
          .first()

        rslt.zid = source.zid
        rslt.subject = subject
        rslt.visit_date = source.visit_date

        for protocol_zid in source.protocol_zids:
            rslt.protocols.append(Session.query(model.Protocol)\
                .filter_by(zid=protocol_zid)\
                .first())
