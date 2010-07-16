import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
ptc.setupPloneSite()

from zope.interface import verify

import avrc.data.store
from avrc.data.store import schema
from avrc.data.store import interfaces

class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml',
                             avrc.data.store)
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass

    def test_implementation(self):
        """
        Tests proper implementation
        """
        interface = interfaces.ISchemaManager
        cls = schema.SchemaManager
        
        self.assertTrue(interface.implementedBy(cls), "Not implemented")
        self.assertTrue(verify.verifyClass(interface, cls))


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
