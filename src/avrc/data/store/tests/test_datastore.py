import unittest

import transaction
import zope.component.testing
from zope.configuration import xmlconfig
from zope.interface.verify import verifyClass

from z3c.saconfig import EngineFactory
from z3c.saconfig import GloballyScopedSession
from z3c.saconfig.interfaces import IEngineFactory
from z3c.saconfig.interfaces import IScopedSession

import avrc.data.store
from avrc.data.store import interfaces
from avrc.data.store import datastore

from avrc.data.store.tests import testing

class TestCase(unittest.TestCase):

    def setUp(self):
        zope.component.testing.setUp(self)
        engine_factory = EngineFactory(u"sqlite:///:memory:")
        ScopedSession = GloballyScopedSession()
        zope.component.provideUtility(engine_factory, provides=IEngineFactory)
        zope.component.provideUtility(ScopedSession, provides=IScopedSession)

        xmlconfig.file(u"configure.zcml", avrc.data.store)

    def tearDown(self):
        zope.component.testing.tearDown(self)

class DatastoreTestCase(TestCase):

    def test_implementation(self):
        """ Tests if the data store implementation has fully objected the
            interface contract.
        """
        iface = interfaces.IDatastore
        impl = datastore.Datastore
        self.assertTrue(verifyClass(iface, impl))

    def test_add_instance(self):
        """ Tests that data store is able to successfully add an object instance
        """
        ds = datastore.Datastore(session=u"")

        sm = ds.getSchemaManager()

        sm.put(testing.IStandaloneInterface)
        sm.put(testing.ISimple)
        sm.put(testing.IAnnotatedInterface)

        iface = sm.get(testing.IStandaloneInterface.__name__)

        obj = ds.spawn(iface,
            foo=u"Hello World!",
            bar=u"Really\n\n\nlong",
            baz=123
            )

        key = ds.put(obj)

        ds.get("avrc.data.store.schema.virtual.IStandaloneInterface")

    def test_choiced_instance(self):
        """
        """
        ds = datastore.Datastore(session=u"")

        sm = ds.schemata

        sm.put(testing.IChoicedInterface)

        iface = sm.get(testing.IChoicedInterface.__name__)

        obj = ds.spawn(iface, choice=u"foo")

        ds.put(obj)

        self.fail("OMG")

    def test_update_data(self):
        ds = datastore.Datastore(session=u"")
        sm = ds.schemata

        isource = testing.IStandaloneInterface

        sm.put(isource)

        iface = sm.get(isource.__name__)

        spawned = ds.spawn(iface,
#            foo=u"Before update",
#            bar=u"This is text before\nwe update",
#            baz=123,
#            joe=["jello", "apples"]
            )

        print "spawned"
        print spawned.__dict__

        obj = ds.put(spawned)

        print "putted"
        print obj.__dict__

        gotten = ds.get(obj)

        print "gotten"
        print gotten.__dict__

        obj.foo = u"After update"
        obj.bar = u"Now let's see it\nthis actually worked"
        obj.baz = 987
        obj.joe = ["apples", "bananas"]
        print "modified"
        print obj.__dict__

        obj = ds.put(obj)
        print "putted"
        print obj.__dict__

        self.fail("List interface test complete")

    def test_list_schemata(self):
        ds = datastore.Datastore(session=u"")
        sm = ds.schemata

        sm.put(testing.IListInterface)

        iface = sm.get(testing.IListInterface.__name__)

        obj = ds.put(ds.spawn(iface, int_list=[1,5,10], choice_list=["foo", "baz"]))

        print obj
        gotten = ds.get(obj)
        print gotten.__dict__

        self.fail("List interface test complete")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
