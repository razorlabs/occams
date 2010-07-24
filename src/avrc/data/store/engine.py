"""
DataStore specific library. This module is in charge of handling the
the DataStore instances through the use of Object events to keep track of
multiple instances across sites.  
"""

from zope.interface import implements
from zope.i18nmessageid import MessageFactory

import sqlalchemy as sa
    
from avrc.data.store import _model
from avrc.data.store import interfaces

_ = MessageFactory(__name__)

class Engine(object):
    """
    """
    implements(interfaces.IEngine)
    
    __name__ = None
    __parent__ = None
    
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
        
    @property
    def binds(self):
        # Set up the table-to-engine bindings, this will allow the session
        # to handle multiple engines in a session
        binds = {}
        binds.update(dict.fromkeys(_model.FIA.metadata.sorted_tables, 
                                   self._fia_engine))
        binds.update(dict.fromkeys(_model.PII.metadata.sorted_tables, 
                                   self._pii_engine))
    
    def _setup(self):
        """
        Performs data base back-end setup.
        """
        self._fia_engine = sa.create_engine(self.fia_dsn)
        
        if self.fia_dsn == self.pii_dsn:
            self._pii_engine = self._fia_engine
        else:
            self._pii_engine = sa.create_engine(self.pii_dsn)
            
            
        _model.setup_fia(self._fia_engine)
        _model.setup_pii(self._pii_engine)
            
    def _unsetup(self):
        """
        Cleans up any data base configurations.
        """
        # Apparently SQLAlchemy doesn't need clean up...
        