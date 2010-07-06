import unittest

from zope.component import testing
from Testing import ZopeTestCase as ztc

from Products.PloneTestCase import PloneTestCase as ptc

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base  

BaseA = declarative_base()
BaseB = declarative_base()

class ObjectA(BaseA):
    
    __tablename__ = "objecta"
    
    id = sa.schema.Column(sa.types.Integer, primary_key=True)
    
    foo = sa.schema.Column(sa.types.Unicode, nullable=False)

    
class ObjectB(BaseB):
    
    __tablename__ = "objectb"
    
    id = sa.schema.Column(sa.types.Integer, primary_key=True)
    
    bar = sa.schema.Column(sa.types.Unicode, nullable=False)
            
class TestDB(ptc.PloneTestCase):
    
    def test_multi_engine(self):
        """
        This is test is to check that the underlying eggs are
        behaving themselves and properly using multiple engine support.
        """
        
        BaseA.metadata.bind = sa.create_engine("sqlite:///a.db")
        BaseB.metadata.bind = sa.create_engine("sqlite:///b.db")
        
        BaseA.metadata.create_all(checkfirst=True)
        BaseB.metadata.create_all(checkfirst=True)
        
#        Session = sa.orm.sessionmaker()
#        session = Session()
#        session.add(ObjectA(foo=u"HELLO OBJECTA!"))
#        session.add(ObjectB(foo=u"HELLO OBJECTB!"))
        
        
    def test_multi_domain(self):
        """
        Should test that database names don't collide across multiple domains
        (studies)
        
        TODO move to another test case as this is not specific to DB
        """
        
    def test_multi_database(self):
        """
        Should test that database names don't collide across multiple physical
        databases.
        
        TODO move to another test case as this is not specific to DB
        """


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)





