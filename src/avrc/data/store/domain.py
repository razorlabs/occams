"""
"""
from zope.component import adapts
from zope.component import getUtility
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

from avrc.data.store import interfaces
from avrc.data.store import _model

_ = MessageFactory(__name__)

class Domain(object):
    """
    """
    implements(interfaces.IDomain)
    
    title = None
    
DomainFactory = Factory(
    Domain,
    title=_(u"Create a new domain"),
    description=_("New domain generator")
    )

class EngineDomainManager(object):
    """
    """
    adapts(interfaces.IEngine)
    implements(interfaces.IDomainManager)
    
    def __init__(self, engine):
        self.engine = engine
        
    def get(id):
        """ 
        """
        Session = getUtility(interfaces.ISessionFactory)()
        obj = None
        rslt = Session.query(_model.Domain).filter_by(title=id).first()
        
        if rslt is not None:
            obj = Domain(title=rslt.title)
            
        return obj
    
    def add(self, source):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        Session.add( _model.Domain(title=source.title) )
        Session.commit()
        
    def modify(self, old, new):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        rslt = Session.query(_model.Domain).filter_by(title=old.title).first()
        rslt.title = new.title
        Session.commit()
        
    def expire(self, source):
        """
        """
        raise NotImplementedError()
        
    def remove(self, source):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        rslt = Session.query(_model.Domain).filter_by(title=source.title)
        if rslt is not None:
            Session.remove(rslt)
        Session.commit()
        
    def list(self):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        listing = []
        
        for rslt in Session.query(_model.Domain).all():
            listing.append(Domain(title=rslt.title))
        
        return listing
    
