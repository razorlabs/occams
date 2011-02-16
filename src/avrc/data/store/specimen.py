""" Contains how to: specimen and aliquot
"""
import transaction

from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import implements

from avrc.data.store._manager import AbstractDatastoreConventionalManager
from avrc.data.store._item import AbstractItem
from avrc.data.store import interfaces
from avrc.data.store import model

class Specimen(AbstractItem):
    """ See `ISpecimen`
    """
    implements(interfaces.ISpecimen)


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


class Aliquot(object):
    """ See `IAliquot`
    """
    implements(interfaces.IAliquot)


    dsid = FieldProperty(interfaces.IAliquot["dsid"])
    specimen_dsid = FieldProperty(interfaces.IAliquot["specimen_dsid"])
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
        obj.specimen_dsid = rslt.specimen.id
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
        obj.special_instruction = rslt.special_instruction.value
        return obj


class DatastoreSpecimenManager(AbstractDatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.ISpecimenManager)

    _model = model.Specimen
    _type = Specimen


    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """

    def get(self, key):
        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model

        specimen_rslt = Session.query(SpecimenModel)\
                        .filter_by(id=int(key))\
                        .first()

        return specimen_rslt and Specimen.from_rslt(specimen_rslt) or None

    def get_vocabulary(self, name):
        """ Utility method for retrieving supported vocabulary terms for
            specimen and aliquot attributes.

            Arguments:
                name: (unicode) the name of the vocabulary to fetch
            Returns:
                SimpleVocabulary object
        """
        Session = self._datastore.getScopedSession()

        term_list = []
        term_q = Session.query(model.SpecimenAliquotTerm)\
                  .filter_by(vocabulary_name=name)

        for term_rslt in term_q.all():
            term_list.append(SimpleTerm(
                value=term_rslt.value,
                token=term_rslt.token,
                title=term_rslt.title
                ))

        return SimpleVocabulary(term_list)

    def setupVocabulary(self, vocabularies):
        Session = self._datastore.getScopedSession()

        for vocabulary_name, vocabulary_obj in vocabularies.items():
            for term_obj in vocabulary_obj:
                Session.add(model.SpecimenAliquotTerm(
                    vocabulary_name=unicode(vocabulary_name),
                    title=term_obj.title and unicode(term_obj.title) or None,
                    token=unicode(term_obj.token),
                    value=unicode(term_obj.value)
                    ))

        transaction.commit()

    def list_by_state(self, state, before_date=None, after_date=None):
        """ """
        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model

        specimen_q = Session.query(SpecimenModel)\
                        .join(SpecimenModel.state)\
                        .filter_by(value=unicode(state))

        if before_date:
            exp_q = SpecimenModel.collect_date <= before_date
            specimen_q = specimen_q.filter(exp_q)

        if after_date:
            exp_q = SpecimenModel.collect_date >= after_date
            specimen_q = specimen_q.filter(exp_q)

        specimen_q = specimen_q.order_by(SpecimenModel.id.desc())

        return [Specimen.from_rslt(r) for r in specimen_q.all()]

    def list_specimen_by_group(self,
                               protocol_zid=None,
                               subject_zid=None,
                               state=None,
                               specimen_type=None):
        """ """
        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model
        SubjectModel = model.Subject
        ProtocolModel = model.Protocol
        specimen_q = Session.query(SpecimenModel)

        if state:
            specimen_q = specimen_q\
                        .join(SpecimenModel.state)\
                        .filter_by(value=unicode(state))

        if specimen_type:
            specimen_q = specimen_q\
                        .join(SpecimenModel.type)\
                        .filter_by(value=unicode(specimen_type))

        if protocol_zid:
            specimen_q = specimen_q\
                            .join(ProtocolModel)\
                            .filter(ProtocolModel.zid==protocol_zid)

        if subject_zid:
            specimen_q = specimen_q\
                            .join(SubjectModel)\
                            .filter(SubjectModel.zid==subject_zid)


        specimen_q = specimen_q.order_by(SpecimenModel.id.desc())

        return [Specimen.from_rslt(r) for r in specimen_q.all()]

    def put(self, source):

        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model

        # Find the 'vocabulary' objects for the database relation
        keywords = {"state": u"specimen_state",
                    "tube_type": u"specimen_tube_type",
                    "destination": u"specimen_destination",
                    "specimen_type": u"specimen_type"
                    }

        rslt = {}

        for attr_name, vocab_name in keywords.items():
            value = getattr(source, attr_name, None)

            if value:
                rslt[vocab_name] = Session.query(model.SpecimenAliquotTerm)\
                                .filter_by(vocabulary_name=vocab_name,
                                           value=value
                                           )\
                                .first()
            else:
                rslt[vocab_name] = None

        if source.dsid is not None:
            specimen_rslt = Session.query(SpecimenModel)\
                            .filter_by(id=source.dsid)\
                            .first()
        else:
            # which enrollment we get the subject from.
            subject_rslt = Session.query(model.Subject)\
                            .filter_by(zid=source.subject_zid)\
                            .first()

            protocol_rslt = Session.query(model.Protocol)\
                            .filter_by(zid=source.protocol_zid)\
                            .first()

            # specimen is not already in the data base, we need to create one
            specimen_rslt = SpecimenModel(
                subject=subject_rslt,
                protocol=protocol_rslt,
                type=rslt["specimen_type"],
                )

            Session.add(specimen_rslt)

        specimen_rslt.destination = rslt["specimen_destination"]
        specimen_rslt.state = rslt["specimen_state"]
        specimen_rslt.collect_date = source.date_collected
        specimen_rslt.collect_time = source.time_collected
        specimen_rslt.tubes = source.tubes
        specimen_rslt.tube_type = rslt["specimen_tube_type"]
        specimen_rslt.notes = source.notes

        transaction.commit()

        if not source.dsid:
            source.dsid = specimen_rslt.id

        return source

    def aliquot(self, key):
        return interfaces.IAliquotManager(self._datastore, self.get(key))


class DatastoreAliquotManager(AbstractDatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IAliquotManager)

    __doc__ = interfaces.IAliquotManager.__doc__

    _model = model.Aliquot
    _type = Aliquot


    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """

    def get(self, key):
        Session = self._datastore.getScopedSession()
        AliquotModel = self._model

        aliquot_rslt = Session.query(AliquotModel)\
                        .filter_by(id=int(key))\
                        .first()

        return aliquot_rslt and Aliquot.from_rslt(aliquot_rslt) or None

    def list_by_state(self, state, our_id=None):
        """ """
        Session = self._datastore.getScopedSession()
        AliquotModel = self._model

        aliquot_q = Session.query(AliquotModel)\
                        .join(AliquotModel.state)\
                        .filter_by(value=unicode(state))

        if our_id:
            aliquot_q = aliquot_q\
                            .join(AliquotModel.specimen)\
                            .join(model.Specimen.subject)\
                            .filter_by(uid=our_id)

        aliquot_q = aliquot_q.order_by(AliquotModel.id.desc())

        return [Aliquot.from_rslt(r) for r in aliquot_q.all()]

    def list_aliquot_by_group(self,
                              protocol_zid=None,
                              subject_zid=None,
                              state=None):
        """ """
        Session = self._datastore.getScopedSession()
        AliquotModel = self._model
        SpecimenModel = model.Specimen
        SubjectModel = model.Subject
        ProtocolModel = model.Protocol
        aliquot_q = Session.query(AliquotModel)

        if state:
            aliquot_q = aliquot_q\
                        .join(AliquotModel.state)\
                        .filter_by(value=unicode(state))

        if protocol_zid or subject_zid:

            aliquot_q = aliquot_q\
                            .join(SpecimenModel)

            if protocol_zid:
                aliquot_q = aliquot_q\
                                .join(ProtocolModel)\
                                .filter(ProtocolModel.zid==protocol_zid)

            if subject_zid:
                aliquot_q = aliquot_q\
                                .join(SubjectModel)\
                                .filter(SubjectModel.zid==subject_zid)


        aliquot_q = aliquot_q.order_by(AliquotModel.id.desc())

        return [Aliquot.from_rslt(r) for r in aliquot_q.all()]

    def put(self, source):

        Session = self._datastore.getScopedSession()
        AliquotModel = self._model

        # Find the 'vocabulary' objects for the database relation
        keywords = {"state": u"aliquot_state",
                    "type": u"aliquot_type",
                    "storage_site": u"aliquot_storage_site",
                    "analysis_status": u"aliquot_analysis_status",
                    "special_instruction": u"aliquot_special_instruction",
                    }

        rslt = {}

        for attr_name, vocab_name in keywords.items():

            value = getattr(source, attr_name, None)
            if value:
                rslt[vocab_name] = Session.query(model.SpecimenAliquotTerm)\
                                .filter_by(vocabulary_name=vocab_name,
                                           value=value
                                           )\
                                .first()
            else:
                rslt[vocab_name] = None

        if source.dsid is not None:
            aliquot_rslt = Session.query(AliquotModel)\
                            .filter_by(id=source.dsid)\
                            .first()
        else:
            # which enrollment we get the subject from.
            specimen_rslt = Session.query(model.Specimen)\
                            .filter_by(id=source.specimen_dsid)\
                            .first()

            # specimen is not already in the data base, we need to create one
            aliquot_rslt = AliquotModel(
                specimen=specimen_rslt,
                type=rslt["aliquot_type"],
                )

            Session.add(aliquot_rslt)

        aliquot_rslt.analysis_status =  rslt["aliquot_state"]
        aliquot_rslt.sent_date = source.sent_date
        aliquot_rslt.sent_name = source.sent_name
        aliquot_rslt.special_instruction = rslt["aliquot_special_instruction"]
        aliquot_rslt.storage_site = rslt["aliquot_storage_site"]
        aliquot_rslt.state = rslt["aliquot_state"]
        aliquot_rslt.volume = source.volume
        aliquot_rslt.cell_amount = source.cell_amount
        aliquot_rslt.store_date = source.store_date
        aliquot_rslt.freezer = source.freezer
        aliquot_rslt.rack = source.rack
        aliquot_rslt.box = source.box
        aliquot_rslt.thawed_num = source.thawed_num
        aliquot_rslt.notes = source.notes

        transaction.commit()

        if not source.dsid:
            source.dsid = aliquot_rslt.id
        return source
