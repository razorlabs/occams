""" Medication and Drug components
"""
import logging

import transaction
from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import implements

from sqlalchemy.sql import and_
from sqlalchemy.sql import or_

from avrc.data.store._manager import AbstractDatastoreManager
from avrc.data.store._item import AbstractItem
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IDrugManager
from avrc.data.store.interfaces import IMedication
from avrc.data.store.interfaces import IMedicationManager
from avrc.data.store import model


log = logging.getLogger(__name__)


class Medication(AbstractItem):
    """ See `IMedication`
    """
    implements(IMedication)

    dsid = FieldProperty(IMedication['dsid'])
    subject_zid = FieldProperty(IMedication['subject_zid'])
    drug_code = FieldProperty(IMedication['drug_code'])
    start_date = FieldProperty(IMedication['start_date'])
    stop_date = FieldProperty(IMedication['stop_date'])
    notes = FieldProperty(IMedication['notes'])

    @classmethod
    def from_rslt(cls, rslt):
        obj = Medication()
        obj.dsid = rslt.id
        obj.subject_zid = rslt.subject.zid
        obj.drug_code = rslt.drug.code
        obj.start_date = rslt.start_date
        obj.stop_date = rslt.stop_date
        obj.notes = rslt.notes
        return obj


class DatastoreDrugManager(AbstractDatastoreManager):
    """ See `IDrugManager`

        TODO: Needs full implementation...
    """
    adapts(IDatastore)
    implements(IDrugManager)


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

        code_counter = dict()

        for code, dose, category, status, name in drug_list:
            category_rslt = Session.query(model.DrugCategory) \
                .filter_by(value=category) \
                .first()

            if not category_rslt:
                category_rslt = model.DrugCategory()
                category_rslt.value = category
                Session.add(category_rslt)

            status_rslt = Session.query(model.DrugStatus) \
                .filter_by(value=status) \
                .first()

            if not status_rslt:
                status_rslt = model.DrugStatus()
                status_rslt.value = status
                Session.add(status_rslt)

            drug_rslt = Session.query(model.Drug) \
                .filter_by(code=code) \
                .first()

            if not drug_rslt:
                code_counter[code] = 0

                drug_rslt = model.Drug()
                drug_rslt.code = code
                drug_rslt.category = category_rslt
                drug_rslt.status = status_rslt
                drug_rslt.dose = dose
                Session.add(drug_rslt)

            name_rslt = Session.query(model.DrugName) \
                .filter_by(drug=drug_rslt, value=name) \
                .first()

            if not name_rslt:
                code_counter[code] += 1

                name_rslt = model.DrugName()
                name_rslt.value = name
                name_rslt.order = code_counter[code]
                drug_rslt.names.append(name_rslt)

            transaction.commit()


    def getCodesVocabulary(self):
        """ See `IDrugManager.getCodesVocabulary`
        """
        Session = self._datastore.getScopedSession()

        term_list = []

        drug_q = Session.query(model.Drug) \
            .filter_by(is_active=True) \
            .order_by(model.Drug.code)

        for drug_rslt in drug_q.all():
            term_list.append(SimpleTerm(
                value=drug_rslt.code,
                token=drug_rslt.code,
                title=drug_rslt.code + ' - ' + ' / '.join([n.value for n in drug_rslt.names])
                ))

        return SimpleVocabulary(term_list)


class DatastoreMedicationManager(AbstractDatastoreManager):
    """ See `IMedicationManager`
    """
    adapts(IDatastore)
    implements(IMedicationManager)


    def listByVisit(self, visit, subject):
        """
        """
        Session = self._datastore.getScopedSession()

        medication_q = Session.query(model.Medication) \
            .filter_by(is_active=True) \
            .filter(and_(model.Medication.start_date < visit.visit_date,
                         or_(model.Medication.stop_date == None,
                             model.Medication.stop_date >= visit.visit_date
                             )
                         )
                    ) \
            .join(model.Medication.subject) \
            .filter_by(zid=subject.zid)

        medication_q = medication_q.order_by(model.Medication.start_date)

        return [Medication.from_rslt(r) for r in medication_q.all()]


    def listBySubject(self, subject):
        """
        """
        Session = self._datastore.getScopedSession()

        medication_q = Session.query(model.Medication) \
            .filter_by(is_active=True) \
            .join(model.Medication.subject) \
            .filter_by(zid=subject.zid)

        medication_q = medication_q.order_by(model.Medication.start_date)

        return [Medication.from_rslt(r) for r in medication_q.all()]


    def get(self, key):
        """ See `IDrugManager.get`
        """
        Session = self._datastore.getScopedSession()

        result = Session.query(model.Medication)\
            .filter_by(id=int(key), is_active=True)\
            .first()

        return result and Medication.from_rslt(result) or None


    def put(self, source):
        """ See `IMedicationManager.put`
        """

        Session = self._datastore.getScopedSession()

        if source.dsid is not None:
            medication_rslt = Session.query(model.Medication) \
                .filter_by(id=source.dsid) \
                .first()
        else:
            drug_rslt = Session.query(model.Drug) \
                .filter_by(code=source.drug_code,
                           is_active=True) \
                .first()

            subject_rslt = Session.query(model.Subject) \
                .filter_by(zid=source.subject_zid) \
                .first()

            medication_rslt = model.Medication()
            medication_rslt.subject = subject_rslt
            medication_rslt.drug = drug_rslt
            medication_rslt.start_date = source.start_date

            Session.add(medication_rslt)

        medication_rslt.stop_date = source.stop_date
        medication_rslt.notes = source.notes

        transaction.commit()

        if not source.dsid:
            source.dsid = medication_rslt.id

        return source


    def has(self, key):
        raise NotImplementedError


    def retire(self, source):
        Session = self._datastore.getScopedSession()

        if source.dsid is not None:
            medication_rslt = Session.query(model.Medication) \
                .filter_by(id=source.dsid) \
                .first()

        if not medication_rslt:
            return None

        medication_rslt.is_active = False
        transaction.commit()

        return source
