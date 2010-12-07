""" Symptom components
"""
import logging

import transaction
from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import implements

from sqlalchemy.sql import and_
from sqlalchemy.sql import or_

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISymptom
from avrc.data.store.interfaces import ISymptomManager
from avrc.data.store import model


log = logging.getLogger(__name__)


class Symptom(object):
    """ See `ISymptom`
    """
    implements(ISymptom)

    dsid = FieldProperty(ISymptom['dsid'])
    subject_zid = FieldProperty(ISymptom['subject_zid'])
    type = FieldProperty(ISymptom['type'])
    status = FieldProperty(ISymptom['status'])
    start_date = FieldProperty(ISymptom['start_date'])
    stop_date = FieldProperty(ISymptom['stop_date'])
    notes = FieldProperty(ISymptom['notes'])

    @classmethod
    def from_rslt(cls, rslt):
        obj = Symptom()
        obj.dsid = rslt.id
        obj.subject_zid = rslt.subject.zid
        obj.type = rslt.type.zid
        obj.status = rslt.drug.status
        obj.start_date = rslt.start_date
        obj.stop_date = rslt.stop_date
        obj.notes = rslt.notes
        return obj


class DatastoreSymptomManager(object):
    """ See `ISymptomManager`
    """
    adapts(IDatastore)
    implements(ISymptomManager)

    def __init__(self, datastore):
        self._datastore = datastore


    def importTypes(self, symptom_types):
        """ See `ISymptomManager.importTypes`
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        for name in symptom_types:
            type_rslt = session.query(model.SymptomType) \
                .filter_by(value=name) \
                .first()

            if not type_rslt:
                type_rslt = model.SymptomType()
                type_rslt.value = name
                session.add(type_rslt)

        transaction.commit()


    def importStatuses(self, symptom_statuses):
        """
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        for name in symptom_statuses:
            status_rslt = session.query(model.SymptomStatus) \
                .filter_by(value=name) \
                .first()

            if not status_rslt:
                status_rslt = model.SymptomStatus()
                status_rslt.value = name
                session.add(status_rslt)

        transaction.commit()


    def getTypesVocabulary(self):
        """ See `ISytmptomManager.getTypesVocabulary`
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        symptom_type_q = session.query(model.SymptomType) \
            .filter_by(is_active=True)

        term_list = [t.value for t in symptom_type_q.all()]

        return SimpleVocabulary.fromValues(term_list)


    def getStatusVocabulary(self):
        """
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        symptom_status_q = session.query(model.SymptomStatus) \
            .filter_by(is_active=True)

        term_list = [t.value for t in symptom_status_q.all()]

        return SimpleVocabulary.fromValues(term_list)


    def listByVisit(self, visit, subject):
        """
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        symptom_q = session.query(model.Symptom) \
            .filter_by(is_active=True) \
            .filter(and_(model.Symptom.start_date < visit.visit_date,
                         or_(model.Symptom.stop_date == None,
                             model.Symptom.stop_date >= visit.visit_date
                             )
                         )
                    ) \
            .join(model.Symptom.subject) \
            .filter_by(zid=subject.zid)

        symptom_q = symptom_q.order_by(model.Symptom.start_date)

        return [Symptom.from_rslt(r) for r in symptom_q.all()]


    def listBySubject(self, subject):
        """
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        symptom_q = session.query(model.Symptom) \
            .filter_by(is_active=True) \
            .join(model.Symptom.subject) \
            .filter_by(zid=subject.zid)

        symptom_q = symptom_q.order_by(model.Symptom.start_date)

        return [Symptom.from_rslt(r) for r in symptom_q.all()]



    def get(self, key):
        """ See `IDrugManager.get`
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        result = session.query(model.Symptom)\
            .filter_by(id=int(key), is_active=True)\
            .first()

        return result and Symptom.from_rslt(result) or None


    def put(self, source):
        """ See `ISymptomManager.put`
        """

        Session = self._datastore.getScopedSession()
        session = Session()

        if source.dsid is not None:
            symptom_rslt = session.query(model.Symptom) \
                .filter_by(id=source.dsid) \
                .first()
        else:
            drug_rslt = session.query(model.Drug) \
                .filter_by(code=source.drug_code,
                           is_active=True) \
                .first()

            subject_rslt = session.query(model.Subject) \
                .filter_by(zid=source.subject_zid) \
                .first()

            visit_rslt = session.query(model.Visit) \
                .filter_by(zid=source.visit_zid) \
                .first()

            symptom_rslt = model.Symptom()
            symptom_rslt.subject = subject_rslt
            symptom_rslt.visit = visit_rslt
            symptom_rslt.drug = drug_rslt
            symptom_rslt.start_date = source.start_date

            session.add(symptom_rslt)

        symptom_rslt.stop_date = source.stop_date
        symptom_rslt.notes = source.notes

        transaction.commit()

        if not source.dsid:
            source.dsid = symptom_rslt.id

        return source


    def has(self, key):
        raise NotImplementedError


    def retire(self, source):
        raise NotImplementedError


    def restore(self, key):
        raise NotImplementedError


    def purge(self, source):
        raise NotImplementedError


    def keys(self):
        raise NotImplementedError
