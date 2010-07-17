import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
ptc.setupPloneSite()

import zope.schema
from zope.interface import Interface, verify

import avrc.data.store
from avrc.data.store import schema
from avrc.data.store import interfaces

class IObject(Interface):
    """
    """
    
    foo = zope.schema.TextLine(title=u"FOO")
    
    bar = zope.schema.Text(title=u"BAR")
    

class IDummy(Interface):
    """
    This is a dummy schema to test if the schema manger can properly import it.
    """
    
    integer = zope.schema.Int(title=u"INTEGER", description=u"INTEGERDESC")
    
    string = zope.schema.TextLine(title=u"STRING", description=u"STRINGDESC")
    
    text = zope.schema.Text(title=u"TEXT", description=u"TEXTDESC")
    
    boolean = zope.schema.Bool(title=u"BOOL", description=u"BOOLDESC")
    
    decimal = zope.schema.Decimal(title=u"DECIMAL", description=u"DECIMALDESC")
    
    datetime = zope.schema.Datetime(title=u"DATETIME", description=u"DATETIMEDESC")
    
    object = zope.schema.Object(title=u"OBJECT", description=u"OBJECTDESC", schema=IObject)
    

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
        Tests proper implementation
        """
        interface = interfaces.ISchemaManager
        cls = schema.SchemaManager
        
        self.assertTrue(interface.implementedBy(cls), "Not implemented")
        self.assertTrue(verify.verifyClass(interface, cls))
        
    def test_schema_import(self):
        """
        Tests that the schema manager can properly import a schema into the
        data store
        """
        
        mg = schema.SchemaManager()
        
        mg.importPredefined(IDummy)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
