""" 
DataStore implementation module and supporting utilities.
"""

from zope.component import adapts
from zope.interface import implements
from zope.interface import classProvides

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import ScopedSession


from avrc.data.store.interfaces import IDataStoreFactory
from avrc.data.store.interfaces import IDataStore
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.storage import EntityManager
from avrc.data.store.storage import ObjectFactory
from avrc.data.store.schema import SchemaManager


class Datastore(object):
    """ 
    For the love of baby jesus, do not use this. 
    """
    implements(IDatastore)


class DataStore(object):
    classProvides(IDataStoreFactory)
    implements(IDataStore)
    adapts(ScopedSession)


    def __init__(self, session):
        self.session = session
        self.storage = EntityManager(session)
        self.schemata = SchemaManager(session)

    @classmethod
    def create(cls, url):
        """ Convenience method for creating instances factory-style
        """
        engine = create_engine(url)
        session = scoped_session(sessionmaker(engine))
        instance = cls(session)
        return instance

    def __str__(self):
        class_ = self.__class__.__name__
        url = self.session.bind.url
        return u'<%(class_)s (\'%(bind)s\')>' % dict(class_=class_, bind=url)


    def spawn(self, *args, **kwargs):
        return ObjectFactory(*args, **kwargs)


    def keys(self, *args, **kwargs):
        return self.storage.keys(*args, **kwargs)


    def lifecycles(self, *args, **kwargs):
        return self.storage.lifecycles(*args, **kwargs)


    def has(self, *args, **kwargs):
        return self.storage.has(*args, **kwargs)


    def purge(self, *args, **kwargs):
        return self.storage.purge(*args, **kwargs)


    def retire(self, *args, **kwargs):
        return self.storage.retire(*args, **kwargs)


    def restore(self, *args, **kwargs):
        return self.storage.restore(*args, **kwargs)


    def get(self, *args, **kwargs):
        return self.storage.get(*args, **kwargs)


    def put(self, *args, **kwargs):
        return self.storage.put(*args, **kwargs)
