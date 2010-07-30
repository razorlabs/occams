import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite

ptc.setupPloneSite()

import zope.schema
from zope.app.folder import rootFolder
from zope.component import provideUtility
from zope.interface import verify
from zope.interface.interface import InterfaceClass

import sqlalchemy as sa

import avrc.data.store
from avrc.data.store import schema
from avrc.data.store import datastore
from avrc.data.store import interfaces
from avrc.data.store import model

import etc

class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml', avrc.data.store)
            fiveconfigure.debug_mode = False

            # Create a fake in-memory session
            engine = sa.create_engine("sqlite:///:memory:", echo=etc.SA_ECHO)
            model.setup_fia(engine)
            model.setup_pii(engine)
            provideUtility(datastore.SessionFactory(bind=engine),
                           provides=interfaces.ISessionFactory)
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
        mg = schema.SchemaManager() 
        mg.importSchema(etc.IDummy)
        
        klass = mg.getSchema(etc.IDummy.__name__)
        
        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(interfaces.IMutableSchema))
        self.assertEquals(klass.__name__, etc.IDummy.__name__)
        self.assertEquals("avrc.data.store.schema.generated", klass.__module__)
        
        # Check to make sure the generated interface still specifies the
        # correct fields
        dummynames = set(zope.schema.getFieldNames(etc.IDummy))
        klassnames = set(zope.schema.getFieldNames(klass))
        self.assertTrue(set(dummynames) < set(klassnames))
        
        # Check that we can properly recreate the fields also
        for name in dummynames:
            self.assertEquals(klass[name], etc.IDummy[name])
            

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
