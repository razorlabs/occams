"""
Tests for storage implementations and services
"""

import unittest2 as unittest

from zope.interface import Interface
from zope.interface import implements
import zope.schema

from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore.item import Item
from occams.datastore.item import ItemFactory
from occams.datastore.item import entityToDictionary


class ItemTestCase(unittest.TestCase):

    def testWithoutInterface(self):
        # Just a regular opject
        item = Item()
        self.assertEqual(0, len(list(iter(item.__provides__))))

    def testWithInterface(self):
        class IFoo(Interface):
            integerField = zope.schema.Int(title=u'Integer')

        class Foo(Item):
            implements(IFoo)

        foo = Foo()
        self.assertTrue(IFoo.providedBy(foo))

        foo = Foo(integerField=10)
        self.assertTrue(IFoo.providedBy(foo))
        self.assertEqual(10, foo.integerField)

        # Ignores fields not in the interface
        foo = Foo(blah='adfjas;dfsadf')
        self.assertTrue(IFoo.providedBy(foo))
        with self.assertRaises(AttributeError):
            foo.blah


class ItemFactoryTestCase(unittest.TestCase):

    def testBasicInterface(self):
        class IFoo(Interface):
            integerField = zope.schema.Int(title=u'Integer')

        item = ItemFactory(IFoo)
        self.assertTrue(IFoo.providedBy(item))

        item = ItemFactory(IFoo, integerField=123)
        self.assertTrue(IFoo.providedBy(item))
        self.assertEqual(123, item.integerField)

        # Also ignores non-interface parameters
        item = ItemFactory(IFoo, blah='sdafasdfasdf')
        self.assertTrue(IFoo.providedBy(item))
        with self.assertRaises(AttributeError):
            item.blah

    def testWithSubObjectViaDictionary(self):
        class IBar(Interface):
            integerField = zope.schema.Int(title=u'Integer')

        class IFoo(Interface):
            bar = zope.schema.Object(title=u'Bar', schema=IBar)

        item = ItemFactory(IFoo)
        self.assertTrue(IFoo.providedBy(item))
        self.assertIsNone(item.bar)

        item = ItemFactory(IFoo, **dict(bar=dict(integerField=123)))
        self.assertTrue(IFoo.providedBy(item))
        self.assertTrue(IBar.providedBy(item.bar))
        self.assertEqual(123, item.bar.integerField)

    def testWithSubObjectViaItem(self):
        class IBar(Interface):
            integerField = zope.schema.Int(title=u'Integer')

        class IFoo(Interface):
            bar = zope.schema.Object(title=u'Bar', schema=IBar)

        item = ItemFactory(IFoo)
        self.assertTrue(IFoo.providedBy(item))
        self.assertIsNone(item.bar)

        # already premade
        bar = ItemFactory(IBar, integerField=123)
        item = ItemFactory(IFoo, **dict(bar=bar))
        self.assertTrue(IFoo.providedBy(item))
        self.assertTrue(IBar.providedBy(item.bar))
        self.assertEqual(123, item.bar.integerField)


class EntityToDictionaryTestCase(unittest.TestCase):

    layer = DATASTORE_LAYER

    def testBasic(self):
        session = self.layer['session']
        schema = model.Schema(name='IFoo', title=u'', state='published', attributes=dict(
            zero=model.Attribute(name='zero', title=u'', type='string', order=0),
            one=model.Attribute(name='one', title=u'', type='integer', order=1),
            two=model.Attribute(name='two', title=u'', type='boolean', order=2),
            ))
        entity = model.Entity(schema=schema, name='foo', title=u'Foo')
        session.add(entity)
        session.flush()

        entity['zero'] = u'huzzah?'
        entity['one'] = 123
        entity['two'] = True
        # This is currently not working because storage is not quite done yet
        data = entityToDictionary(entity)
        self.assertIn('__metadata__', data)
        self.assertIn('zero', data)
        self.assertIn('one', data)
        self.assertIn('two', data)

    def testWithSubObject(self):
        session = self.layer['session']
        schema = model.Schema(name='IFoo', title=u'', state='published',)
        schema['zero'] = model.Attribute(title=u'', type='object', order=0,)
        schema['zero'].object_schema = model.Schema(name='ISub', title=u'Sub', state='published',)
        schema['zero']['one'] = model.Attribute(title=u'', type='integer', order=0)
        schema['zero']['two'] = model.Attribute(title=u'', type='string', order=1)

        entity = model.Entity(schema=schema, name='foo', title=u'Foo')
        session.add(entity)
        session.flush()

        # Trying converting before we assign anything, because we're evil
        data = entityToDictionary(entity)
        self.assertIn('__metadata__', data)
        self.assertIn('zero', data)
        self.assertIsNone(data['zero'])

        # Now be nice and actually assign it data
        sub = model.Entity(schema=schema['zero'].object_schema, name='sub', title=u'sub')
        session.add(sub)
        session.flush()
        entity['zero'] = sub
        entity['zero']['one'] = 1234
        entity['zero']['two'] = u'huzzah?'

        data = entityToDictionary(entity)
        self.assertIn('__metadata__', data)
        self.assertIn('zero', data)
        self.assertIn('__metadata__', data['zero'])
        self.assertIn('one', data['zero'])
        self.assertEqual(1234, data['zero']['one'])
        self.assertIn('two', data['zero'])
        self.assertEqual(u'huzzah?', data['zero']['two'])

