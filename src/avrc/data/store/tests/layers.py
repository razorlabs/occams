""" 
Application layers
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from avrc.data.store import model


CONFIG_URL = 'postgresql://test@localhost/eavcr_test'
CONFIG_ECHO = False


class Layer(object):
    """ 
    Base layer for test case layers.
    """


class DataBaseLayer(Layer):
    """ 
    DataBase application layer for tests.
    """

    session = None

    @classmethod
    def setUp(cls):
        """ 
        Creates the database structures.
        """
        engine = create_engine(CONFIG_URL, echo=CONFIG_ECHO)
        model.Model.metadata.create_all(engine, checkfirst=True)
        factory = sessionmaker(engine, autoflush=False, autocommit=False)
        cls.session = scoped_session(factory)


    @classmethod
    def tearDown(cls):
        """ 
        Destroys the database structures.
        """
        model.Model.metadata.drop_all(cls.session.bind, checkfirst=True)
        cls.session.close()
        cls.session = None


    @classmethod
    def testSetUp(cls):
        pass


    @classmethod
    def testTearDown(cls):
        """ 
        Cancels the transaction after each test case method.
        """
        cls.session.rollback()
