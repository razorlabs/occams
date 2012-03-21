
import unittest2 as unittest
from datetime import datetime

from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

import sqlalchemy.exc

from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER

class SchemaTestCase(unittest.TestCase):
    """
    Verifies Schema model
    """

    layer = DATASTORE_LAYER

    def testAdd(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Schema).count()
        self.assertEquals(schemaCount, 1, u'Found more than one entry')

    def testProperties(self):
        session = self.layer['session']
        schema = model.Schema(name='Sample', title=u'This is a sample.')
        session.add(schema)
        session.flush()

        # Check that all properties are working properly
        self.assertEqual(None, schema.base_schema)
        self.assertEqual([], schema.sub_schemata)
        self.assertEqual(None, schema.description)
        self.assertEqual('eav', schema.storage)
        self.assertEqual(None, schema.is_association)
        self.assertEqual(None, schema.is_inline)
        self.assertNotEqual(None, schema.create_date)
        self.assertNotEqual(None, schema.modify_date)

    def testMissingTitle(self):
        session = self.layer['session']
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.add(model.Schema(name='Sample'))
            session.flush()

    def testCopy(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(name='foo', title=u'Enter Foo', type='string', order=0)
        schema['foo'].choices = [
            model.Choice(name='foo', title=u'Foo', value='foo', order=0),
            model.Choice(name='bar', title=u'Bar', value='bar', order=1),
            model.Choice(name='baz', title=u'Baz', value='baz', order=2),
            ]
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Choice).count()
        self.assertEquals(schemaCount, 3, u'Did not find choices')

        schemaCopy = schema.copy()
        session.add(schemaCopy)
        session.flush()
        self.assertNotEqual(schema.id, schemaCopy.id)


class AttributeTestCase(unittest.TestCase):
    """
    Verifies Attribute model
    """

    layer = DATASTORE_LAYER

    def testAdd(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(
            name='foo',
            title=u'Enter Foo',
            type='string',
            order=0
            )
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Attribute).count()
        self.assertEquals(schemaCount, 1, u'Found more than one entry')


class ChoiceTestCase(unittest.TestCase):
    """
    Verifies Choice model
    """

    layer = DATASTORE_LAYER

    def testAdd(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(name='foo', title=u'Enter Foo', type='string', order=0)
        schema['foo'].choices = [
            model.Choice(name='foo', title=u'Foo', value='foo', order=0),
            model.Choice(name='bar', title=u'Bar', value='bar', order=1),
            model.Choice(name='baz', title=u'Baz', value='baz', order=2),
            ]
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Choice).count()
        self.assertEquals(schemaCount, 3, u'Did not find choices')


