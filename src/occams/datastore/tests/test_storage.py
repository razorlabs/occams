"""
Tests for storage implementations and services
"""

import unittest2 as unittest
from datetime import datetime
from datetime import date

import sqlalchemy.exc
from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore import directives
from occams.datastore.interfaces import IManager
from occams.datastore.interfaces import ISchemaManagerFactory
from occams.datastore.interfaces import ManagerKeyError
from occams.datastore.storage import EntityManager
from occams.datastore.storage import ObjectFactory
from occams.datastore.schema import SchemaManager
from occams.datastore.schema import HierarchyInspector
from occams.datastore.testing import DATASTORE_LAYER


p1 = date(2012, 3, 1)
p2 = date(2012, 4, 1)
p3 = date(2012, 5, 1)
p4 = date(2012, 6, 1)


class EntityModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = DATASTORE_LAYER


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


class EntityManagerTestCase(unittest.TestCase):
    """
    Verifies DataStore Entity storage
    """

    layer = DATASTORE_LAYER


#    def setUp(self):
#        self.layer['session'] = self.layer['session']
#
#        schema = model.Schema(name='Foo', title=u'Type Foo', create_date=time1, modify_date=time1)
#        self.layer['session'].add(schema)
#
#        self.layer['session'].add_all([
#            model.Entity(
#                schema=schema,
#                name='Foo', title=u'This is foo',
#                create_date=time1, modify_date=time1, remove_date=time2
#                ),
#            model.Entity(
#                schema=schema,
#                name='Foo', title=u'This is foo',
#                create_date=time2, modify_date=time2, remove_date=time4
#                ),
#            model.Entity(
#                schema=schema,
#                name='Foo', title=u'This is foo',
#                create_date=time4, modify_date=time4
#                ),
#
#
#            model.Entity(
#                schema=schema,
#                name='Bar', title=u'This is bar',
#                create_date=time1, modify_date=time1
#                ),
#
#
#            model.Entity(
#                schema=schema,
#                name='Baz', title=u'This is baz',
#                create_date=time1, modify_date=time1, remove_date=time3
#                ),
#
#            model.Entity(
#                schema=schema,
#                name='Baz', title=u'This is baz',
#                create_date=time3, modify_date=time3
#                ),
#
#
#            model.Entity(
#                schema=schema,
#                name='Caz', title=u'This is caz',
#                create_date=time1, modify_date=time1, remove_date=time2
#                ),
#            ])
#
#        self.layer['session'].flush()
#
#        self.schema = schema
#        self.iface = SchemaManager(self.layer['session']).get(schema.name, on=schema.create_date)
#        self.manager = EntityManager(self.layer['session'])
#
#
#    def tearDown(self):
#        self.schema = None
#        self.iface = None
#        self.manager = None
#
#
#    def test_implementation(self):
#        self.assertTrue(verifyClass(IManager, EntityManager))
#        self.assertTrue(verifyObject(IEntityManagerFactory, EntityManager))
#
#
#    def test_keys(self):
#        manager = self.manager
#
#        keys = manager.keys()
#        self.assertEqual(3, len(keys))
#
#        keys = manager.keys(ever=True)
#        self.assertEqual(7, len(keys))
#
#        keys = manager.keys(on=time2)
#        self.assertEqual(3, len(keys))
#        self.assertTrue('Foo' in keys)
#        self.assertTrue('Bar' in keys)
#        self.assertTrue('Baz' in keys)
#
#
#    def test_has(self):
#        manager = self.manager
#
#        self.assertTrue(manager.has('Foo'))
#        self.assertTrue(manager.has('Foo', on=datetime.now()))
#        self.assertTrue(manager.has('Foo', ever=True))
#        self.assertFalse(manager.has('foo'))
#        self.assertFalse(manager.has('foo', ever=False))
#
#        self.assertFalse(manager.has('Stuff'))
#        self.assertTrue(manager.has('Bar'))
#
#        self.assertFalse(manager.has('Caz'))
#        self.assertFalse(manager.has('Caz', on=datetime.now()))
#        self.assertTrue(manager.has('Caz', ever=True))
#        self.assertTrue(manager.has('Caz', on=time1))
#        self.assertFalse(manager.has('Caz', on=time2))
#        self.assertFalse(manager.has('Caz', on=time3))
#
#
#    def test_retire(self):
#        manager = self.manager
#        session = self.manager.session
#
#        # Can't retire something that doesn't exist
#        name = 'NonExisting'
#        result = manager.retire(name)
#        self.assertEqual(0, result)
#
#        # Can't retire something that's already retired
#        name = 'Caz'
#        result = manager.retire(name)
#        self.assertEqual(0, result)
#
#        # Make sure the item is actually retired
#        name = 'Foo'
#        result = manager.retire(name)
#        self.assertEqual(1, result)
#
#        result = (
#            session.query(model.Entity)
#            .filter(name == model.Entity.name)
#            .filter(None != model.Entity.remove_date)
#            .all()
#            )
#
#        self.assertEqual(3, len(result))
#
#
#    def test_restore(self):
#        manager = self.manager
#        session = self.manager.session
#
#        # Can't restore something that doesn't exist
#        name = 'NonExisting'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Can't restore something that isn't retired
#        name = 'Bar'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Make sure only the most recent entry is restored
#        name = 'Caz'
#        result = manager.restore(name)
#        self.assertEqual(1, result)
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Try to restore something that's been removed a couple of times,
#        # should only work on the most recently created
#        name = 'Foo'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Simulate retirement
#        result = (
#            session.query(model.Entity)
#            .filter(None == model.Entity.remove_date)
#            .update(dict(remove_date=model.NOW), 'fetch')
#            )
#
#        # Should only restore once
#        result = manager.restore(name)
#        self.assertEqual(1, result)
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#
#    def test_purge(self):
#        manager = self.manager
#        session = self.manager.session
#
#        result = session.query(model.Entity).count()
#        self.assertEqual(7, result)
#
#        # Can't purge anything that doesn't exist
#        name = 'NonExisting'
#        result = manager.purge(name)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time1)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time2)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time3)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time4)
#        self.assertEqual(0, result)
#        result = manager.purge(name, ever=True)
#        self.assertEqual(0, result)
#
#        # Purge single items
#        name = 'Bar'
#        result = manager.purge(name)
#        self.assertEqual(1, result)
#        result = session.query(model.Entity).filter_by(name=name).count()
#        self.assertEqual(0, result)
#
#        # Purge only the currently active item
#        name = 'Baz'
#        result = manager.purge(name)
#        self.assertEqual(1, result)
#        result = session.query(model.Entity).filter_by(name=name).count()
#        self.assertEqual(1, result)
#        result = (
#            session.query(model.Entity)
#            .filter_by(name=name, create_date=time1)
#            .count()
#            )
#        self.assertEqual(1, result)
#
#        # Purge an intermediary version
#        name = 'Foo'
#        result = manager.purge(name, on=time3)
#        self.assertEqual(1, result)
#        result = (
#            session.query(model.Entity)
#            .filter_by(name=name, create_date=time1)
#            .count()
#            )
#        self.assertEqual(1, result)
#        result = (
#            session.query(model.Entity)
#            .filter_by(name=name, create_date=time4)
#            .count()
#            )
#        self.assertEqual(1, result)
#
#        # Purge all of name (There's only two of "Foo" left at this point)
#        name = 'Foo'
#        result = manager.purge(name, ever=True)
#        self.assertEqual(2, result)
#        result = session.query(model.Entity).filter_by(name=name).count()
#        self.assertEqual(0, result)
#
#
#    def test_get(self):
#        manager = self.manager
#
#        # Get something that dosn't exist
#        name = 'NonExisting'
#        item = manager.get(name)
#        self.assertEqual(None, item)
#
#        # Get something that only has one version
#        name = 'Foo'
#        item = manager.get(name)
#        self.assertEqual(name, item.__name__)
#        self.assertNotEqual(None, item)
#        self.assertNotEqual(None, item.__title__)
#        self.assertNotEqual(None, item.__version__)
#
#        # Get something that's been removed
#        name = 'Caz'
#        item = manager.get(name)
#        self.assertEqual(None, item)
#
#        # Only works if we specify the version
#        item = manager.get(name, on=time1)
#        self.assertNotEqual(None, item)
#
#
#    def test_put(self):
#        manager = self.manager
#        session = self.manager.session
#        iface = self.iface
#
#        item = ObjectFactory(iface)
#        manager.put(item.__name__, item)
#
#
#class ValueManagerTestCase(unittest.TestCase):
#    """
#    Verifies the modification of values
#    """
#
#
#    layer = DATASTORE_LAYER
#
#
#    def setUp(self):
#        session = self.layer['session'] = self.layer['session']
#        schema = model.Schema(name='Schema', title=u'Test Schema')
#        entity = model.Entity(schema=schema, name='Sample', title=u'Sample')
#        # We're not versioning attributes, only data in this test case
#        foo = model.Attribute(
#            schema=schema, type='string', name='foo', title=u'Foo', order=1
#            )
#        bar = model.Attribute(
#            schema=schema, type='integer', name='bar', title=u'Bar', order=2
#            )
#
#        caz = model.Attribute(
#            schema=schema, type='datetime', name='caz', title=u'Caz', order=3
#            )
#
#        empty = model.Attribute(
#                schema=schema, type='string', name='empty', title=u'Empty', order=4
#            )
#        session.add(empty)
#
#        red = model.Choice(name='red', title=u'Red', value=u'red', order=1)
#        green = model.Choice(name='green', title=u'Green', value=u'green', order=2)
#        blue = model.Choice(name='blue', title=u'Blue', value=u'blue', order=3)
#        purple = model.Choice(name='purple', title=u'Purple', value=u'purple', order=4)
#        yellow = model.Choice(name='yellow', title=u'Yellow', value=u'yellow', order=5)
#
#        liz = model.Attribute(
#            schema=schema, type='string', name='liz', title=u'Liz', order=5,
#            is_collection=True, choices=dict(
#                red=red,
#                green=green,
#                blue=blue,
#                purple=purple,
#                yellow=yellow
#                )
#            )
#
#        session.add_all([
#            # Foo's values
#            model.ValueString(
#                entity=entity, attribute=foo, value=u'Hi!!!',
#                create_date=time1, modify_date=time2, remove_date=time2,
#                ),
#            model.ValueString(
#                entity=entity, attribute=foo, value=u'Never mind!!',
#                create_date=time2, modify_date=time4, remove_date=time4,
#                ),
#            model.ValueString(
#                entity=entity, attribute=foo, value=u'Hello world!!',
#                create_date=time4, modify_date=time4,
#                ),
#
#            # Bar's values
#            model.ValueInteger(
#                entity=entity, attribute=bar, value=42,
#                create_date=time2, modify_date=time3, remove_date=time3,
#                ),
#            model.ValueInteger(
#                entity=entity, attribute=bar, value=420,
#                create_date=time3, modify_date=time3,
#                ),
#
#            # Caz's values
#            model.ValueDatetime(
#                entity=entity, attribute=caz, value=datetime.now(),
#                create_date=time1, modify_date=time1, remove_date=time2,
#                ),
#
#            # Liz's values
#            model.ValueString(
#                entity=entity, attribute=liz, choice=red, value=u'red',
#                create_date=time1, modify_date=time2, remove_date=time2,
#                ),
#            model.ValueString(
#                entity=entity, attribute=liz, choice=blue, value=u'blue',
#                create_date=time1, modify_date=time2, remove_date=time2,
#                ),
#            model.ValueString(
#                entity=entity, attribute=liz, choice=purple, value=u'purple',
#                create_date=time2, modify_date=time2,
#                ),
#            model.ValueString(
#                entity=entity, attribute=liz, choice=blue, value=u'blue',
#                create_date=time2, modify_date=time2,
#                ),
#            model.ValueString(
#                entity=entity, attribute=liz, choice=green, value=u'green',
#                create_date=time2, modify_date=time2,
#                ),
#            ])
#
#        session.flush()
#
#        self.entity = entity
#        self.foo_attr = foo
#        self.bar_attr = bar
#        self.baz_attr = caz
#        self.liz_attr = liz
#        self.manager = ValueManager(entity)
#
#
#    def tearDown(self):
#        self.entity = None
#        self.foo_attr = None
#        self.bar_attr = None
#        self.baz_attr = None
#        self.liz_attr = None
#        self.manager = None
#
#
#    def test_implementation(self):
#        self.assertTrue(verifyClass(IManager, ValueManager))
#        self.assertTrue(verifyObject(IValueManagerFactory, ValueManager))
#
#
#    def test_keys(self):
#        manager = self.manager
#
#        # Haven't assigned anything yet
#        keys = manager.keys(on=datetime(1776, 7, 4))
#        self.assertEqual(0, len(keys))
#
#        keys = manager.keys()
#        self.assertEqual(3, len(keys))
#        keys = manager.keys(ever=True)
#        self.assertEqual(4, len(keys))
#
#        keys = manager.keys(on=time3)
#        self.assertTrue('foo' in keys)
#        self.assertTrue('bar' in keys)
#        self.assertTrue('liz' in keys)
#
#
#    def test_has(self):
#        manager = self.manager
#
#        self.assertTrue(manager.has('foo'))
#        self.assertTrue(manager.has('bar'))
#        self.assertTrue(manager.has('foo', on=datetime.now()))
#        self.assertTrue(manager.has('foo', ever=True))
#        self.assertFalse(manager.has('empty'))
#        self.assertFalse(manager.has('empty', ever=False))
#
#    def test_purge(self):
#        manager = self.manager
#        session = self.manager.session
#        bar_attr = self.bar_attr
#        foo_attr = self.foo_attr
#
#        # Can't purge anything that doesn't exist
#        name = 'empty'
#        result = manager.purge(name)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time1)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time2)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time3)
#        self.assertEqual(0, result)
#        result = manager.purge(name, on=time4)
#        self.assertEqual(0, result)
#        result = manager.purge(name, ever=True)
#        self.assertEqual(0, result)
#
#        # Purge only the currently active item
#        name = 'bar'
#        result = manager.purge(name)
#        self.assertEqual(1, result)
#        query = session.query(model.ValueInteger).filter_by(attribute=bar_attr)
#        result = query.count()
#        self.assertEqual(1, result)
#        result = query.filter_by(create_date=time2).count()
#        self.assertEqual(1, result)
#
#        # Purge an intermediary version
#        name = 'foo'
#        query = session.query(model.ValueString).filter_by(attribute=foo_attr)
#        result = manager.purge(name, on=time3)
#        self.assertEqual(1, result)
#        result = query.filter_by(create_date=time1).count()
#        self.assertEqual(1, result)
#        result = query.filter_by(create_date=time4).count()
#        self.assertEqual(1, result)
#
#        # Purge all of name (There's only two of "foo" left at this point)
#        name = 'foo'
#        result = manager.purge(name, ever=True)
#        self.assertEqual(2, result)
#        query = session.query(model.ValueString).filter_by(attribute=foo_attr)
#        result = query.count()
#        self.assertEqual(0, result)
#
#
#    def test_retire(self):
#        manager = self.manager
#        session = self.manager.session
#        foo_attr = self.foo_attr
#        entity = self.entity
#
#        # Can't retire something that doesn't exist
#        name = 'empty'
#        result = manager.retire(name)
#        self.assertEqual(0, result)
#
#        # Can't retire something that's already retired
#        name = 'caz'
#        result = manager.retire(name)
#        self.assertEqual(0, result)
#
#        # Make sure the item is actually retired
#        name = 'foo'
#        result = manager.retire(name)
#        self.assertEqual(1, result)
#
#        result = (
#            session.query(model.ValueString)
#            .filter_by(entity=entity, attribute=foo_attr)
#            .filter(None != model.ValueString.remove_date)
#            .all()
#            )
#
#        self.assertEqual(3, len(result))
#
#        # Retire the list
#        name = 'liz'
#        result = manager.retire(name)
#        # The list has three items, so it should have retired three values
#        self.assertEqual(3, result)
#
#
#    def test_restore(self):
#        manager = self.manager
#        session = self.manager.session
#        foo_attr = self.foo_attr
#        liz_attr = self.liz_attr
#
#        # Can't restore something that doesn't exist
#        name = 'empty'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Can't restore something that isn't retired
#        name = 'bar'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Make sure only the most recent entry is restored
#        name = 'caz'
#        result = manager.restore(name)
#        self.assertEqual(1, result)
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Try to restore something that's been removed a couple of times,
#        # should only work on the most recently created
#        name = 'foo'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#        # Simulate retirement
#        result = (
#            session.query(model.ValueString)
#            .filter_by(attribute=foo_attr, remove_date=None)
#            .update(dict(remove_date=model.NOW), 'fetch')
#            )
#        # Should only restore once (the most recent one)
#        result = manager.restore(name)
#        self.assertEqual(1, result)
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#        # Now do the same test, but for a list this time...
#        name = 'liz'
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#        # Simulate retirement
#        query = (
#            session.query(model.ValueString)
#            .filter_by(attribute=liz_attr, remove_date=None)
#            )
#        result = query.update(dict(remove_date=model.NOW), 'fetch')
#        # Should only restore once (for all three values)
#        result = manager.restore(name)
#        self.assertEqual(3, result)
#        result = manager.restore(name)
#        self.assertEqual(0, result)
#
#
#    def test_get(self):
#        manager = self.manager
#
#        # Get something that dosn't exist
#        name = 'empty'
#        result = manager.get(name)
#        self.assertEqual(None, result)
#
#        # Get something that only has one version
#        name = 'foo'
#        result = manager.get(name)
#        self.assertEqual(u'Hello world!!', result)
#
#        # Get something that's been removed
#        name = 'caz'
#        result = manager.get(name)
#        self.assertEqual(None, result)
#        # Only works if we specify the version
#        result = manager.get(name, on=time1)
#        self.assertNotEqual(None, result)
#
#
#    def test_put(self):
#        manager = self.manager
#        session = self.manager.session
#        entity = self.entity
#
#        # Cannot put unsupported type
#        name = 'will_fail'
#        self.assertRaises(PropertyNotDefinedError, manager.put, name, u'blah')
#
#        # Now put something that's going to be versioned several times
#        # First, let's manually create a property
#
#        attribute = model.Attribute(
#            schema=entity.schema,
#            type='string', name='sample', title=u'Sample', order=6,
#            )
#        session.add(attribute)
#        session.flush()
#
#        id_1 = manager.put(attribute.name, u'Test')
#        entry_1 = session.query(model.ValueString).get(id_1)
#        self.assertNotEqual(None, id_1)
#        self.assertNotEqual(None, entry_1)
#        self.assertEqual(None, entry_1.remove_date)
#
#        # OK, we hate the title, let's change it.
#        id_2 = manager.put(attribute.name, u'Another Test')
#        entry_2 = session.query(model.ValueString).get(id_2)
#        self.assertNotEqual(id_1, id_2)
#        self.assertNotEqual(entry_2.value, entry_1.value)
#        # Make sure the new version is different from the old.
#        self.assertNotEqual(None, entry_1.remove_date)
#        self.assertEqual(None, entry_2.remove_date)
#        self.assertTrue(entry_1.create_date <= entry_2.create_date)
#        # More changes
#        id_3 = manager.put(attribute.name, u'Weeee!')
#        entry_3 = session.query(model.ValueString).get(id_3)
#        self.assertNotEqual(id_1, id_3)
#        self.assertNotEqual(id_2, id_3)
#        self.assertNotEqual(entry_3.value, entry_2.value)
#        self.assertNotEqual(None, entry_1.remove_date)
#        self.assertNotEqual(None, entry_2.remove_date)
#        self.assertEqual(None, entry_3.remove_date)
#        self.assertTrue(entry_2.create_date <= entry_3.create_date)
