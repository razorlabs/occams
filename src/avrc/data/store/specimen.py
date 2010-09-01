"""
Contains how to: specimen and aliquot
"""
from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
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

    @classmethod
    def from_rslt(cls, rslt):
        obj = Specimen()
        obj.dsid = rslt.id
        obj.subject_zid = rslt.subject.zid
        obj.protocol_zid = rslt.protocol.zid
        obj.state = rslt.state.value
        obj.date_collected = rslt.collect_date
        obj.time_collected = rslt.collect_time
        obj.specimen_type = rslt.type.value
        obj.destination = rslt.destination.value
        obj.tubes = rslt.tubes
        obj.tube_type = rslt.tube_type.value
        obj.notes = rslt.notes
        return obj

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

        return specimen_rslt and Specimen.from_rslt(specimen_rslt) or None

    def list_by_state(self, state, before_date=None, after_date=None):
        """
        """
        session = self._session
        SpecimenModel = self._model

        sepecimen_q = session.query(SpecimenModel)\
                        .join(SpecimenModel.state)\
                        .filter_by(value=unicode(state))\

        if before_date:
            exp_q = SpecimenModel.collect_date <= before_date
            sepecimen_q = sepecimen_q.filter_by(exp_q)

        if after_date:
            exp_q = SpecimenModel.collect_date >= after_date
            sepecimen_q = sepecimen_q.filter_by(exp_q)

        return [Specimen.from_rslt(r) for r in sepecimen_q.all()]

    def put(self, source):

        session = self._session
        SpecimenModel = self._model

        # Find the 'vocabulary' objects for the database relation
        keywords = ("state", "tube_type", "destination", "specimen_type")
        rslt = {}

        for keyword in keywords:
            value = getattr(source, keyword, None)

            if value:
                rslt[keyword] = session.query(model.SpecimenAliquotTerm)\
                                .filter_by(vocabulary_name=unicode(keyword),
                                           value=unicode(value)
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

    def aliquot(self, key):
        return interfaces.IAliquotManager(self._datastore, self.get(key))

    def keys(self):
        raise NotImplementedError()

    def has(self, key):
        raise NotImplementedError()

    def purge(self, key):
        # easy
        raise NotImplementedError()

    def retire(self, key):
        # easy
        raise NotImplementedError()

    def restore(self, key):
        # easy
        raise NotImplementedError()

class Aliquot(object):
    implements(interfaces.IAliquot)

    __doc__ = interfaces.IAliquot.__doc__

    dsid = FieldProperty(interfaces.IAliquot["dsid"])
    type = FieldProperty(interfaces.IAliquot["type"])
    state = FieldProperty(interfaces.IAliquot["state"])
    volume = FieldProperty(interfaces.IAliquot["volume"])
    cell_amount = FieldProperty(interfaces.IAliquot["cell_amount"])
    store_date = FieldProperty(interfaces.IAliquot["store_date"])
    freezer = FieldProperty(interfaces.IAliquot["freezer"])
    rack = FieldProperty(interfaces.IAliquot["rack"])
    box = FieldProperty(interfaces.IAliquot["box"])
    storage_site = FieldProperty(interfaces.IAliquot["storage_site"])
    thawed_num = FieldProperty(interfaces.IAliquot["thawed_num"])
    analysis_status = FieldProperty(interfaces.IAliquot["analysis_status"])
    sent_date = FieldProperty(interfaces.IAliquot["sent_date"])
    sent_name = FieldProperty(interfaces.IAliquot["sent_name"])
    notes = FieldProperty(interfaces.IAliquot["notes"])
    special_instruction = \
        FieldProperty(interfaces.IAliquot["special_instruction"])

    @classmethod
    def from_rslt(cls, rslt):
        obj = cls()
        obj.dsid = rslt.id
        obj.type = rslt.type.value
        obj.state = rslt.state.value
        obj.volume = rslt.volume
        obj.cell_amount = rslt.cell_amount
        obj.store_date = rslt.store_date
        obj.freezer = rslt.freezer
        obj.rack = rslt.rack
        obj.box = rslt.box
        obj.storage_site = rslt.storage_site.value
        obj.thawed_num = rslt.thawed_num
        obj.analysis_status = rslt.analysis_status.value
        obj.sent_date = rslt.sent_date
        obj.sent_name = rslt.sent_name
        obj.notes = rslt.notes
        obj.special_instruction = \
            rslt.special_instruction.value

        return obj

class DatastoreSpecimenAliquotManager(object):
    """
    A specialized manager for aliquot using the context of a specimen in a
    data store.
    """
    adapts(interfaces.IDatastore, interfaces.ISpecimen)
    implements(interfaces.IAliquotManager)

    def __init__(self, datastore_obj, specimen_obj):
        """
        """
        self._datastore_obj = datastore_obj
        self._specimen_obj = specimen_obj

    def list_by_state(self, state):
        """
        """
        Session = named_session(self._datastore_obj)
        session = Session()

        aliquot_q = session.query(model.Aliquot)\
                    .filter_by(is_active=True)\
                    .join(model.Aliquot.state)\
                    .filter_by(value=unicode(state))\
                    .join(model.Specimen)\
                    .filter(model.Specimen.id == self._specimen_obj.dsid)

        # not doing by date because we already have the specimen we'd like
        # to know more about. (unless aliquot are created at separate times?)
#        if before_date:
#            exp_q = model.Aliquot.collect_date <= before_date
#            aliquot_q = aliquot_q.filter_by(exp_q)
#
#        if after_date:
#            exp_q = model.Aliquot.collect_date >= after_date
#            aliquot_q = aliquot_q.filter_by(exp_q)

        return [Aliquot.from_rslt(r) for r in aliquot_q.all()]

    def list(self):
        Session = named_session(self._datastore_obj)
        session = Session()

        # Find the specimen first and from there get the aliquot results
        # to create objects
        specimen_rslt = session.query(model.Specimen)\
                        .filter_by(id=self._specimen_obj.dsid,
                                   is_active=True)\
                        .first()

        return [Aliquot.from_rslt(r) for r in specimen_rslt.aliquot]

    def get(self, key):
        Session = named_session(self._datastore_obj)
        session = Session()

        aliquot_rslt = session.query(model.Aliquot)\
                        .filter_by(specimen_id=self._specimen_obj.dsid,
                                   is_active=True,
                                   id=int(key))\
                        .first()

        return aliquot_rslt and Aliquot.from_rslt(aliquot_rslt) or None

    def put(self, source):
        Session = named_session(self._datastore_obj)
        session = Session()
        aliquot_obj = source

        # Find the 'vocabulary' objects for the database relation
        keywords = ("state", "analysis_status", "storage_site", "type",
                    "special_instruction")
        rslt = {}

        for keyword in keywords:
            value = getattr(source, keyword, None)

            if value:
                rslt[keyword] = session.query(model.SpecimenAliquotTerm)\
                                .filter_by(vocabulary_name=unicode(keyword),
                                           value=unicode(value)
                                           )\
                                .first()
            else:
                rslt[keyword] = None

        if aliquot_obj.dsid is not None:
            aliquot_rslt = session.query(model.Aliquot)\
                            .filter_by(id=aliquot_obj.dsid)\
                            .first()
        else:
            specimen_rslt = session.query(model.Specimen)\
                            .filter_by(id=self._specimen_obj.dsid)\
                            .first()

            # specimen is not already in the data base, we need to create one
            aliquot_rslt = model.Aliquot(
                specimen_id=self._specimen_obj.dsid,
                type=rslt["type"],
                )

            session.add(specimen_rslt)

        aliquot_rslt.volume = aliquot_obj.volume
        aliquot_rslt.cell_amount = aliquot_obj.cell_amount
        aliquot_rslt.state = rslt["state"]
        aliquot_rslt.store_date = aliquot_obj.storage_date
        aliquot_rslt.freezer = aliquot_obj.freezer
        aliquot_rslt.rack = aliquot_obj.rack
        aliquot_rslt.box = aliquot_obj.box
        aliquot_rslt.storage_site = rslt["storage_site"]
        aliquot_rslt.thawed_num = aliquot_obj.thawed_num
        aliquot_rslt.analysis_status = rslt["analysis_status"]
        aliquot_rslt.sent_date = aliquot_obj.sent_date
        aliquot_rslt.sent_name = aliquot_obj.sent_name
        aliquot_rslt.notes = aliquot_obj.notes
        aliquot_rslt.special_instruction = rslt["special_instrction"]

        transaction.commit()

        if not aliquot_obj.dsid:
            aliquot_obj.dsid = aliquot_rslt.id

        return aliquot_obj

    def keys(self):
        raise NotImplementedError()

    def has(self, key):
        raise NotImplementedError()

    def purge(self, key):
        # easy
        raise NotImplementedError()

    def retire(self, key):
        # easy
        raise NotImplementedError()

    def restore(self, key):
        # easy
        raise NotImplementedError()

#def get_all_aliquot_by_state(datastore_obj,
#                             state,
#                             before_date=None,
#                             after_date=None):
#    """
#    get all the aliquot (regardless of specimen) that are of a current state
#    """
#    Session = named_session(datastore_obj)
#    session = Session()
#
#    obj_list = []
#
#    aliquot_q = session.query(model.Aliquot)\
#                .filter_by(is_active=True)\
#                .join(model.Aliquot.state)\
#                .filter_by(value=unicode(state))\
#                .join(model.Specimen)\
#
#    if before_date:
#        exp_q = model.Specimen.collect_date <= before_date
#        aliquot_q = aliquot_q.filter_by(exp_q)
#
#    if after_date:
#        exp_q = model.Specimen.collect_date >= after_date
#        aliquot_q = aliquot_q.filter_by(exp_q)
#
#    specimen_cache = {}
#
#    specimen_aliquot_lists = {}
#
#    for aliquot_rslt in aliquot_q.all():
#        # slight optimization
#        if aliquot_rslt.specimen.id in specimen_cache:
#            specimen_obj = Specimen.from_rslt(aliquot_rslt.specimen)
#        else:
#            specimen_obj = specimen_cache[aliquot_rslt.specimen.id]
#
#
#
#    # [(v, k) for (k, v) in d.iteritems()]
#    return [Aliquot.from_rslt(r) for r in specimen_rslt.aliquot]
