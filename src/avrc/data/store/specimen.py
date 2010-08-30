"""
Contains how to: specimen and aliquot
"""
from zope.component import adapts
from zope.component import getUtility
from zope.schema.fieldproperty import FieldProperty
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

from avrc.data.store._utils import DatastoreConventionalManager
from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store.datastore import named_session

_ = MessageFactory(__name__)

class Specimen(object):
    implements(interfaces.ISpecimen)

    __doc__ = interfaces.ISpecimen.__doc__

    dsid = FieldProperty(interfaces.ISpecimen['dsid'])
    subject_zid = FieldProperty(interfaces.ISpecimen['subject_zid'])
    protocol_zid = FieldProperty(interfaces.ISpecimen['protocol_zid'])
    state = FieldProperty(interfaces.ISpecimen['state'])
    date_collected = FieldProperty(interfaces.ISpecimen['date_collected'])
    time_collected = FieldProperty(interfaces.ISpecimen['time_collected'])
    specimen_type = FieldProperty(interfaces.ISpecimen['specimen_type'])
    destination = FieldProperty(interfaces.ISpecimen['destination'])
    tubes = FieldProperty(interfaces.ISpecimen['tubes'])
    tube_type = FieldProperty(interfaces.ISpecimen['tube_type'])
    notes = FieldProperty(interfaces.ISpecimen['notes'])

#    zid = FieldProperty(interfaces.ISubject["zid"])
#
#    def __init__(self, zid, uid):
#        self.zid = zid
#        self.uid = uid

class DatastoreSpecimenManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.ISpecimenManager)

    __doc__ = interfaces.ISpecimenManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Specimen
        self._type = Specimen
        Session = named_session(self._datastore)
        self._session = Session()

    def putProperties(self, rslt, source):
        """
        Add the items from the source to ds
        """
#        rslt.schemata.append(;lasdkfjas;lfj;saldfja;sldjfsa;ldjf;saldfjsa;fhsa)

    def get(self, key):
        session = self._session
        SpecimenModel = self._model
        
        specimen_rslt = session.query(SpecimenModel)\
                        .filter_by(id=int(key))\
                        .first()
        
        if not specimen_rslt:
            return None
        
        specimen_obj = Specimen()
        specimen_obj.dsid = specimen_rslt.dsid
        specimen_obj.subject_zid = specimen_rslt.subject.zid
        specimen_obj.protocol_zid = specimen_rslt.protocol.zid
        specimen_obj.state = specimen_rslt.state.value
        specimen_obj.date_collected = specimen_rslt.collect_date
        specimen_obj.time_collected = specimen_rslt.collect_time
        specimen_obj.specimen_type = specimen_rslt.type.value
        specimen_obj.destination = specimen_rslt.destination.value
        specimen_obj.tubes = specimen_rslt.tubes
        specimen_obj.tube_type = specimen_rslt.tube_type.value
        specimen_obj.notes = specimen_rslt.notes
        return specimen_obj

    def put(self, source):
        session = self._session
        SpecimenModel = self._model
                        
        # Find the 'vocabulary' objects for the database relation
        keywords = ("state", "tube_type", "destination", "specimen_type")
        rslt = {}
        
        for keyword in keywords:
            if hasattr(source, keyword):
                rslt[keyword] = session.query(model.SpecimenAliquotTerm)\
                                .filter_by(vocabulary_name=unicode(keyword),
                                           value=unicode(getattr(source, keyword))
                                           )\
                                .first()
            else:
                rslt[keyword] = None
    
        if source.dsid is not None:
            specimen_rslt = session.query(Specimen)\
                            .filter_by(id=source.dsid)\
                            .first()
        else:
            # which enrollment we get the subject from.
            subject_rslt = session.query(model.Subject)\
                            .filter_by(zid=source.subject_zid)\
                            .first()
    
            protocol_rslt = session.query(model.Protocol)\
                            .filter_by(zid=source.protocol_zid)\
                            .first()
            
            # specimen is not already in the data base, we need to create one
            specimen_rslt = SpecimenModel(
                subject=subject_rslt,
                protocol=protocol_rslt,
                type=rslt["specimen_type"],
                )

            session.add(specimen_rslt)
        
        specimen_rslt.destination = rslt["destination"],
        specimen_rslt.state = rslt["state"]
        specimen_rslt.collect_date = source.date_collected
        specimen_rslt.collect_time = source.time_collected
        specimen_rslt.tubes = source.tubes
        specimen_rslt.tube_type = rslt["tube_type"]
        specimen_rslt.notes = source.notes
        
        session.commit()
        
        if not source.dsid:
            source.dsid = specimen_rslt.id
            
        return source

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

class DatastoreEnrollmentManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IEnrollmentManager)

    __doc__ = interfaces.IEnrollmentManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Enrollment
        self._type = Enrollment
        Session = named_session(self._datastore)
        self._session = Session()


    def put(self, source):

        rslt = self._session.query(self._model)\
                      .filter_by(zid=source.zid)\
                      .first()

        domain = self._session.query(model.Domain)\
                      .filter_by(zid=source.domain_zid)\
                      .first()
        subject =  self._session.query(model.Subject)\
                      .filter_by(zid = source.subject_zid)\
                      .first()
        if rslt is None:
            rslt = self._model(zid=source.zid, domain=domain, domain_id=domain.id, subject=subject, subject_id=subject.id, start_date=source.start_date, consent_date=source.consent_date)
            self._session.add(rslt)
        else:
        # won't update the code
            rslt = self.putProperties(rslt, source)
        self._session.commit()

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

class DatastoreVisitManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IVisitManager)

    __doc__ = interfaces.IVisitManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Visit
        self._type = Visit
        Session = named_session(self._datastore)
        self._session = Session()

    def putProperties(self, rslt, source):
        """
        Add the items from the source to ds
        """
        rslt.visit_date = source.visit_date
        for enrollment_zid in source.enrollment_zids:
            rslt.enrollments.append(self._session.query(model.Enrollment)\
                      .filter_by(zid=enrollment_zid)\
                      .first())

        for protocol_zid in source.protocol_zids:
            rslt.protocols.append(self._session.query(model.Protocol)\
                      .filter_by(zid=protocol_zid)\
                      .first())


    def getEnteredData(self, visit):
        """
        Get all of the data entered for a visit
        """
        instances_rslt = self._session.query(model.Instance)\
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
        """
        Get all of the data entered for a visit
        """
        instance_rslt = self._session.query(model.Instance)\
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
        "??!?"
        visit_rslt = self._session.query(self._model)\
                                  .filter_by(zid=visit.zid)\
                                  .first()

        for obj in obj_or_list:
            obj_rslt = self._session.query(model.Instance)\
                                    .filter_by(title=obj.title)\
                                    .first()
            visit_rslt.instances.append(obj_rslt)

        self._session.commit()

