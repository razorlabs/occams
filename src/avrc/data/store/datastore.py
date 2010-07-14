
"""
Data Manipulation Library
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
    """

    implements(interfaces.ISessionFactory)
    
    def __init__(self, autocommit=True, autoflush=True, twophase=False):
        """
        """
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.twophase = twophase
    
    def __call__(self):
        """
        """
        Session  = orm.scoped_session(orm.sessionmaker(
            autocommit=self.autocommit,
            autoflush=self.autoflush,
            twophase=self.twophase
            ))
        
        return Session
        

@adapter(interfaces.IDataStore, IObjectAddedEvent)
def handleDataStoreAdded(datastore, event):
    """
    Triggered when a new DataStore instance is added to a container
    """
    
    # Get the expected data connection strings    
    fia_dsn = getattr(datastore, "fia", None)
    pii_dsn = getattr(datastore, "pii", None)
    
    fia_engine = sa.create_engine(fia_dsn, echo=True)
    pii_engine = sa.create_engine(pii_dsn, echo=True)
    
    model.setup_internal(pii_engine)
    model.setup_accessible(fia_engine)

    utility = SessionFactory(
        autocommit=False,
        autoflush=True,
        )
    
    sm = component.getSiteManager(datastore)
    
    sm.registerUtility(utility, provided=interfaces.ISessionFactory)
    
    
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
    
