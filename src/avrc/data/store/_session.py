
from zope.component import adapter
from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectRemovedEvent

from sqlalchemy import orm

from avrc.data.store import interfaces

@adapter(interfaces.IEngine)
def EngineSession(engine):
    """
    Creates the Session object and binds it to the appropriate databases.
    """
    Session  = orm.scoped_session(orm.sessionmaker(
        autocommit=False,
        autoflush=True,
        twophase=False
        ))
    
    Session.configure(binds=engine.binds)
    
    return Session()
        
        
@adapter(interfaces.IEngine, IObjectAddedEvent)
def handleEngineAdded(engine, event):
    """
    Triggered when a new DataStore instance is added to a container (i.e.
    when it is added to a site.
    This method will setup all metadata needed for the engine to fully
    offer it's services.
    """
    engine._setup()
    
@adapter(interfaces.IEngine, IObjectRemovedEvent)
def handleDataStoreRemoved(engine, event):
    """
    Triggered when a new DataStore instance is removed from a container
    """
    engine._unsetup()