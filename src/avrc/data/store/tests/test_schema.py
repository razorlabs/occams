import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite

ptc.setupPloneSite()

import zope.schema
from zope.component import provideUtility
from zope.interface import verify
from zope.interface.interface import InterfaceClass

import sqlalchemy as sa

import avrc.data.store
from avrc.data.store import schema
from avrc.data.store import datastore
from avrc.data.store import interfaces
from avrc.data.store import model

import samples

DSN = "sqlite:///:memory:"
ECHO = True

class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml', avrc.data.store)
            fiveconfigure.debug_mode = False

            # Create a fake in-memory session
            engine = sa.create_engine(DSN, echo=ECHO)
            model.setup(engine)
            utility = datastore.SessionFactory(bind=engine)
            provideUtility(utility, provides=interfaces.ISessionFactory)
            datastore.setupSupportedTypes()

        @classmethod
        def tearDown(cls):
            pass

    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_implementation(self):
        """
        Tests proper implementation
        """
        self.assertTrue(verify.verifyClass(interfaces.ISchemaManager,
                                           schema.SchemaManager))

    def test_schema_import(self):
        """
        Tests that the schema manager can properly import a schema into the
        data store. The way it does this is it import the schema into the
        data store, retrieves it and then checks if it's equivalent.
        """
        itest = samples.IStandaloneInterface
        
        schema.MutableSchema.import_(itest)
        
        klass = schema.MutableSchema.get_interface(itest.__name__)

        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(interfaces.IMutableSchema))
        self.assertEquals(klass.__name__, itest.__name__)
        self.assertEquals("avrc.data.store.schema.generated", klass.__module__)

        # Check to make sure the generated interface still specifies the
        # correct fields
        dummynames = set(zope.schema.getFieldNames(itest))
        klassnames = set(zope.schema.getFieldNames(klass))
        self.assertTrue(set(dummynames) < set(klassnames))

        # Check that we can properly recreate the fields also
        for name in dummynames:
            self.assertEquals(klass[name], itest[name])

    def test_composite_import(self):
        """
        Test a schema that contains a object field to a another schema
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
        
    def test_versioning(self):
        """
        """

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
