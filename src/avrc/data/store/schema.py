"""
Responsible for schemata, attributes, and vocabularies
"""

import zope.schema
from zope.component import adapts
from zope.component import getUtility
from zope.component import createObject
from zope.component.factory import Factory
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.i18nmessageid import MessageFactory
from zope.schema.vocabulary import SimpleVocabulary

from avrc.data.store import _model
from avrc.data.store import interfaces

_ = MessageFactory(__name__)

#
# TODO this really need to be replaced with something much cleaner
#
TYPE_MAP = {
    zope.schema.Int: u"integer",
    zope.schema.TextLine: u"string",
    zope.schema.Bytes: u"binary",
    zope.schema.Bool: u"boolean",
    zope.schema.Decimal: u"real",
    zope.schema.Date: u"datetime",
    zope.schema.Object: u"object",
    }

REVERSE_TYPE_MAP = dict(zip(TYPE_MAP.values() ,TYPE_MAP.keys()))

"""
"""
from zope.component import adapts
from zope.component import getUtility
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

import zope.schema

from avrc.data.store import _model
from avrc.data.store import interfaces

_ = MessageFactory(__name__)

class Attribute(object):
    """
    """
    
    

AttributeFactory = Factory(
    Attribute,
    title=_(u"Creates a attribute"),
    description=_(u"Zah?")
    )

class EngineAttributeManager(object):
    """
    """
    adapts(interfaces.IEngine)
    implements(interfaces.IAttributeManager)
    
    def __init__(self, engine):
        """
        """
        self.engine = engine
        
    def add(self, source):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        
        schema = _model.Schema(
            title=unicode(source.__name__),
            description=unicode(source.__doc__)
            )
        
        Session.add(schema)
        
        for name, type in zope.schema.getFieldsInOrder(source):
            name = unicode(name)
            
            symbol = Session.query(_model.Symbol).filter_by(title=name).first()
            
            if symbol is None:
                symbol = _model.Symbol(title=name)
            
            attribute = _model.Attribute()
            attribute.schema = schema
            attribute.symbol = symbol
            attribute.order = type.order
            attribute.field = _model.Field(
                title=type.title,
                description=type.description,
                is_required=type.required,
                )
            
            attribute.field.type = Session.query(_model.Type)\
                                   .filter_by(title=TYPE_MAP[type.__class__])\
                                   .first()
        
            Session.add(attribute)
        
        Session.commit()
        
    def get(self, id):
        """
        """
        raise NotImplementedError()
        
    def modify(self, target):
        """
        """
        raise NotImplementedError()
        
    def expire(self, target):
        """
        """
        raise NotImplementedError()
        
    def remove(self, target):
        """
        """
        raise NotImplementedError()
        
    def list(self):
        """
        """
        raise NotImplementedError()

class Schema(object):
    pass

SchemaFactory = Factory(
    Schema,
    title=_(u"Creates a schema"),
    description=_(u"Zah?")
    )

class EngineSchemaManager(object):
    """
    Apparently takes a protocol and produces a schema
    """
    adapts(interfaces.IEngine)
    implements(interfaces.ISchemaManager)
    
    def __init__(self, engine):
        self.engine = engine
    
    def add(self, source):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        
        spec_rslt = _model.Specifiation(
            title=source.title,
            description=source.description,
            )
        
        schema_rslt = _model.Schema()
        schema_rslt.specification = spec_rslt
        
        am = interfaces.IAttributeManager(self.engine)
        
        for name, field in zope.schema.getFieldsInOrder(source):
            name = unicode(name)
            attr_obj = createObject("avrc.data.store.Attribtue")
            attr_obj.add(attr_obj)
            attr_obj.get(attr_obj.id)
        
        Session.add(schema_rslt)
        Session.commit()
        
#        schema = _model.Schema(
#            title=unicode(source.__name__),
#            description=unicode(source.__doc__)
#            )
#        
#        Session.add(schema)
#        
#        for name, type in zope.schema.getFieldsInOrder(source):
#            name = unicode(name)
#            
#            symbol = Session.query(_model.Symbol).filter_by(title=name).first()
#            
#            if symbol is None:
#                symbol = _model.Symbol(title=name)
#            
#            attribute = _model.Attribute()
#            attribute.schema = schema
#            attribute.symbol = symbol
#            attribute.order = type.order
#            attribute.field = _model.Field(
#                title=type.title,
#                description=type.description,
#                is_required=type.required,
#                )
#            
#            attribute.field.type = Session.query(_model.Type)\
#                                   .filter_by(title=_TYPE_MAP[type.__class__])\
#                                   .first()
#        
#            Session.add(attribute)
#        
#        Session.commit()

        
    def get(self, id):
        """
        @see: avrc.data.store.interfaces.ISchemaManager#getSchema
        """
        title = unicode(id)
        Session = getUtility(interfaces.ISessionFactory)()
    
        schema = Session.query(_model.Schema).filter_by(title=title).first()
    
        attributes = Session.query(_model.Attribute)\
                      .order_by(_model.Attribute.order.asc())\
                      .join(_model.Schema)\
                      .filter_by(title=title)\
                      .all()
        
        attrs = {}
        
        for attribute in attributes:
            cls = REVERSE_TYPE_MAP[attribute.field.type.title] 
            attrs[attribute.symbol.title] = cls(
                title=attribute.field.title,
                description=attribute.field.description,
                required=attribute.field.is_required
                )
                
        klass = InterfaceClass(
            name=schema.title,
            __doc__=schema.description,
            __module__="avrc.data.store._virtual",
            bases=(interfaces.IMutableSchema,),
            attrs=attrs,
            )
                
        return klass    
        
    def modify(self, target):
        raise NotImplementedError()
        
    def expire(self, target):
        raise NotImplementedError()
        
    def remove(self, target):
        raise NotImplementedError()
        
    def list(self):
        raise NotImplementedError()
    
    


US_STATES_LIST = ["ca", "wa"]

statesVocabulary = SimpleVocabulary.fromValues(US_STATES_LIST)

TYPES = (
    ('binary',),
    ('boolean',),
    ('datetime',),
    ('date'),
    ('time'),
    ('integer',),
    ('real',),
    ('string',),
    ('text',),
    ('object',),
    )
    