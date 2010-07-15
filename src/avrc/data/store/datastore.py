"""
DataStore specific library. This module is in charge of handling the
the DataStore instances through the use of Object events to keep track of
multiple instances accross sites.  
"""

from zope import component
from zope.component import adapter
from zope.interface import implements

from zope.i18nmessageid import MessageFactory

from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent
from zope.lifecycleevent import IObjectRemovedEvent

import sqlalchemy as sa
from sqlalchemy import orm
    
from avrc.data.store import model
from avrc.data.store import interfaces

_ = MessageFactory(__name__)

# -----------------------------------------------------------------------------
# DataStore handles
# -----------------------------------------------------------------------------

class SessionFactory(object):
    """
    @see avrc.data.store.interfaces.ISessionFactory
    """

    implements(interfaces.ISessionFactory)
    
    def __init__(self, 
                 autocommit=False, 
                 autoflush=True, 
                 twophase=False, 
                 binds=None):
        """
        Our ISessionFactory implementation takes an extra parameter which 
        will be the database bindings.
        """
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.twophase = twophase
        self.binds = binds
    
    def __call__(self):
        """
        Creates the Session object and binds it to the appropriate databases.
        """
        Session  = orm.scoped_session(orm.sessionmaker(
            autocommit=self.autocommit,
            autoflush=self.autoflush,
            twophase=self.twophase
            ))
        
        Session.configure(binds=self.binds)
        
        return Session
        

@adapter(interfaces.IDataStore, IObjectAddedEvent)
def handleDataStoreAdded(datastore, event):
    """
    Triggered when a new DataStore instance is added to a container (i.e.
    when it is added to a site.
    
    @param    datastore    the data store object that was added
    @param    event        the event triggered
    """
    
    # Get the expected data connection strings    
    fia_dsn = getattr(datastore, "fia", None)
    pii_dsn = getattr(datastore, "pii", None)
    
    # The IDataStore interface specifies that pii = fia if none is set
    pii_dsn = pii_dsn is None and fia_dsn or pii_dsn
    
    fia_engine = sa.create_engine(fia_dsn, echo=True)
    pii_engine = sa.create_engine(pii_dsn, echo=True)
    
    model.setup_accessible(fia_engine)
    model.setup_internal(pii_engine)

    # Set up the table-to-engine bindings, this will allow the session
    # to handle multiple engines in a session
    binds = {}
    fia_metadata = getattr(model.Accessible, "metadata", None)
    pii_metadata = getattr(model.Internal, "metadata", None)
    fia_tables = getattr(fia_metadata, "sorted_tables")
    pii_tables = getattr(pii_metadata, "sorted_tables")
    binds.update(dict.fromkeys(fia_tables, fia_engine))
    binds.update(dict.fromkeys(pii_tables, pii_engine))

    utility = SessionFactory(autocommit=False, autoflush=True, binds=binds)
    
    # Get the site that added the data store and register the new Session
    sm = component.getSiteManager(datastore)
    sm.registerUtility(utility, provided=interfaces.ISessionFactory)
    
    
@adapter(interfaces.IDataStore, IObjectModifiedEvent)
def handleDataStoreModified(datastore, event):
    """
    Triggered when a new DataStore instance is modified.
    
    @param    datastore    the data store object that was added
    @param    event        the event triggered
    """
    
    # Override the original data store
    handleDataStoreAdded(datastore, event)
    
@adapter(interfaces.IDataStore, IObjectRemovedEvent)
def handleDataStoreRemoved(datastore, event):
    """
    Triggered when a new DataStore instance is removed from a container
    
    @param    datastore    the data store object that was added
    @param    event        the event triggered
    """
    
    # Pretty much, just remove the local utility for the site
    sm = component.getSiteManager(datastore)
    sm.registerUtility(None, provided=interfaces.ISessionFactory)
    