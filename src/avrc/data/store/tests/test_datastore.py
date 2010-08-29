from pprint import pprint
import unittest

from zope.testing import doctestunit
from zope.component import testing
from Testing import ZopeTestCase as ztc

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
ptc.setupPloneSite()

from zope.app.folder import rootFolder
from zope.app.component.site import SiteManagerContainer, LocalSiteManager
from zope.app.component.site import setSite
from zope.component import createObject
from zope.component import getUtility
from zope.interface import verify

import avrc.data.store
from avrc.data.store import interfaces
from avrc.data.store import datastore
from avrc.data.store import model
from avrc.data.store.datastore import named_session

from avrc.data.store.tests import samples

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
        self.assertTrue(verify.verifyClass(interfaces.IDatastore,
                                           datastore.Datastore))

    def test_build(self):
        """
        Passes if the database gets built.
        """
        dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"my ds", dsn=dsn)

        self.assertTrue(ds is not None)

    def test_multi_site(self):
        """
        Test that the DataStore is able to handle being added to multiple sites
        without mixing the underlying database engines and session.
        """

        root = rootFolder()

        root[u"site1"] = site1 = SiteManagerContainer()
        root[u"site2"] = site2 = SiteManagerContainer()

        self.assertNotEqual(site1, site2, u"Site containers must be different.")

        site1.setSiteManager(LocalSiteManager(site1))
        site2.setSiteManager(LocalSiteManager(site2))

        sm1 = site1.getSiteManager()
        sm2 = site2.getSiteManager()

        self.assertNotEqual(sm1, sm2, u"Site managers must be different.")

        sm1.registerUtility(component=datastore.Datastore(
                                  title=u"ds1",
                                  dsn=u"sqlite:///:memory:"),
                            provided=interfaces.IDatastore)
        sm2.registerUtility(component=datastore.Datastore(
                                  title=u"ds2",
                                  dsn=u"sqlite:///:memory:"),
                            provided=interfaces.IDatastore)

        setSite(site1)
        ds1 = getUtility(interfaces.IDatastore)

        setSite(site2)
        ds2 = getUtility(interfaces.IDatastore)

        self.assertNotEqual(ds1, ds2)

        setSite(site1)
        ds = getUtility(interfaces.IDatastore)
        Session = named_session(ds)
        session = Session()

        session.add(model.Type(title=u"FOO"))
        session.commit()

        p = session.query(model.Type).filter_by(title=u"FOO").first()
        self.assertTrue(p is not None, "No person found in first database")

        p = session.query(model.Type).filter_by(title=u"BAR").first()
        self.assertTrue(p is None, "Databases engines are mixed up.")

        setSite(site2)
        ds = getUtility(interfaces.IDatastore)
        Session = named_session(ds)
        session = Session()

        session.add(model.Type(title=u"BAR"))
        session.commit()

        p = session.query(model.Type).filter_by(title=u"BAR").first()
        self.assertTrue(p is not None, "No person found in first database")

        p = session.query(model.Type).filter_by(title=u"FOO").first()
        self.assertTrue(p is None, "Databases engines are mixed up.")

    def test_add_instance(self):
        """
        Tests that data store is able to successfully add an object instance
        """
        #dsn = u"sqlite:///test.db"
        dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"my ds", dsn=dsn)

        sm = ds.schemata

        sm.put(samples.IStandaloneInterface)
        sm.put(samples.ISimple)
        sm.put(samples.IAnnotatedInterface)

        iface = sm.get(samples.IStandaloneInterface.__name__)

        obj = ds.spawn(iface,
            foo=u"Hello World!",
            bar=u"Really\n\n\nlong",
            baz=123
            )

        key = ds.put(obj)

        ds.get("avrc.data.store.schema.virtual.IStandaloneInterface")

        self.fail("OMG")

    def test_directives(self):
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"my ds", dsn=dsn)

        sm = ds.schemata

        sm.put(samples.IAnnotatedInterface)

        from pprint import pprint

        print
        print "Original"
        for tag in samples.IAnnotatedInterface.getTaggedValueTags():
            print tag
            pprint(samples.IAnnotatedInterface.getTaggedValue(tag))


        pprint(samples.IAnnotatedInterface.getTaggedValue("__form_directive_values__")["plone.supermodel.fieldsets"][0].__dict__)

        iface = sm.get(samples.IAnnotatedInterface.__name__)

        print
        print "Generated"
        for tag in iface.getTaggedValueTags():
            print tag
            pprint(iface.getTaggedValue(tag))


        self.fail("OMG")

    def test_choiced_instance(self):
        """
        """
        #dsn = u"sqlite:///test.db"
        dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"my ds", dsn=dsn)

        sm = ds.schemata

        sm.put(samples.IChoicedInterface)

        iface = sm.get(samples.IChoicedInterface.__name__)

        obj = ds.spawn(iface, choice=u"foo")

        ds.put(obj)

        self.fail("OMG")


    def test_dependents(self):
        """
        """
        #dsn = u"sqlite:///test.db"
        dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"my ds", dsn=dsn)

        sm = ds.schemata

        sm.put(samples.ISimple)
        sm.put(samples.IStandaloneInterface)
        sm.put(samples.IDependentInterface)

        iface = sm.get(samples.IDependentInterface.__name__)

        for dependent in iface.__dependents__:
            print dependent

        #ds.put(obj)

        self.fail("OMG")

    def test_inheritance(self):
        """
        """
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"blah", dsn=dsn)
        sm = ds.schemata

        sm.put(samples.IGrandfather)
        sm.put(samples.IGrandmother)
        sm.put(samples.IFather)
        sm.put(samples.IUncle)
        sm.put(samples.IAunt)
        sm.put(samples.IBrother)
        sm.put(samples.ISister)

        iface = sm.get(samples.IGrandfather.__name__)
        descendants = sm.get_descendants(iface)

        print str(iface) + " " + str(iface.getBases())
        print "descendants:"
        for descendant in descendants:
            print str(descendant) + " " + str(descendant.getBases())

        print

        self.fail("Inheritance test complete")

    def test_update_data(self):
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"blah", dsn=dsn)
        sm = ds.schemata

        isource = samples.IStandaloneInterface

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
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"blah", dsn=dsn)
        sm = ds.schemata

        sm.put(samples.IListInterface)

        iface = sm.get(samples.IListInterface.__name__)

        obj = ds.put(ds.spawn(iface, int_list=[1,5,10], choice_list=["foo", "baz"]))

        print obj
        gotten = ds.get(obj)
        print gotten.__dict__

        self.fail("List interface test complete")

    def test_search(self):
        """
        """
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = createObject("avrc.data.store.Datastore", title=u"blah", dsn=dsn)

        ds.schema.put(samples.IStandaloneInterface)

        # just get everything
        results_obj = ds.search.by_base(4, 10)

        print
        print results_obj
        print

        self.fail("Search Complete")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
