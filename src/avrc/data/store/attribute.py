"""
"""
from zope.component import adapts
from zope.component import getUtility
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

from avrc.data.store import _model
from avrc.data.store import interfaces

_ = MessageFactory(__name__)

class Attribute(object):
    pass

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
                                   .filter_by(title=_TYPE_MAP[type.__class__])\
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