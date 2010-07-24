"""
"""

import zope.schema
from zope.component import adapts
from zope.component import getUtility
from zope.component.factory import Factory
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.i18nmessageid import MessageFactory

from avrc.data.store import interfaces
from avrc.data.store import _model

_TYPE_MAP = {
    zope.schema.Int: u"integer",
    zope.schema.TextLine: u"string",
    zope.schema.Bytes: u"binary",
    zope.schema.Bool: u"boolean",
    zope.schema.Decimal: u"real",
    zope.schema.Date: u"datetime",
    zope.schema.Object: u"object",
    }

_REVERSE_TYPE_MAP = dict(zip(_TYPE_MAP.values() ,_TYPE_MAP.keys()))

_ = MessageFactory(__name__)

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
            cls = _REVERSE_TYPE_MAP[attribute.field.type.title] 
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
    