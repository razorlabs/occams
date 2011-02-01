""" Contains how to: domain and protocol
"""
import transaction

from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.component.factory import Factory
from zope.interface import implements

from avrc.data.store._utils import DatastoreConventionalManager
from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store import MessageFactory as _

class Subject(object):
    implements(interfaces.ISubject)

    __doc__ = interfaces.ISubject.__doc__

    zid = FieldProperty(interfaces.ISubject["zid"])
    uid = FieldProperty(interfaces.ISubject["uid"])
    nurse_email = FieldProperty(interfaces.ISubject["nurse_email"])
    aeh = FieldProperty(interfaces.ISubject["aeh"])

    def __init__(self, zid, uid, aeh=None):
        self.zid = zid
        self.uid = uid
        self.aeh = aeh

SubjectFactory = Factory(
    Subject,
    title=_(u"Create a subject instance"),
    )

class DatastoreSubjectManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.ISubjectManager)

    __doc__ = interfaces.ISubjectManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Subject
        self._type = Subject

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        rslt.zid = source.zid
        rslt.uid = source.uid
        rslt.nurse_email = source.nurse_email
        rslt.aeh = source.aeh

    def getEnteredDataOfType(self, subject, type):
        """ Get all of the data entered for a visit """
        Session = self._datastore.getScopedSession()
        session = Session()
        instance_rslt = session.query(model.Instance)\
                                      .join(self._model.instances)\
                                      .filter(self._model.zid==subject.zid)\
                                      .join(model.Schema)\
                                      .join(model.Specification)\
                                      .filter_by(name=type)\
                                      .first()
        if not instance_rslt:
            return None
        return self._datastore.get(instance_rslt.title)



    def add_instances(self, subject, obj_or_list):
        """ ??!? """
        Session = self._datastore.getScopedSession()
        session = Session()
        subject_rslt = session.query(self._model)\
                                  .filter_by(zid=subject.zid)\
                                  .first()

        for obj in obj_or_list:
            obj_rslt = session.query(model.Instance)\
                                    .filter_by(title=obj.title)\
                                    .first()
            subject_rslt.instances.append(obj_rslt)

        transaction.commit()

class Enrollment(object):
    implements(interfaces.IEnrollment)

    __doc__ = interfaces.IEnrollment.__doc__

    start_date = FieldProperty(interfaces.IEnrollment["start_date"])

    consent_date = FieldProperty(interfaces.IEnrollment["consent_date"])

    stop_date = FieldProperty(interfaces.IEnrollment["stop_date"])

    eid = FieldProperty(interfaces.IEnrollment["eid"])

    def __init__(self, start_date, consent_date=None):
        self.start_date = start_date
        if consent_date is None:
            consent_date = start_date
        self.consent_date = consent_date

EnrollmentFactory = Factory(
    Enrollment,
    title=_(u"Create a enrollment instance"),
    )

class DatastoreEnrollmentManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IEnrollmentManager)

    __doc__ = interfaces.IEnrollmentManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Enrollment
        self._type = Enrollment


    def put(self, source):
        Session = self._datastore.getScopedSession()
        session = Session()
        rslt = session.query(self._model)\
                      .filter_by(zid=source.zid)\
                      .first()
        if rslt is None:
            domain = session.query(model.Domain)\
                          .filter_by(zid=source.domain_zid)\
                          .first()
            subject =  session.query(model.Subject)\
                          .filter_by(zid = source.subject_zid)\
                          .first()
            rslt = self._model(
                zid=source.zid,
                domain=domain,
                domain_id=domain.id,
                subject=subject,
                subject_id=subject.id,
                start_date=source.start_date,
                consent_date=source.consent_date
                )

            if hasattr(source, 'eid') and source.eid is not None:
                rslt.eid = source.eid

            session.add(rslt)
        else:
        # won't update the code
            rslt = self.putProperties(rslt, source)
        transaction.commit()
        return source

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """

        rslt.start_date = source.start_date
        rslt.consent_date = source.consent_date
        rslt.stop_date = source.stop_date
        if hasattr(source, 'eid') and source.eid is not None:
            rslt.eid = source.eid
        return rslt

    def get_objects_by_eid(self, eid, iface=None):
        """ Utility method for retrieving objects based on the enrollment and
            (optionally) based on when it was collected.
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        search_q = session.query(model.Instance.id)\
                .join(model.visit_instance_table)\
                .join(model.Visit)\
                .join(model.Visit.enrollments)\
                .filter_by(eid=unicode(eid))\

        if iface is not None:
            iface_name = ""
            iface_version = None

            if isinstance(iface, (str, unicode)):
                if len(iface):
                    iface_name = unicode(iface)
                else:
                    raise Exception("Empty schema name specified for search")
            elif iface.extends(interfaces.Schema):
                iface_name = iface.__name__
                iface_version = iface.__version__
            else:
                raise Exception("Invalid schema for search: %s" % iface)

            search_q = search_q.join(model.Schema)\
                        .join(model.Specification)\
                        .filter(model.Specification.name == iface_name)

            if iface_version:
                exp_q = model.Schema.create_date == iface_version
                search_q = search_q.filter(exp_q)

        rows = search_q.all()

        return [self._datastore.get(row.id) for row in rows]

    def getEnteredDataOfType(self, enrollment, type):
        """ Get all of the data entered for a visit """
        Session = self._datastore.getScopedSession()
        session = Session()
        instance_rslt = session.query(model.Instance)\
                                      .join(self._model.instances)\
                                      .filter(self._model.zid==enrollment.zid)\
                                      .join(model.Schema)\
                                      .join(model.Specification)\
                                      .filter_by(name=type)\
                                      .first()
        if not instance_rslt:
            return None
        return self._datastore.get(instance_rslt.title)


    def add_instances(self, enrollment, obj_or_list):
        """ ??!? """
        Session = self._datastore.getScopedSession()
        session = Session()
        enrollment_rslt = session.query(self._model)\
                                  .filter_by(zid=enrollment.zid)\
                                  .first()

        for obj in obj_or_list:
            obj_rslt = session.query(model.Instance)\
                                    .filter_by(title=obj.title)\
                                    .first()
            enrollment_rslt.instances.append(obj_rslt)

        transaction.commit()


class Visit(object):
    implements(interfaces.IVisit)

    __doc__ = interfaces.IVisit.__doc__

    zid = FieldProperty(interfaces.IVisit["zid"])

    enrollment_zids = FieldProperty(interfaces.IVisit["enrollment_zids"])

    protocol_zids = FieldProperty(interfaces.IVisit["protocol_zids"])

    visit_date = FieldProperty(interfaces.IVisit["visit_date"])

VisitFactory = Factory(
    Visit,
    title=_(u"Create a visit instance"),
    )

class DatastoreVisitManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IVisitManager)

    __doc__ = interfaces.IVisitManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Visit
        self._type = Visit


    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        Session = self._datastore.getScopedSession()
        session = Session()
        rslt.visit_date = source.visit_date
        for enrollment_zid in source.enrollment_zids:
            rslt.enrollments.append(session.query(model.Enrollment)\
                      .filter_by(zid=enrollment_zid)\
                      .first())

        for protocol_zid in source.protocol_zids:
            rslt.protocols.append(session.query(model.Protocol)\
                      .filter_by(zid=protocol_zid)\
                      .first())

    def getEnteredData(self, visit):
        """ Get all of the data entered for a visit """
        Session = self._datastore.getScopedSession()
        session = Session()
        instances_rslt = session.query(model.Instance)\
                                      .join(self._model.instances)\
                                      .filter(self._model.zid==visit.zid)\
                                      .all()
        if not instances_rslt:
            return []

        objects = []
        for instance_rslt in instances_rslt:
            objects.append(self._datastore.get(instance_rslt.title))
        return objects

    def getEnteredDataOfType(self, visit, type):
        """ Get all of the data entered for a visit """
        Session = self._datastore.getScopedSession()
        session = Session()
        instance_rslt = session.query(model.Instance)\
                                      .join(self._model.instances)\
                                      .filter(self._model.zid==visit.zid)\
                                      .join(model.Schema)\
                                      .join(model.Specification)\
                                      .filter_by(name=type)\
                                      .first()
        if not instance_rslt:
            return None
        return self._datastore.get(instance_rslt.title)

    def add_instances(self, visit, obj_or_list):
        """ ??!? """
        Session = self._datastore.getScopedSession()
        session = Session()
        visit_rslt = session.query(self._model)\
                                  .filter_by(zid=visit.zid)\
                                  .first()

        for obj in obj_or_list:
            obj_rslt = session.query(model.Instance)\
                                    .filter_by(title=obj.title)\
                                    .first()
            visit_rslt.instances.append(obj_rslt)

        transaction.commit()

class Protocol(object):
    implements(interfaces.IProtocol)

    zid = FieldProperty(interfaces.IProtocol['zid'])
    cycle = FieldProperty(interfaces.IProtocol['cycle'])
    domain_zid = FieldProperty(interfaces.IProtocol['domain_zid'])
    threshold = FieldProperty(interfaces.IProtocol['threshold'])
    is_active = FieldProperty(interfaces.IProtocol['is_active'])

class Domain(object):
    implements(interfaces.IDomain)

    zid = FieldProperty(interfaces.IDomain['zid'])
    code = FieldProperty(interfaces.IDomain['code'])
    title = FieldProperty(interfaces.IDomain['title'])
    consent_date = FieldProperty(interfaces.IDomain['consent_date'])
