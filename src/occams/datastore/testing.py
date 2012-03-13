"""
Application layers
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from occams.datastore import model
from plone.testing import Layer


CONFIG_URL = 'sqlite:///'
CONFIG_ECHO = True


class DataBaseLayer(Layer):
    """
    DataBase application layer for tests.
    """

    def setUp(self):
        """
        Creates the database structures.
        """
        engine = create_engine(CONFIG_URL, echo=CONFIG_ECHO)
        model.Model.metadata.create_all(engine, checkfirst=True)
        factory = sessionmaker(engine, autoflush=False, autocommit=False)
        self['session'] = session = scoped_session(factory)
        model.registerAuditingSession(session)
        model.registerLibarianSession(session)

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


DATABASE_LAYER = DataBaseLayer()
