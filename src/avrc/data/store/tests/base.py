
import unittest

import zope.component
import zope.component.testing

from z3c.saconfig import EngineFactory
from z3c.saconfig import GloballyScopedSession
from z3c.saconfig.interfaces import IEngineFactory
from z3c.saconfig.interfaces import IScopedSession

class TestCase(unittest.TestCase):

    def setUp(self):
        zope.component.testing.setUp(self)
        engine_factory = EngineFactory(u"sqlite:///:memory:")
        ScopedSession = GloballyScopedSession()
        zope.component.provideUtility(engine_factory, provides=IEngineFactory)
        zope.component.provideUtility(ScopedSession, provides=IScopedSession)

    def tearDown(self):
        zope.component.testing.tearDown(self)
