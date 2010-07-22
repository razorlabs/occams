import unittest

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store import model

_SA_ECHO = True

class TestCase(unittest.TestCase):
    
    def setUp(self):
        engine = sa.create_engine("sqlite:///:memory:", echo=_SA_ECHO)
        self.Session = orm.scoped_session(orm.sessionmaker())
        self.Session.configure(bind=engine)
        
        model.FIA.metadata.create_all(bind=engine)
        model.PII.metadata.create_all(bind=engine)
        
    def tearDown(self):
        self.Session.remove()

    def test_single_engine(self):
        """
        """
        self.fail("Not done yet")
    
    def test_multi_engine(self):
        """
        """
        self.fail("Not done yet")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
