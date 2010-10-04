""" This is where the querying functionality is going to live.
"""
from collections import deque as queue
from zope.component import getUtility
from zope.component import adapts
from zope.interface import implements

from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store import schema
from avrc.data.store.datastore import named_session

class SearchMonkey(object):

    def __init__(self, datastore):
        """
        """
        self._datastore = datastore
        self._query = None

    def query(self, iface, version=None):

        return self

    def filter_by(self, **kw):

        return self


    def by_base(self, offset, length, iface=None):
        """ Find all object in the data store that extend the specified base
            TODO: versioning not supported
        """
        object_list = []

        Session = named_session(self._datastore)
        session = Session()

        version = None
        name = None

        if interfaces.Schema.providedBy(iface):
            version = schema.version(iface)
            name = iface.__name__
        elif isinstance(iface, (str, unicode)):
            name = unicode(iface)

        # First, we need all the specifications that extend the given interface
        spec_ids = []

        spec_rslt = session.query(model.Specification)\
                    .filter_by(name=name)\
                    .first()

        if not spec_rslt:
            return object_list

        to_visit = queue([spec_rslt])

        while to_visit:
            spec_rslt = to_visit.popleft()
            to_visit.extend(spec_rslt.children)
            spec_ids.append(spec_rslt.id)

        instances_rslt = session.query(model.Instance.id)\
                            .join(model.Instance.schema)\
                            .filter(model.Schema.specification_id.in_(spec_ids))\
                            [offset:length]



        return object_list

