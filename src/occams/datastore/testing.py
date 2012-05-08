"""
Application layers
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
import plone.testing

from occams.datastore import model

# Vendor-specific URIs, note that some tests still use the SQLite URI for
# general proof-of-concept testing (auditing, metadata, batching, etc)

SQLITE_URI = 'sqlite://'

# Use this if you have a testing database setup
PSQL_URI = 'postgresql://localhost/test'

DEFAULT_URI = SQLITE_URI


class OccamsDataStoreLayer(plone.testing.Layer):
    """
    DataBase application layer for tests.

    Important GOTCHA:  if you are plugging into DataStore with additional models,
    make sure that their metadata has been loaded into the ``Model`` declarative
    base, otherwise they wont be available during testing. Rarely will
    this be an issue and will possibly even go unnoticed, unless the client
    application is doing something exotic like deferring the loading of the
    model classes.
    """

    def setUp(self):
        """
        Creates the database structures.
        """
        engine = create_engine(DEFAULT_URI, echo=False)
        model.Model.metadata.drop_all(engine, checkfirst=True)
        model.Model.metadata.create_all(engine, checkfirst=False)
        self['session'] = scoped_session(sessionmaker(
            bind=engine,
            class_=model.DataStoreSession,
            user=lambda: 'bitcore@ucsd.edu'
            ))

    def tearDown(self):
        """
        Destroys the database structures.
        """
        self['session'].close()
        del self['session']

    def testSetUp(self):
        """
        """
        session = self['session']
        user = model.User(key='bitcore@ucsd.edu')
        session.add(user)
        session.flush()
        self['user'] = user

    def testTearDown(self):
        """
        Cancels the transaction after each test case method.
        """
        self['session'].rollback()


OCCAMS_DATASTORE_FIXTURE = OccamsDataStoreLayer()
