
from zope.component import adapts
from zope.interface import implements

from avrc.data.store import interfaces

class DatastoreProtocol(object):
    adapts(interfaces.IDataStore)
    implements(interfaces.IProtocol)
    
    def __init__(self, datastore):
        self.datastore = datastore
        
        
class ProtocolManager(object):
    implements(interfaces.IProtocolManager)