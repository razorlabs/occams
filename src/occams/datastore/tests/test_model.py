
import unittest2 as unittest
from datetime import datetime

from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

import sqlalchemy.exc

from occams.datastore import model


from occams.datastore.testing import DATABASE_LAYER


class ModelTestCase(unittest.TestCase):
    """
    Verifies DataStore compatibility with Zope-style schema
    """

    layer = DATABASE_LAYER

    def testSchema(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Schema).count()
        self.assertEquals(schemaCount, 1, u'Found more than one entry')

    def testAttribute(self):
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

    def testChoice(self):
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

    def testSchemaCopy(self):
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
