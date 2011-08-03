
import unittest
from datetime import datetime

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from avrc.data.store import model
from avrc.data.store.interfaces import IEntityManagerFactory
from avrc.data.store.interfaces import IManager
from avrc.data.store.storage import EntityManager
from avrc.data.store.storage import ObjectFactory
from avrc.data.store.schema import SchemaManager

from avrc.data.store.tests.layers import DataBaseLayer


time1 = datetime.now()
time2 = datetime.now()
time3 = datetime.now()
time4 = datetime.now()

class EntityManagerTestCase(unittest.TestCase):
    """ 
    Verifies DataStore Entity storage
    """

    layer = DataBaseLayer


    def setUp(self):
        session = self.layer.session

        schema = model.Schema(name='Foo', title=u'Type Foo', create_date=time1)
        session.add(schema)

        session.add_all([
            model.Entity(
                schema=schema,
                name='Foo', title=u'This is foo',
                create_date=time1, modify_date=time1, remove_date=time2
                ),
            model.Entity(
                schema=schema,
                name='Foo', title=u'This is foo',
                create_date=time2, modify_date=time2, remove_date=time4
                ),
            model.Entity(
                schema=schema,
                name='Foo', title=u'This is foo',
                create_date=time4, modify_date=time4
                ),


            model.Entity(
                schema=schema,
                name='Bar', title=u'This is bar',
                create_date=time1, modify_date=time1
                ),


            model.Entity(
                schema=schema,
                name='Baz', title=u'This is baz',
                create_date=time1, modify_date=time1, remove_date=time3
                ),

            model.Entity(
                schema=schema,
                name='Baz', title=u'This is baz',
                create_date=time3, modify_date=time3
                ),


            model.Entity(
                schema=schema,
                name='Caz', title=u'This is caz',
                create_date=time1, modify_date=time1, remove_date=time2
                ),
            ])

        session.flush()

        self.schema = schema
        self.iface = SchemaManager(session).get(schema.name, on=schema.create_date)
        self.manager = EntityManager(session)


    def tearDown(self):
        self.manager = None


    def test_implementation(self):
        self.assertTrue(verifyClass(IManager, EntityManager))
        self.assertTrue(verifyObject(IEntityManagerFactory, EntityManager))


    def test_keys(self):
        manager = self.manager

        keys = manager.keys()
        self.assertEqual(3, len(keys))

        keys = manager.keys(ever=True)
        self.assertEqual(7, len(keys))

        keys = manager.keys(on=time2)
        self.assertEqual(3, len(keys))
        self.assertTrue('Foo' in keys)
        self.assertTrue('Bar' in keys)
        self.assertTrue('Baz' in keys)


    def test_has(self):
        manager = self.manager

        self.assertTrue(manager.has('Foo'))
        self.assertTrue(manager.has('Foo', on=datetime.now()))
        self.assertTrue(manager.has('Foo', ever=True))
        self.assertFalse(manager.has('foo'))
        self.assertFalse(manager.has('foo', ever=False))

        self.assertFalse(manager.has('Stuff'))
        self.assertTrue(manager.has('Bar'))

        self.assertFalse(manager.has('Caz'))
        self.assertFalse(manager.has('Caz', on=datetime.now()))
        self.assertTrue(manager.has('Caz', ever=True))
        self.assertTrue(manager.has('Caz', on=time1))
        self.assertFalse(manager.has('Caz', on=time2))
        self.assertFalse(manager.has('Caz', on=time3))


    def test_retire(self):
        manager = self.manager
        session = self.manager.session

        # Can't retire something that doesn't exist
        name = 'NonExisting'
        result = manager.retire(name)
        self.assertEqual(0, result)

        # Can't retire something that's already retired
        name = 'Caz'
        result = manager.retire(name)
        self.assertEqual(0, result)

        # Make sure the item is actually retired
        name = 'Foo'
        result = manager.retire(name)
        self.assertEqual(1, result)

        result = (
            session.query(model.Entity)
            .filter(name == model.Entity.name)
            .filter(None != model.Entity.remove_date)
            .all()
            )

        self.assertEqual(3, len(result))


    def test_restore(self):
        manager = self.manager
        session = self.manager.session

        # Can't restore something that doesn't exist
        name = 'NonExisting'
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Can't restore something that isn't retired
        name = 'Bar'
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Make sure only the most recent entry is restored
        name = 'Caz'
        result = manager.restore(name)
        self.assertEqual(1, result)
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Try to restore something that's been removed a couple of times,
        # should only work on the most recently created
        name = 'Foo'
        result = manager.restore(name)
        self.assertEqual(0, result)

        # Simulate retirement
        result = (
            session.query(model.Entity)
            .filter(None == model.Entity.remove_date)
            .update(dict(remove_date=model.NOW), 'fetch')
            )

        # Should only restore once
        result = manager.restore(name)
        self.assertEqual(1, result)
        result = manager.restore(name)
        self.assertEqual(0, result)


    def test_purge(self):
        manager = self.manager
        session = self.manager.session

        result = session.query(model.Entity).count()
        self.assertEqual(7, result)

        # Can't purge anything that doesn't exist
        name = 'NonExisting'
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

        # Purge single items
        name = 'Bar'
        result = manager.purge(name)
        self.assertEqual(1, result)
        result = session.query(model.Entity).filter_by(name=name).count()
        self.assertEqual(0, result)

        # Purge only the currently active item
        name = 'Baz'
        result = manager.purge(name)
        self.assertEqual(1, result)
        result = session.query(model.Entity).filter_by(name=name).count()
        self.assertEqual(1, result)
        result = (
            session.query(model.Entity)
            .filter_by(name=name, create_date=time1)
            .count()
            )
        self.assertEqual(1, result)

        # Purge an intermediary version
        name = 'Foo'
        result = manager.purge(name, on=time3)
        self.assertEqual(1, result)
        result = (
            session.query(model.Entity)
            .filter_by(name=name, create_date=time1)
            .count()
            )
        self.assertEqual(1, result)
        result = (
            session.query(model.Entity)
            .filter_by(name=name, create_date=time4)
            .count()
            )
        self.assertEqual(1, result)

        # Purge all of name (There's only two of "Foo" left at this point)
        name = 'Foo'
        result = manager.purge(name, ever=True)
        self.assertEqual(2, result)
        result = session.query(model.Entity).filter_by(name=name).count()
        self.assertEqual(0, result)


    def test_get(self):
        manager = self.manager

        # Get something that dosn't exist
        name = 'NonExisting'
        item = manager.get(name)
        self.assertEqual(None, item)

        # Get something that only has one version
        name = 'Foo'
        item = manager.get(name)
        self.assertEqual(name, item.__name__)
        self.assertNotEqual(None, item)
        self.assertNotEqual(None, item.__title__)
        self.assertNotEqual(None, item.__version__)

        # Get something that's been removed
        name = 'Caz'
        item = manager.get(name)
        self.assertEqual(None, item)

        # Only works if we specify the version
        item = manager.get(name, on=time1)
        self.assertNotEqual(None, item)


    def test_put(self):
        manager = self.manager
        session = self.manager.session
        iface = self.iface

        item = ObjectFactory(iface)
        manager.put(item.__name__, item)



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
