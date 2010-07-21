"""
"""

import zope.schema
from zope.component import adapts
from zope.component import getUtility
from zope.interface import implements
from zope.interface.interface import InterfaceClass

from avrc.data.store import interfaces
from avrc.data.store import model

_TYPE_MAP = {
    zope.schema.Int: u"integer",
    zope.schema.TextLine: u"string",
    zope.schema.Bytes: u"binary",
    zope.schema.Bool: u"boolean",
    zope.schema.Decimal: u"real",
    zope.schema.Date: u"datetime",
    zope.schema.Object: u"object"
    }

_REVERSE_TYPE_MAP = dict(zip(_TYPE_MAP.values() ,_TYPE_MAP.keys()))

class SchemaManager(object):
    """
    """
    implements(interfaces.ISchemaManager)
    
    
    def __init__(self):
        """
        Custom initialization method
        """
    
    def addSchema(self, name):
        """
        @see: avrc.data.store.interfaces.ISchemaManager#add
        """
        raise NotImplementedError()
        
        
    def importSchema(self, source):
        """
        @see: avrc.data.store.interfaces.ISchemaManager#importSchema
        """
        Session = getUtility(interfaces.ISessionFactory)()
        
        schema = model.Schema(
            title=unicode(source.__name__),
            description=unicode(source.__doc__)
            )
        
        Session.add(schema)
        
        for name, type in zope.schema.getFieldsInOrder(source):
            name = unicode(name)
            
            symbol = Session.query(model.Symbol).filter_by(title=name).first()
            
            if symbol is None:
                symbol = model.Symbol(title=name)
            
            attribute = model.Attribute()
            attribute.schema = schema
            attribute.symbol = symbol
            attribute.order = type.order
            attribute.field = model.Field(
                title=type.title,
                description=type.description,
                is_required=type.required,
                )
            
            attribute.field.type = Session.query(model.Type)\
                                   .filter_by(title=_TYPE_MAP[type.__class__])\
                                   .first()
        
            Session.add(attribute)
        
        Session.commit()
        
    def getSchema(self, title):
        """
        @see: avrc.data.store.interfaces.ISchemaManager#getSchema
        """
        title = unicode(title)
        Session = getUtility(interfaces.ISessionFactory)()
    
        schema = Session.query(model.Schema).filter_by(title=title).first()
    
        attributes = Session.query(model.Attribute)\
                      .order_by(model.Attribute.order.asc())\
                      .join(model.Schema)\
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
            __module__="avrc.data.store.schema.generated",
            bases=(interfaces.IMutableSchema,),
            attrs=attrs,
            )
                
        return klass 
        
    

class SubjectData(object):
    """
    """
    implements(interfaces.IMutableSchema)
    adapts(interfaces.ISubject)
    
    
    

class MutableSchema(object):
    """
    """
