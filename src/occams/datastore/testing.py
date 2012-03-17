"""
Application layers
"""

import sqlalchemy.orm
import plone.testing

from occams.datastore import model


class DataStoreLayer(plone.testing.Layer):
    """
    DataBase application layer for tests.
    """

    def setUp(self):
        """
        Creates the database structures.
        """
        engine = sqlalchemy.create_engine('sqlite:///', echo=False)
        model.Model.metadata.create_all(engine, checkfirst=True)
        factory = sqlalchemy.orm.sessionmaker(engine, class_=model.DataStoreSession)
        self['session'] = sqlalchemy.orm.scoped_session(factory)

    def tearDown(self):
        """
        Destroys the database structures.
        """
        model.Model.metadata.drop_all(self['session'].bind, checkfirst=True)
        self['session'].close()
        del self['session']

    def testSetUp(self):
        """
        Sets active user for each test
        """
        session = self['session']
        user = model.User(email='bitcore@ucsd.edu')
        session.add(user)
        session.flush()
        model.setActiveUser(user)

    def testTearDown(self):
        """
        Cancels the transaction after each test case method.
        """
        self['session'].rollback()


DATASTORE_LAYER = DataStoreLayer()
