"""
"""
from zope.component import adapts
from zope.interface import implements

from avrc.data.store import interfaces
from avrc.data.store import _model

class Domain(object):
    """
    """
    implements(interfaces.IDomain)

class EngineDomainManager(object):
    """
    """
    adapts(interfaces.IEngine)
    implements(interfaces.IDomainManager)
    
    def __init__(self, engine):
        self.engine = engine
        
    def add(self, title):
        """
        """
        title=unicode(title)
        Session = interfaces.ISession(self)
        Session.add( _model.Domain(title=title) )
        
    def delete(self, title):
        """
        """
        title=unicode(title)
        Session = interfaces.ISession(self)
        rslt = Session.query(_model.Domain).filter_by(title=title)
        if rslt is not None:
            Session.remove(rslt)
        
    def list(self):
        """
        """
        listing = []
        Session = interfaces.ISession(self)
        
        for domainrslt in Session.query(_model.Domain).all():
            domainobj = Domain()
            
            for prop in domainrslt.context.compiled.statement.columns:
                setattr(domainobj, prop, getattr(domainrslt, prop, None))
            
            listing.append(domainobj)
        
        return listing
    
