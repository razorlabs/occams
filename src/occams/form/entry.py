"""
Data entry functionality
"""
from five import grok
from zope.interface import implements
import zope.component
from occams.form import interfaces
# from occams.form import traversal
# from zope.interface.common.mapping import IFullMapping
from sqlalchemy.orm import object_session
# from occams.form.traversal import closest
# from sqlalchemy.orm.exc import NoResultFound
# from plone.memoize import ram
import zope.interface
def _entity_context_cache_key(method, self):
    return self.item.id

def _entity_data_cache_key(method, self):
    return self.item.modify_date

# class DataBaseEntryContext(traversal.DataBaseItemContext):
#     """
#     Entity context for traversal. Provides the parts necessary for interacting with
#     avrc.data.store Entities in a traversable manner within the Plone context
#     """
#     implements(interfaces.IDataBaseEntryContext)

#     def __init__(self, item, data=None):
#         self.item = item
#         self.session = object_session(item)
#         self.formschema = item.schema

#         self.id = None
#         self.name = self.__name__ = str(self.formschema.name)
#         title = self.formschema.title

#         self.title = title
#         self.Title = lambda:title
#         self.description = self.formschema.description

#     @ram.cache(_entity_context_cache_key)
#     def patient(self):
#         patientQ = (
#             self.session.query(model.Patient)
#             .filter(model.Patient.entities.any(model.Entity.id== self.item.id))
#             )
#         return patientQ.one()

#     @ram.cache(_entity_context_cache_key)
#     def visit(self):
#         visitQ = (
#             self.session.query(model.Visit)
#             .filter(model.Visit.entities.any(model.Entity.id == self.item.id))
#             )
#         try:
#             ret = visitQ.one()
#         except NoResultFound:
#             ret = None
#         return ret

#     @ram.cache(_entity_context_cache_key)
#     def enrollment(self):
#         enrollmentQ = (
#             self.session.query(model.Enrollment)
#             .filter(model.Enrollment.entities.any(model.Entity.id == self.item.id))
#             )
#         try:
#             ret = enrollmentQ.one()
#         except NoResultFound:
#             ret = None
#         return ret

#     @property
#     def data(self):
#         mapping = getattr(self, '_data', None)
#         if mapping is None:
#             mapping = IFullMapping(self.item)
#             mapping['collect_date'] = self.item.collect_date
#             self._data = mapping
#         return self._data

# class DataBaseAddContext(traversal.DataBaseItemContext):
#     """
#     Entity context for traversal. Provides the parts necessary for interacting with
#     avrc.data.store Entities in a traversable manner within the Plone context
#     """
#     implements(interfaces.IDataBaseAddContext)

#     def __init__(self, formschema, data=None):
#         self.formschema = formschema
#         self.session = object_session(formschema)
#         self.id = None
#         self.name = self.__name__ = str(self.formschema.name)
#         title = self.formschema.title
#         self.title = title
#         self.Title = lambda:title
#         self.description = self.formschema.description
        
#     def closestModel(self):
#         parent = getattr(self, 'getParentNode', None)
#         if parent is None:
#             return None
#         ploneObj = closest(self, interfaces.IClinicalObject)
#         modelQ = (
#             self.session.query(ploneObj.getModel())
#             .filter(ploneObj.getModel().zid == ploneObj.zid)
#             )
#         try:
#             ret = modelQ.one()
#         except NoResultFound:
#             ret = None
#         return ret  

#     def patient(self):
#         parent = getattr(self, 'getParentNode', None)
#         if parent is None:
#             return None
#         patient = closest(self, interfaces.IPatient)
#         modelQ = (
#             self.session.query(patient.getModel())
#             .filter(patient.getModel().zid == patient.zid)
#             )
#         try:
#             ret = modelQ.one()
#         except NoResultFound:
#             ret = None
#         return ret

#     def visit(self):
#         parent = getattr(self, 'getParentNode', None)
#         if parent is None:
#             return None
#         visit = closest(self, interfaces.IVisit)
#         if visit is None:
#             return None
#         modelQ = (
#             self.session.query(visit.getModel())
#             .filter(visit.getModel().zid == visit.zid)
#             )
#         try:
#             ret = modelQ.one()
#         except NoResultFound:
#             ret = None
#         return ret
            
#     def enrollment(self):
#         parent = getattr(self, 'getParentNode', None)
#         if parent is None:
#             return None
#         enrollment = closest(self, interfaces.IEnrollment)
#         if enrollment is None:
#             return None
#         modelQ = (
#             self.session.query(enrollment.getModel())
#             .filter(enrollment.getModel().zid == enrollment.zid)
#             )
#         try:
#             ret = modelQ.one()
#         except NoResultFound:
#             ret = None
#         return ret

#     @property
#     def data(self):
#         return {}

class EntityMovedEvent(zope.component.interfaces.ObjectEvent):
    """Event to notify that entities have been saved.
    """
    implements(interfaces.IEntityMovedEvent)

    def __init__(self, context, object):
        self.context = context
        self.object = object
        self.session = object_session(context)

# @grok.subscribe(zope.interface.Interface, interfaces.IEntityMovedEvent)
# def handleEntityMovedEvent(object, event):
#     """
#     Handles adding the Clinical Object to datastore
#     """
#     ## We can either use the plone objects, or the new entity context. I like the
#     # Entity context better
#     contextQ = (
#         event.session.query(model.Context)
#         .filter(model.Context.entity_id == object.id)
#     )
#     for contextmodel in iter(contextQ):
#         event.session.delete(contextmodel)
#     event.session.flush()

#     event.context.entities.add(object)
#     patient = getattr(event.context, 'patient', None)
#     if patient:
#         patient.entities.add(object)
#     event.session.flush()