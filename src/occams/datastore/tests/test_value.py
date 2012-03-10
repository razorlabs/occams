
import unittest2 as unittest
from datetime import datetime

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore.interfaces import IValueManagerFactory
from occams.datastore.interfaces import IManager
from occams.datastore.interfaces import PropertyNotDefinedError
from occams.datastore.storage import ValueManager
from occams.datastore.storage import SchemaManager
from occams.datastore.storage import ObjectFactory

from occams.datastore.testing import DATABASE_LAYER


time1 = datetime.now()
time2 = datetime.now()
time3 = datetime.now()
time4 = datetime.now()


class ValueManagerTestCase(unittest.TestCase):
    """ 
    Verifies the modification of values
    """


    layer = DATABASE_LAYER


    def setUp(self):
        session = self.session = self.layer['session']
        schema = model.Schema(name='Schema', title=u'Test Schema')
        entity = model.Entity(schema=schema, name='Sample', title=u'Sample')
        # We're not versioning attributes, only data in this test case
        foo = model.Attribute(
            schema=schema, type='string', name='foo', title=u'Foo', order=1
            )
        bar = model.Attribute(
            schema=schema, type='integer', name='bar', title=u'Bar', order=2
            )

        caz = model.Attribute(
            schema=schema, type='datetime', name='caz', title=u'Caz', order=3
            )

        empty = model.Attribute(
                schema=schema, type='string', name='empty', title=u'Empty', order=4
            )
        session.add(empty)

        red = model.Choice(name='red', title=u'Red', value=u'red', order=1)
        green = model.Choice(name='green', title=u'Green', value=u'green', order=2)
        blue = model.Choice(name='blue', title=u'Blue', value=u'blue', order=3)
        purple = model.Choice(name='purple', title=u'Purple', value=u'purple', order=4)
        yellow = model.Choice(name='yellow', title=u'Yellow', value=u'yellow', order=5)

        liz = model.Attribute(
            schema=schema, type='string', name='liz', title=u'Liz', order=5,
            is_collection=True, choices=dict(
                red=red,
                green=green,
                blue=blue,
                purple=purple,
                yellow=yellow
                )
            )

        session.add_all([
            # Foo's values
            model.ValueString(
                entity=entity, attribute=foo, value=u'Hi!!!',
                create_date=time1, modify_date=time2, remove_date=time2,
                ),
            model.ValueString(
                entity=entity, attribute=foo, value=u'Never mind!!',
                create_date=time2, modify_date=time4, remove_date=time4,
                ),
            model.ValueString(
                entity=entity, attribute=foo, value=u'Hello world!!',
                create_date=time4, modify_date=time4,
                ),

            # Bar's values
            model.ValueInteger(
                entity=entity, attribute=bar, value=42,
                create_date=time2, modify_date=time3, remove_date=time3,
                ),
            model.ValueInteger(
                entity=entity, attribute=bar, value=420,
                create_date=time3, modify_date=time3,
                ),

            # Caz's values
            model.ValueDatetime(
                entity=entity, attribute=caz, value=datetime.now(),
                create_date=time1, modify_date=time1, remove_date=time2,
                ),

            # Liz's values
            model.ValueString(
                entity=entity, attribute=liz, choice=red, value=u'red',
                create_date=time1, modify_date=time2, remove_date=time2,
                ),
            model.ValueString(
                entity=entity, attribute=liz, choice=blue, value=u'blue',
                create_date=time1, modify_date=time2, remove_date=time2,
                ),
            model.ValueString(
                entity=entity, attribute=liz, choice=purple, value=u'purple',
                create_date=time2, modify_date=time2,
                ),
            model.ValueString(
                entity=entity, attribute=liz, choice=blue, value=u'blue',
                create_date=time2, modify_date=time2,
                ),
            model.ValueString(
                entity=entity, attribute=liz, choice=green, value=u'green',
                create_date=time2, modify_date=time2,
                ),
            ])

        session.flush()

        self.entity = entity
        self.foo_attr = foo
        self.bar_attr = bar
        self.baz_attr = caz
        self.liz_attr = liz
        self.manager = ValueManager(entity)


    def tearDown(self):
        self.entity = None
        self.foo_attr = None
        self.bar_attr = None
        self.baz_attr = None
        self.liz_attr = None
        self.manager = None


    def test_implementation(self):
        self.assertTrue(verifyClass(IManager, ValueManager))
        self.assertTrue(verifyObject(IValueManagerFactory, ValueManager))


    def test_keys(self):
        manager = self.manager

        # Haven't assigned anything yet
        keys = manager.keys(on=datetime(1776, 7, 4))
        self.assertEqual(0, len(keys))

        keys = manager.keys()
        self.assertEqual(3, len(keys))
        keys = manager.keys(ever=True)
        self.assertEqual(4, len(keys))

        keys = manager.keys(on=time3)
        self.assertTrue('foo' in keys)
        self.assertTrue('bar' in keys)
        self.assertTrue('liz' in keys)


    def test_has(self):
        manager = self.manager

        self.assertTrue(manager.has('foo'))
        self.assertTrue(manager.has('bar'))
        self.assertTrue(manager.has('foo', on=datetime.now()))
        self.assertTrue(manager.has('foo', ever=True))
        self.assertFalse(manager.has('empty'))
        self.assertFalse(manager.has('empty', ever=False))

    def test_purge(self):
        manager = self.manager
        session = self.manager.session
        bar_attr = self.bar_attr
        foo_attr = self.foo_attr

        # Can't purge anything that doesn't exist
        name = 'empty'
        result = manager.purge(name)
        self.assertEqual(0, result)
        result = manager.purge(name, on=time1)
        self.assertEqual(0, result)
        result = manager.purge(name, on=time2)
        self.assertEqual(0, result)
        result = manager.purge(name, on=time3)
        self.assertEqual(0, result)
        result = manager.purge(name, on=time4)
        self.assertEqual(0, result)
        result = manager.purge(name, ever=True)
        self.assertEqual(0, result)

        # Purge only the currently active item
        name = 'bar'
        result = manager.purge(name)
        self.assertEqual(1, result)
        query = session.query(model.ValueInteger).filter_by(attribute=bar_attr)
        result = query.count()
        self.assertEqual(1, result)
        result = query.filter_by(create_date=time2).count()
        self.assertEqual(1, result)

        # Purge an intermediary version
        name = 'foo'
        query = session.query(model.ValueString).filter_by(attribute=foo_attr)
        result = manager.purge(name, on=time3)
        self.assertEqual(1, result)
        result = query.filter_by(create_date=time1).count()
        self.assertEqual(1, result)
        result = query.filter_by(create_date=time4).count()
        self.assertEqual(1, result)

        # Purge all of name (There's only two of "foo" left at this point)
        name = 'foo'
        result = manager.purge(name, ever=True)
        self.assertEqual(2, result)
        query = session.query(model.ValueString).filter_by(attribute=foo_attr)
        result = query.count()
        self.assertEqual(0, result)


    def test_retire(self):
        manager = self.manager
        session = self.manager.session
        foo_attr = self.foo_attr
        entity = self.entity

        # Can't retire something that doesn't exist
        name = 'empty'
        result = manager.retire(name)
        self.assertEqual(0, result)

        # Can't retire something that's already retired
        name = 'caz'
        result = manager.retire(name)
        self.assertEqual(0, result)

        # Make sure the item is actually retired
        name = 'foo'
        result = manager.retire(name)
        self.assertEqual(1, result)

        result = (
            session.query(model.ValueString)
            .filter_by(entity=entity, attribute=foo_attr)
            .filter(None != model.ValueString.remove_date)
            .all()
            )

        self.assertEqual(3, len(result))

        # Retire the list
        name = 'liz'
        result = manager.retire(name)
        # The list has three items, so it should have retired three values
        self.assertEqual(3, result)


    def test_restore(self):
        manager = self.manager
        session = self.manager.session
        foo_attr = self.foo_attr
        liz_attr = self.liz_attr

        # Can't restore something that doesn't exist
        name = 'empty'
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Can't restore something that isn't retired
        name = 'bar'
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Make sure only the most recent entry is restored
        name = 'caz'
        result = manager.restore(name)
        self.assertEqual(1, result)
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Try to restore something that's been removed a couple of times,
        # should only work on the most recently created
        name = 'foo'
        result = manager.restore(name)
        self.assertEqual(0, result)
        # Simulate retirement
        result = (
            session.query(model.ValueString)
            .filter_by(attribute=foo_attr, remove_date=None)
            .update(dict(remove_date=model.NOW), 'fetch')
            )
        # Should only restore once (the most recent one)
        result = manager.restore(name)
        self.assertEqual(1, result)
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Now do the same test, but for a list this time...
        name = 'liz'
        result = manager.restore(name)
        self.assertEqual(0, result)
        # Simulate retirement
        query = (
            session.query(model.ValueString)
            .filter_by(attribute=liz_attr, remove_date=None)
            )
        result = query.update(dict(remove_date=model.NOW), 'fetch')
        # Should only restore once (for all three values)
        result = manager.restore(name)
        self.assertEqual(3, result)
        result = manager.restore(name)
        self.assertEqual(0, result)


    def test_get(self):
        manager = self.manager

        # Get something that dosn't exist
        name = 'empty'
        result = manager.get(name)
        self.assertEqual(None, result)

        # Get something that only has one version
        name = 'foo'
        result = manager.get(name)
        self.assertEqual(u'Hello world!!', result)

        # Get something that's been removed
        name = 'caz'
        result = manager.get(name)
        self.assertEqual(None, result)
        # Only works if we specify the version
        result = manager.get(name, on=time1)
        self.assertNotEqual(None, result)


    def test_put(self):
        manager = self.manager
        session = self.manager.session
        entity = self.entity

        # Cannot put unsupported type
        name = 'will_fail'
        self.assertRaises(PropertyNotDefinedError, manager.put, name, u'blah')

        # Now put something that's going to be versioned several times
        # First, let's manually create a property

        attribute = model.Attribute(
            schema=entity.schema,
            type='string', name='sample', title=u'Sample', order=6,
            )
        session.add(attribute)
        session.flush()

        id_1 = manager.put(attribute.name, u'Test')
        entry_1 = session.query(model.ValueString).get(id_1)
        self.assertNotEqual(None, id_1)
        self.assertNotEqual(None, entry_1)
        self.assertEqual(None, entry_1.remove_date)

        # OK, we hate the title, let's change it.
        id_2 = manager.put(attribute.name, u'Another Test')
        entry_2 = session.query(model.ValueString).get(id_2)
        self.assertNotEqual(id_1, id_2)
        self.assertNotEqual(entry_2.value, entry_1.value)
        # Make sure the new version is different from the old.
        self.assertNotEqual(None, entry_1.remove_date)
        self.assertEqual(None, entry_2.remove_date)
        self.assertTrue(entry_1.create_date <= entry_2.create_date)
        # More changes
        id_3 = manager.put(attribute.name, u'Weeee!')
        entry_3 = session.query(model.ValueString).get(id_3)
        self.assertNotEqual(id_1, id_3)
        self.assertNotEqual(id_2, id_3)
        self.assertNotEqual(entry_3.value, entry_2.value)
        self.assertNotEqual(None, entry_1.remove_date)
        self.assertNotEqual(None, entry_2.remove_date)
        self.assertEqual(None, entry_3.remove_date)
        self.assertTrue(entry_2.create_date <= entry_3.create_date)

