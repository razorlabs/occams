"""
Contains how to: domain and protocol
"""
from zope.component import adapts
from zope.component import getUtility
from zope.schema.fieldproperty import FieldProperty
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store.datastore import named_session


_ = MessageFactory(__name__)
    
class Subject(object):
    implements(interfaces.ISubject)

    __doc__ = interfaces.ISubject.__doc__

    uid = FieldProperty(interfaces.ISubject["uid"])

    def __init__(self, uid):
        self.uid = uid

SubjectFactory = Factory(
    Subject,
    title=_(u"Create a subject instance"),
    )

from avrc.data.store._utils import DatastoreConventionalManager
class DatastoreSubjectManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.ISubjectManager)

    __doc__ = interfaces.ISubjectManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Subject
        self._type = Subject
        
    def putProperties(self, rslt, source):
        """
        Add the items from the source to ds
        """
        rslt.uid = source.uid 
        
class Enrollment(object):
    implements(interfaces.IEnrollment)

    __doc__ = interfaces.IEnrollment.__doc__

    start_date = FieldProperty(interfaces.IEnrollment["start_date"])

    consent_date = FieldProperty(interfaces.IEnrollment["consent_date"])

    stop_date = FieldProperty(interfaces.IEnrollment["stop_date"])

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
        Session = named_session(self._datastore)
        session = Session()

        rslt = session.query(self._model)\
                      .filter_by(zid=source.zid)\
                      .first()

        domain = session.query(model.Domain)\
                      .filter_by(zid=source.domain_zid)\
                      .first()
        subject =  session.query(model.Subject)\
                      .filter_by(zid = source.subject_zid)\
                      .first()
        if rslt is None:
            rslt = self._model(zid=source.zid, domain=domain, domain_id=domain.id, subject=subject, subject_id=subject.id, start_date=source.start_date, consent_date=source.consent_date)
            session.add(rslt)
        else:
        # won't update the code
            rslt = self.putProperties(rslt, source, session)
        session.commit()

    def putProperties(self, rslt, source):
        """
        Add the items from the source to ds
        """
#        rslt.schemata.append(;lasdkfjas;lfj;saldfja;sldjfsa;ldjf;saldfjsa;fhsa)
        rslt.start_date = source.start_date
        rslt.consent_date = source.consent_date
        rslt.stop_date = source.stop_date

        return rslt


class Visit(object):
    implements(interfaces.IVisit)

    __doc__ = interfaces.IVisit.__doc__

    visit_date = FieldProperty(interfaces.IVisit["visit_date"])

    def __init__(self, visit_date):
        self.visit_date = visit_date
            
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
        """
        Add the items from the source to ds
        """
        rslt.visit_date = source.visit_date
#        rslt.enrollments.extend(source.enrollments)
#        rslt.protocols.extend(source.protocols)



