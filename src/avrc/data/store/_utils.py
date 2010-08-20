
from zope.component import adapts
from zope.component import createObject
from zope.component import getUtility
from zope.interface import implements

from avrc.data.store.datastore import named_session
from avrc.data.store.model import *
from avrc.data.store import interfaces

class DatastoreConventionalManager(object):
    """
    """
#    implements(interfaces.IDatastoreConventionalManager)
#    datastore = None
#    _type = None
    
    __doc__ = interfaces.IConventionalManager.__doc__

    def __init__(self, datastore, model, type):
        self._datastore = datastore
        self._model = model
        self._type = type
        
    def has(self, key):
        pass

    has.__doc__ = interfaces.IConventionalManager["has"].__doc__
    
    def queryModel(self, session, source=None, key=None):
        raise NotImplementedError("Subclasses must implement queryModel")

    def putProperties(self, rslt, source):
        raise NotImplementedError("Subclasses must implement putProperties")

    def get(self, key):
        Session = named_session(self._datastore)
        session = Session()

        rslt = session.query(self._model)\
                      .filter_by(zid=key)\
                      .first()
        newObj = createObject(self._type)
        newObj = self.putProperties(newObj, rslt)
        
        return newObj
    
    get.__doc__ = interfaces.IConventionalManager["get"].__doc__

    def put(self, source):
        Session = named_session(self._datastore)
        session = Session()

        rslt = session.query(self._model)\
                      .filter_by(zid=source.zid)\
                      .first()

        if rslt is None:
            rslt = self._model(zid=source.zid)
            session.add(rslt)

        # won't update the code
        rslt = self.putProperties(rslt, source)
        session.commit()

    put.__doc__ = interfaces.IConventionalManager["put"].__doc__

    def retire(self, source):
        pass

    retire.__doc__ = interfaces.IConventionalManager["retire"].__doc__

    def restore(self, key):
        pass

    restore.__doc__ = interfaces.IConventionalManager["restore"].__doc__

    def purge(self, source):
        Session = getUtility(interfaces.ISessionFactory)
        session = Session()
        rslt = session.query(self._model)\
                      .filter_by(zid=source.zid)\
                      .first()
        
        if rslt is not None:
            session.remove(rslt)
        session.commit()

    purge.__doc__ = interfaces.IConventionalManager["purge"].__doc__

    def keys(self):
        listing = []
        Session = getUtility(interfaces.ISessionFactory)()

        for rslt in Session.query(self._model).all():
            newObj = createObject(self._type)
            newObj = self.putProperties(newObj, rslt)
            listing.append(newObj)
            
        return listing

    keys.__doc__ = interfaces.IConventionalManager["keys"].__doc__