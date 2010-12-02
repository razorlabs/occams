""" Medication and Drug components
"""
import logging

import transaction
from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import implements

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IDrugManager
from avrc.data.store.interfaces import IMedication
from avrc.data.store.interfaces import IMedicationManager
from avrc.data.store import model


log = logging.getLogger(__name__)


class Medication(object):
    """ See `IMedication`
    """
    implements(IMedication)

    dsid = FieldProperty(IMedication['dsid'])
    subject_dsid = FieldProperty(IMedication['subject_dsid'])
    visit_dsid = FieldProperty(IMedication['visit_dsid'])
    drug_code = FieldProperty(IMedication['drug_code'])
    start_date = FieldProperty(IMedication['start_date'])
    stop_date = FieldProperty(IMedication['stop_date'])

    @classmethod
    def from_rslt(cls, rslt):
        obj = Medication()
        obj.dsid = rslt.id
        obj.subject_dsid = rslt.subject.id
        obj.visit_dsid = rslt.visit.id
        obj.drug_code = rslt.drug.code
        obj.start_date = rslt.start_date
        obj.stop_date = rslt.stop_date
        return obj


class DatastoreDrugManager(object):
    """ See `IDrugManager`

        TODO: Needs full implementation...
    """
    adapts(IDatastore)
    implements(IDrugManager)

    def __init__(self, datastore):
        self._datastore = datastore


    def import_(self, drug_list):
        """ Accepts a tuple of (code, dose, status, and name) and adds to
            the database.

            Builds supplementatary table entries if they don't already
            exist (such as status, category and known names)

            Should only be called at installation....

            Will not create duplicates.

            See `IDrugManager.import_`
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        for code, dose, category, status, name in drug_list:
            category_rslt = session.query(model.DrugCategory) \
                .filter_by(value=category) \
                .first()

            if not category_rslt:
                category_rslt = model.DrugCategory()
                category_rslt.value = category
                session.add(category_rslt)

            status_rslt = session.query(model.DrugStatus) \
                .filter_by(value=status) \
                .first()

            if not status_rslt:
                status_rslt = model.DrugStatus()
                status_rslt.value = status
                session.add(status_rslt)

            drug_rslt = session.query(model.Drug) \
                .filter_by(code=code) \
                .first()

            if not drug_rslt:
                drug_rslt = model.Drug()
                drug_rslt.code = code
                drug_rslt.category = category_rslt
                drug_rslt.status = status_rslt
                drug_rslt.dose = dose
                session.add(drug_rslt)

            name_rslt = session.query(model.DrugName) \
                .filter_by(drug=drug_rslt, value=name) \
                .first()

            if not name_rslt:
                name_rslt = model.DrugName()
                name_rslt.value = name
                drug_rslt.names.append(name_rslt)

            transaction.commit()


    def getCodesVocabulary(self):
        """ See `IDrugManager.getCodesVocabulary`
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        term_list = []

        drug_q = session.query(model.Drug) \
            .filter_by(is_active=True)

        for drug_rslt in drug_q.all():
            term_list.append(SimpleTerm(
                value=drug_rslt.code,
                token=drug_rslt.code,
                title=drug_rslt.code + ' - ' + ' / '.join([n.value for n in drug_rslt.names])
                ))

        return SimpleVocabulary(term_list)


    def get(self, key):
        raise NotImplementedError


    def put(self, source):
        raise NotImplementedError


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


class DatastoreMedicationManager(object):
    """ See `IMedicationManager`
    """
    adapts(IDatastore)
    implements(IMedicationManager)

    def __init__(self, datastore):
        self._datastore = datastore


    def listByRecordedVisit(self, visit):
        """
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        medication_q = session.query(model.Medication) \
            .filter_by(is_active=True) \
            .join(model.Medication.visit) \
            .filter_by(zid=visit.zid)

        medication_q = medication_q.order_by(model.Medication.start_date)

        return [Medication.from_rslt(r) for r in medication_q.all()]


    def listBySubject(self, subject):
        """
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        medication_q = session.query(model.Medication) \
            .filter_by(is_active=True) \
            .join(model.Medication.subject) \
            .filter_by(zid=subject.zid)

        medication_q = medication_q.order_by(model.Medication.start_date)

        return [Medication.from_rslt(r) for r in medication_q.all()]


    def get(self, key):
        """ See `IDrugManager.get`
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        result = session.query(model.Medication)\
            .filter_by(id=int(key), is_active=True)\
            .first()

        return result and Medication.from_rslt(result) or None


    def put(self, source):
        """ See `IMedicationManager.put`
        """

        Session = self._datastore.getScopedSession()
        session = Session()

        if source.dsid is not None:
            medication_rslt = session.query(model.Medication) \
                .filter_by(id=source.dsid) \
                .first()
        else:
            drug_rslt = session.query(model.Drug) \
                .filter_by(code=source.drug_code,
                           is_active=True) \
                .first()

            medication_rslt = model.Medication()
            medication_rslt.drug = drug_rslt
            medication_rslt.start_date = source.start_date

            session.add(medication_rslt)

        medication_rslt.stop_date = source.stop_date
        medication_rslt.notes = source.notes

        transaction.commit()

        if not source.dsid:
            source.dsid = medication_rslt.id

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
