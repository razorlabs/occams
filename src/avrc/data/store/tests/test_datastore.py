import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
ptc.setupPloneSite()

import avrc.data.store

class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml', avrc.data.store)
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass
        
    def test_multi_site(self):
        
        self.fail("Not implemented")




def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
