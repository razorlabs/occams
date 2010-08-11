"""
"""

import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite

from zope.interface import verify

import avrc.data.store
from avrc.data.store import interfaces
from avrc.data.store import protocol

ptc.setupPloneSite()

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

    def test_implementation(self):
        """
        Tests if the data store implementation has fully objected the interface
        contract
        """
        interface = interfaces.IProtocolManager
        cls = protocol.DataStoreDomain

        self.assertTrue(interface.implementedBy(cls), "Not implemented")
        self.assertTrue(verify.verifyClass(interface, cls))

    def test_adapter(self):
        """
        Maker sure we can extract a domain manager out of the engine
        """

    def test_add(self):
        """
        """
        self.fail("TODO")

    def test_remove(self):
        self.fail("TODO")


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
