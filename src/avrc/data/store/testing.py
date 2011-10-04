""" 
Application layers
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from avrc.data.store import model
from plone.testing import Layer

CONFIG_URL = 'postgresql://test@localhost/eavcr_test'
CONFIG_ECHO = False


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
        self['session'] = scoped_session(factory)

    def tearDown(self):
        """ 
        Destroys the database structures.
        """
        model.Model.metadata.drop_all(self['session'].bind, checkfirst=True)
        self['session'].close()
        del self['session']

    def testSetUp(self):
        self['session'].rollback()

    def testTearDown(self):
        """ 
        Cancels the transaction after each test case method.
        """
        self['session'].rollback()
        
DATABASE_LAYER = DataBaseLayer()