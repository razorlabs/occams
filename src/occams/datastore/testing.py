"""
Application layers
"""

from sqlalchemy import create_engine
import plone.testing

from occams.datastore import model
from occams.datastore.model.session import scoped_session

class DataStoreLayer(plone.testing.Layer):
    """
    DataBase application layer for tests.
    """

    def setUp(self):
        """
        Creates the database structures.
        """
        engine = create_engine('sqlite:///', echo=False)
        model.Model.metadata.create_all(engine, checkfirst=True)
        session = scoped_session(bind=engine, user=lambda: 'bitcore@ucsd.edu')
        self['session'] = session

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


DATASTORE_LAYER = DataStoreLayer()
