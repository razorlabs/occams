
import unittest

import transaction
from zope.interface.verify import verifyClass
from zope.interface import implements

import z3c.saconfig

from avrc.data.store.tests.base import TestCase

from avrc.data.store import interfaces
from avrc.data.store import schema

class DummyDatastore(object):
    """ Dummy datastore but with only the parts we need.
    """
    implements(interfaces.IDatastore)

    def getScopedSession(self):
        return z3c.saconfig.named_scoped_session(u"")

class SchemaManagementTestCase(TestCase):

    def test_implementation(self):
        """ Make sure the schema manager is fully implemented
        """
        iface = interfaces.ISchemaManager
        impl = schema.SchemaManager
        self.assertTrue(verifyClass(iface, impl))

    def test_add_name(self):
        """ Make sure we can create a name.
        """
        manager = schema.DatastoreSchemaManager(DummyDatastore())

    def test_schema_import(self):
        """ Tests that the schema manager can properly import a schema into the
            data store. The way it does this is it import the schema into the
            data store, retrieves it and then checks if it's equivalent.
        """
        itest = samples.IStandaloneInterface

        schema.MutableSchema.import_(itest)

        klass = schema.MutableSchema.get_interface(itest.__name__)

        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(interfaces.IMutableSchema))
        self.assertEquals(klass.__name__, itest.__name__)
        self.assertEquals(schema.virtual.__name__, klass.__module__)

        # Check to make sure the generated interface still specifies the
        # correct fields
        dummynames = set(zope.schema.getFieldNames(itest))
        klassnames = set(zope.schema.getFieldNames(klass))
        self.assertTrue(set(dummynames) < set(klassnames))

        # Check that we can properly recreate the fields also
        for name in dummynames:
            self.assertEquals(klass[name], itest[name])

    def test_composite_import(self):
        """ Test a schema that contains a object field to a another schema
        """

        itest = samples.IComposedInterface

        self.assertRaises(interfaces.UndefinedSchemaError,
                          schema.MutableSchema.import_,
                          itest)

        schema.MutableSchema.import_(samples.ISimple)
        schema.MutableSchema.import_(samples.IComposedInterface)

        # TODO check this

    def test_vocabulary_import(self):
        """
        """

    def test_annotated_import(self):
        """
        """
        itest = samples.IAnnotatedInterface
        schema.MutableSchema.import_(itest)

        # Make sure the annotations are intact
        klass = schema.MutableSchema.get_interface(itest.__name__)

        from pprint import pprint

        pprint(itest.queryTaggedValue('__form_directive_values__'))
        pprint(klass.queryTaggedValue('__form_directive_values__'))

    def test_inheritance(self):
        """
        """


    def test_versioning(self):
        """
        """

    def test_dependents(self):
        """
        """
        #dsn = u"sqlite:///test.db"
        dsn = u"sqlite:///:memory:"
        ds = datastore.Datastore(title=u"my ds", dsn=dsn)

        sm = ds.schemata

        sm.put(testing.ISimple)
        sm.put(testing.IStandaloneInterface)
        sm.put(testing.IDependentInterface)

        iface = sm.get(testing.IDependentInterface.__name__)

        for dependent in iface.__dependents__:
            print dependent

        #ds.put(obj)

        self.fail("OMG")

    def test_directives(self):
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = datastore.Datastore(title=u"my ds", dsn=dsn)

        sm = ds.schemata

        sm.put(testing.IAnnotatedInterface)

        from pprint import pprint

        print
        print "Original"
        for tag in testing.IAnnotatedInterface.getTaggedValueTags():
            print tag
            pprint(testing.IAnnotatedInterface.getTaggedValue(tag))


        pprint(testing.IAnnotatedInterface.getTaggedValue("__form_directive_values__")["plone.supermodel.fieldsets"][0].__dict__)

        iface = sm.get(testing.IAnnotatedInterface.__name__)

        print
        print "Generated"
        for tag in iface.getTaggedValueTags():
            print tag
            pprint(iface.getTaggedValue(tag))


        self.fail("OMG")

    def test_inheritance(self):
        """
        """
        dsn = u"sqlite:///test.db"
        #dsn = u"sqlite:///:memory:"
        ds = datastore.Datastore(title=u"blah", dsn=dsn)
        sm = ds.schemata

        sm.put(testing.IGrandfather)
        sm.put(testing.IGrandmother)
        sm.put(testing.IFather)
        sm.put(testing.IUncle)
        sm.put(testing.IAunt)
        sm.put(testing.IBrother)
        sm.put(testing.ISister)

        iface = sm.get(testing.IGrandfather.__name__)
        descendants = sm.get_descendants(iface)

        print str(iface) + " " + str(iface.getBases())
        print "descendants:"
        for descendant in descendants:
            print str(descendant) + " " + str(descendant.getBases())

        print

        self.fail("Inheritance test complete")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
