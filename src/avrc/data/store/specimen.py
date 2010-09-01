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

import transaction

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
        specimen_obj.dsid = specimen_rslt.id
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
            specimen_rslt = session.query(SpecimenModel)\
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

        specimen_rslt.destination = rslt["destination"]
        specimen_rslt.state = rslt["state"]
        specimen_rslt.collect_date = source.date_collected
        specimen_rslt.collect_time = source.time_collected
        specimen_rslt.tubes = source.tubes
        specimen_rslt.tube_type = rslt["tube_type"]
        specimen_rslt.notes = source.notes

        transaction.commit()

        if not source.dsid:
            source.dsid = specimen_rslt.id

        return source

