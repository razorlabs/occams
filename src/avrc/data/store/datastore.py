
"""
Data Manipulation Library
"""

from zope import component
from zope.component import adapter

from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent
from zope.lifecycleevent import IObjectRemovedEvent

from z3c.saconfig import EngineFactory
from z3c.saconfig.interfaces import IScopedSession, IEngineFactory

    
from avrc.data.store import ddl, dml
from avrc.data.store import interfaces

# -----------------------------------------------------------------------------
# DataStore handles
# -----------------------------------------------------------------------------


@adapter(interfaces.IDataStore, IObjectAddedEvent)
def handleDataStoreAdded(datastore, event):
    """
    Triggered when a new DataStore instance is added to a container
    """
    
    # Get the expected data connection strings
    fia_dsn = getattr(datastore, "fia", None)
    pii_dsn = getattr(datastore, "pii", fia_dsn)
    
    fia_engine = EngineFactory(fia_dsn)
    pii_engine = EngineFactory(pii_dsn)
    
    dml.setup_internal(fia_engine())
    dml.setup_accessible(pii_engine())
    
    sm = component.getSiteManager(datastore)
    sm.registerUtility(fia_engine, provided=IEngineFactory)
    sm.registerUtility(pii_engine, provided=IEngineFactory)
    component.provideUtility(None, provides=IEngineFactory)
    
    Session = dml.StoreSiteScopedSession()
    
    binds = {}
    
    fia_metadata = getattr(ddl.Accessible, "metadata", None)
    pii_metadata = getattr(ddl.Internal, "metadata", None)
    
    fia_tables = getattr(fia_metadata, "sorted_tables")
    pii_tables = getattr(pii_metadata, "sorted_tables")
    
    binds.update(dict.fromkeys(fia_tables, fia_engine))
    binds.update(dict.fromkeys(pii_tables, pii_engine))
    
    Session.configure(binds=binds)
    
    component.provideUtility(Session, provides=IScopedSession)
    
    
@adapter(interfaces.IDataStore, IObjectModifiedEvent)
def handleDataStoreModified(datastore, event):
    """
    Triggered when a new DataStore instance is modified
    """
    
@adapter(interfaces.IDataStore, IObjectRemovedEvent)
def handleDataStoreRemoved(datastore, event):
    """
    Triggered when a new DataStore instance is removed from a container
    """
    
    
def DataStoreFactory(context):
    """
    Creates Data Store instances.
    """