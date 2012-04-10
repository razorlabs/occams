"""
Tests for storage implementations and services
"""

import unittest2 as unittest
from datetime import date

import sqlalchemy.exc
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore.interfaces import  IEntity

p1 = date(2012, 3, 1)
p2 = date(2012, 4, 1)
p3 = date(2012, 5, 1)
p4 = date(2012, 6, 1)


class EntityModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = DATASTORE_LAYER

    def testImplementation(self):
        self.assertTrue(verifyClass(IEntity, model.Entity))
        self.assertTrue(verifyObject(IEntity, model.Entity()))

    def testAdd(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()
        count = session.query(model.Entity).count()
        self.assertEquals(1, count)

    def testProperties(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        # Check that all properties are working properly
        self.assertIsNotNone(entity.schema)
        self.assertIsNotNone(entity.create_date)
        self.assertIsNotNone(entity.create_user)
        self.assertIsNotNone(entity.modify_date)
        self.assertIsNotNone(entity.modify_user)

    def testDefaultCollectDate(self):
        # Make sure the system can auto-assign a collect date for the entry
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()
        self.assertEqual(date.today(), entity.collect_date)

        # If one is supplied by the user, don't do anything
        collect_date = date(2010, 9, 1)
        entity = model.Entity(
            schema=schema,
            name='Entry 2',
            title=u'Entry 2',
            collect_date=collect_date
            )
        session.add(entity)
        session.flush()
        self.assertEqual(entity.collect_date, collect_date)

    def testMissingTitle(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.add(model.Entity(schema=schema, name='Entry'))
            session.flush()

    def testDictLike(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        # The schema does not define the target attribute, so it should error
        with self.assertRaises(KeyError):
            entity['foo'] = 5

        schema['foo'] = model.Attribute(title=u'', type='integer', order=0)
        entity['foo'] = 5
        session.flush()
        self.assertEqual(5, entity['foo'])

        schema['bar'] = model.Attribute(title=u'', type='integer', is_collection=True, order=1)
        entity['bar'] = [1, 2, 3]
        session.flush()
        self.assertListEqual(entity['bar'], [1, 2, 3])

    def testDelete(self):
        # Test deleting an attribute via dict-like API
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)

        with self.assertRaises(KeyError):
            del entity['foo']

        schema['foo'] = model.Attribute(title=u'', type='integer', order=0)
        session.flush()

        # Nothing happens
        del entity['foo']
        session.flush()

        entity['foo'] = 5
        session.flush()

        # The attribute should have been committed
        result = session.query(model.ValueInteger).filter_by(attribute=schema['foo']).count()
        self.assertEqual(1, result)
        # Delete it like you would a dictionary
        del entity['foo']
        session.flush()
        # Should have been deleted
        result = session.query(model.ValueInteger).filter_by(attribute=schema['foo']).count()
        self.assertEqual(0, result)

        # Now try it with something that can have more than one value..
        schema['bar'] = model.Attribute(title=u'', type='integer', is_collection=True, order=1)
        entity['bar'] = [1, 2, 3]
        session.flush()

        # The attribute should have been committed
        result = session.query(model.ValueInteger).filter_by(attribute=schema['bar']).count()
        self.assertEqual(3, result)
        # Delete it like you would a dictionary
        del entity['bar']
        session.flush()
        # Should have been deleted
        result = session.query(model.ValueInteger).filter_by(attribute=schema['bar']).count()
        self.assertEqual(0, result)


    def testItems(self):
        # Make sure we can enumerate the key/value pairs of the schema
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()
        items = entity.items()
        self.assertEqual([], items)

        schema['foo'] = model.Attribute(title=u'', type='integer', order=0)
        entity['foo'] = 5
        session.flush()
        items = entity.items()
        self.assertEqual(1, len(items))
        self.assertListEqual([('foo', 5)], items)

        schema['bar'] = model.Attribute(title=u'', type='integer', is_collection=True, order=1)
        entity['bar'] = [1, 2, 3]
        session.flush()
        items = entity.items()
        self.assertEqual(2, len(items))
        self.assertListEqual([('foo', 5), ('bar', [1, 2, 3])], items)
