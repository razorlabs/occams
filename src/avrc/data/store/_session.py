"""
TODO: This module might have some issue with nested Sessions... this might
need to be fixed on a per request basis. (using scoped_session maybe?)
"""

from zope.interface import implements
from zope.component import adapter
from zope.component import getSiteManager
from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectRemovedEvent

from sqlalchemy import orm

from avrc.data.store import interfaces

class SessionFactory(object):
    """
    @see avrc.data.store.interfaces.ISessionFactory
    """

    implements(interfaces.ISessionFactory)
    
    def __init__(self, 
                 autocommit=False, 
                 autoflush=True, 
                 twophase=False,
                 bind=None, 
                 binds=None):
        """
        Our ISessionFactory implementation takes an extra parameter which 
        will be the database bindings.
        """
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.twophase = twophase
        self.binds = binds
        self.bind = bind
    
    def __call__(self):
        """
        Creates the Session object and binds it to the appropriate databases.
        @see: avrc.data.store.interfaces.ISessionFactory#__call__
        """
        Session  = orm.scoped_session(orm.sessionmaker(
            autocommit=self.autocommit,
            autoflush=self.autoflush,
            twophase=self.twophase
            ))
        
        Session.configure(bind=self.bind, binds=self.binds)
        
        return Session
 
@adapter(interfaces.IEngine, IObjectAddedEvent)
def handleEngineAdded(engine, event):
    """
    Triggered when a new DataStore instance is added to a container (i.e.
    when it is added to a site.
    This method will setup all metadata needed for the engine to fully
    offer it's services.
    """
    engine._setup()
    sm = getSiteManager(engine)
    sm.registerUtility(SessionFactory(binds=engine.binds),  
                       provided=interfaces.ISessionFactory)
    
@adapter(interfaces.IEngine, IObjectRemovedEvent)
def handleEngineRemoved(engine, event):
    """
    Triggered when a new DataStore instance is removed from a container
    """
    engine._unsetup()
    sm = getSiteManager(engine)
    sm.registerUtlity(None, provided=interfaces.ISessionFactory)
    