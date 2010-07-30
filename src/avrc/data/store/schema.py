"""
Responsible for schemata, attributes, and vocabularies
"""

import datetime

from zope.component import adapts
from zope.component import getUtility
from zope.component import createObject
from zope.component.factory import Factory
from zope.interface import alsoProvides
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.i18nmessageid import MessageFactory

import zope.schema

from sqlalchemy import func

from avrc.data.store import _utils
from avrc.data.store import interfaces
from avrc.data.store import model

_ = MessageFactory(__name__)
    
def SupportedTypesVocabularyFactory(context):
    """
    Generates a list of supported types. This is used for auto-generating
    meta data into the data store once it is added into a site.
    """
    SimpleTerm = zope.schema.vocabulary.SimpleTerm
    return zope.schema.vocabulary.SimpleVocabulary((
        SimpleTerm(zope.schema.Int, "integer", u"Integer"),
        SimpleTerm(zope.schema.TextLine, "string", u"String"),
        SimpleTerm(zope.schema.Text, "text", u"Text"),
        SimpleTerm(zope.schema.Bytes, "binary", u"Binary"),
        SimpleTerm(zope.schema.Bool, "boolean", u"Boolean"),
        SimpleTerm(zope.schema.Decimal, "real", u"Decimal"),
        SimpleTerm(zope.schema.Date, "date", u"Date"),
        SimpleTerm(zope.schema.Datetime, "datetime", u"Datetime"),
        SimpleTerm(zope.schema.Time, "time", u"Time"),
        SimpleTerm(zope.schema.Object, "object", u"Object"),
        ))
        
alsoProvides(SupportedTypesVocabularyFactory, 
             zope.schema.interfaces.IVocabularyFactory)

class VocabularyManager(object):
    """
    """
    implements(interfaces.ISchemaManager)
    
    def __init__(self):
        """
        """
        
    def put(self, source):
        """
        """
        for term in source:
            pass
        
class VocabularySchema(object):
    """
    I don't know what this does yet, just skeching
    """
    adapts(zope.schema.interfaces.IVocabulary)
    implements(interfaces.ISchemaManager)
    
    def __int__(self, vocabulary):
        """
        """
        

class SchemaManager(object):
    """
    """
    implements(interfaces.ISchemaManager)
    
    def __init__(self):
        """
        """
    
    def put(self, source):
        """
        TODO: maybe upgrade an existing one if it's already in the database?
                Can't because we don't know how to to tell if it has changed?
        
        @param source: A ZOPE interface specification 
        """
        Session = getUtility(interfaces.ISessionFactory)()
        
        title = unicode(source.__name__)
        desc = unicode(source.__doc__)
        
        # If we don't already have a specification, we'll start a new schema
        spec_rslt = Session.query(model.Specification)\
                    .filter_by(title=title)\
                    .first()
                    
        if spec_rslt is None:
            spec_rslt = model.Specification(title=title, description=desc)
        
        # Upgrade the specification            
        schema_rslt = model.Schema()
        schema_rslt.specification = spec_rslt
        
        for name, field in zope.schema.getFieldsInOrder(source):
            name = unicode(name)
            attribute_rslt = Session.query(model.Attribute)\
                             .filter_by(name=name)\
                             .join(model.Schema.specification)\
                             .filter_by(title=title)\
                             .first()

            if attribute_rslt is None:
                attribute_rslt = model.Attribute(
                    name=name,
                    title=field.title,
                    description=field.description,
                    is_required=field.required,
                    order=field.order
                    )
            
            type_rslt = Session.query(model.Type)\
                        .filter_by(title=_utils.TYPE_2_STR[field.__class__])\
                        .first()
        
            attribute_rslt.type = type_rslt
            
            schema_rslt.attributes.append(attribute_rslt)
            
        Session.add(schema_rslt)
        Session.commit()
        
    def get(self, key):
        """
        TODO: BROKEN, doesn't do versioning
        @see: avrc.data.store.interfaces.ISchemaManager#getSchema
        """
        title = unicode(key)
        Session = getUtility(interfaces.ISessionFactory)()
    
        schema_rslt = Session.query(model.Schema)\
                      .filter_by(title=title)\
                      .first()
        
        if schema_rslt is None:
            return None
        
        attrs = {}
        
        for attribute_rslt in schema_rslt.attributes:
            cls = _utils.STR_2_TYPE[attribute_rslt.type.title] 
            attrs[attribute_rslt.name] = cls(
                title=attribute_rslt.title,
                description=attribute_rslt.description,
                required=attribute_rslt.is_required
                )
                
        klass = InterfaceClass(
            name=schema_rslt.title,
            __doc__=schema_rslt.description,
            __module__="avrc.data.store._virtual",
            bases=(interfaces.IMutableSchema,),
            attrs=attrs,
            )
                
        return klass
        
    def modify(self, target):
        """
        It isn't very clear how the modification of schemata is going to work.
        That is, how will be know which parts of the schema have been changed?
        """
        raise NotImplementedError()
        
    def expire(self, target):
        """
        """
        raise Exception(u"Expiring of schema is not allowed")
        
    def remove(self, key, hard=False):
        """
        Removes a 
        """
        title = unicode(key)
        Session = getUtility(interfaces.ISessionFactory)()
        
        num_instances = Session.query(model.Instance)\
                        .join(model.Schema.specification)\
                        .filter_by(title=title)\
                        .count()
        
        if num_instances > 0 and not hard:
            raise Exception("There is already data stored for %s" % key)
        
        schema_rslt = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(title=title)\
                      .first()
        
        Session.remove(schema_rslt)
        Session.commit()
        
    def list(self):
        """
        Returns a list of all the existing schemata NAMES only.
        """
        Session = getUtility(interfaces.ISessionFactory)()
        return Session.query(model.Specification.title).all()

        