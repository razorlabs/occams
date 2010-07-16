import unittest

from Products.PloneTestCase import PloneTestCase as ptc

from zope.interface import verify

from avrc.data.store import session
from avrc.data.store import interfaces

class TestCase(ptc.PloneTestCase):
    
    def test_implementation(self):
        """
        Tests proper implementation
        """
        interface = interfaces.ISessionFactory
        cls = session.SessionFactory
        
        self.assertTrue(interface.implementedBy(cls), "Not implemented")
        self.assertTrue(verify.verifyClass(interface, cls))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
