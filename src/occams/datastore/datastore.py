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


from occams.datastore.interfaces import IDataStoreFactory
from occams.datastore.interfaces import IDataStore
from occams.datastore.storage import EntityManager
from occams.datastore.storage import ObjectFactory
from occams.datastore.schema import SchemaManager


class DataStore(object):
    classProvides(IDataStoreFactory)
    implements(IDataStore)
    adapts(ScopedSession)

    def __init__(self, session):
        self.session = session
        self.storage = EntityManager(session)
        self.schemata = SchemaManager(session)

        self.keys = self.storage.lifecycles
        self.has = self.storage.has
        self.purge = self.storage.purge
        self.retire = self.storage.purge
        self.restore = self.storage.restore
        self.get = self.storage.get
        self.put = self.storage.put

    @classmethod
    def create(cls, url):
        """
        Convenience method for creating instances factory-style
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
