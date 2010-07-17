"""
DataStore specific library. This module is in charge of handling the
the DataStore instances through the use of Object events to keep track of
multiple instances across sites.  
"""

from zope import component
from zope.component import adapter
from zope.interface import implements

from zope.i18nmessageid import MessageFactory

from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent
from zope.lifecycleevent import IObjectRemovedEvent


import sqlalchemy as sa
    
from avrc.data.store import model
from avrc.data.store import interfaces
from avrc.data.store import session

_ = MessageFactory(__name__)


class DataStore(object):
    """
    """
    implements(interfaces.IDataStore)
    
    __name__ = __parent__ = None
    
    fia_dsn = u""
    pii_dsn = u""
    
    _pii_engine = None
    _fia_engine = None
    
    store = {}
    
    def __init__(self, fia_dsn, pii_dsn=None):
        """
        """
        self.fia_dsn = fia_dsn
        self.pii_dsn = pii_dsn is None and fia_dsn or pii_dsn
    
    def _setup(self):
        """
        """
        self._fia_engine = sa.create_engine(self.fia_dsn)
        
        if self.fia_dsn == self.pii_dsn:
            self._pii_engine = self._fia_engine
        else:
            self._pii_engine = sa.create_engine(self.pii_dsn)
            
            
        model.setup_fia(self._fia_engine)
        model.setup_pii(self._pii_engine)
    
    
    def _unsetup(self):
        """
        """
    
    def put(self, context, object):
        raise NotImplementedError()
    
    
    def modify(self, context, object):
        raise NotImplementedError()
    
    
    def hide(self, context, object):
        raise NotImplementedError()
    
    
    def remove(self, context, object):
        raise NotImplementedError()
    
    
    def getProtocolManager(self):
        raise NotImplementedError() 
        

@adapter(interfaces.IDataStore, IObjectAddedEvent)
def handleDataStoreAdded(datastore, event):
    """
    Triggered when a new DataStore instance is added to a container (i.e.
    when it is added to a site.
    """

    datastore._setup()

    # Set up the table-to-engine bindings, this will allow the session
    # to handle multiple engines in a session
    binds = {}
    fia_metadata = getattr(model.FIA, "metadata", None)
    pii_metadata = getattr(model.PII, "metadata", None)
    fia_tables = getattr(fia_metadata, "sorted_tables")
    pii_tables = getattr(pii_metadata, "sorted_tables")
    binds.update(dict.fromkeys(fia_tables, datastore._fia_engine))
    binds.update(dict.fromkeys(pii_tables, datastore._pii_engine))

    utility = session.SessionFactory(autocommit=False, 
                                     autoflush=True, 
                                     binds=binds)
    
    # Get the site that added the data store and register the new Session
    sm = component.getSiteManager(datastore)
    sm.registerUtility(utility, provided=interfaces.ISessionFactory)
    
    
@adapter(interfaces.IDataStore, IObjectModifiedEvent)
def handleDataStoreModified(datastore, event):
    """
    Triggered when a new DataStore instance is modified.
    """
    
    # Override the original data store
    handleDataStoreAdded(datastore, event)
    
@adapter(interfaces.IDataStore, IObjectRemovedEvent)
def handleDataStoreRemoved(datastore, event):
    """
    Triggered when a new DataStore instance is removed from a container
    """
    
    datastore._unsetup()
    
    # Pretty much, just remove the local utility for the site
    sm = component.getSiteManager(datastore)
    sm.registerUtility(None, provided=interfaces.ISessionFactory)
    