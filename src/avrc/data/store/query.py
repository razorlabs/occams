"""
This is where the querying functionality is going to live.
"""

from zope.component import getUtility
from zope.component import adapts
from zope.interface import implements

from avrc.data.store import interfaces
from avrc.data.store import model

class DatastoreQuerySearch(object):
    """
    Still not sure how this is going to work
    """
    adapts(interfaces.IDatastore, interfaces.IQuery)

    def __init__(self, datastore, query):
        """
        """
        self._datastore = datastore
        self._query = query

        raise NotImplementedError(u"This library is not yet operational.")


class SearchByID(object):
    """
    """
    implements(interfaces.IQuery)
