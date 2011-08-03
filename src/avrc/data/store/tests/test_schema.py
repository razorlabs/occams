
import unittest
from datetime import datetime

from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

import sqlalchemy.exc

from avrc.data.store import directives
from avrc.data.store import model
from avrc.data.store.interfaces import IManager
from avrc.data.store.interfaces import ISchemaManagerFactory
from avrc.data.store.interfaces import NotCompatibleError
from avrc.data.store.interfaces import MultipleBasesError
from avrc.data.store.schema import SchemaManager

from avrc.data.store.tests.layers import DataBaseLayer


time1 = datetime.now()
time2 = datetime.now()
time3 = datetime.now()
time4 = datetime.now()


def createSchemaInterface(name, bases=[directives.Schema]):
    return InterfaceClass(name, bases=bases)


class SchemaManagerTestCase(unittest.TestCase):
    """ 
    Verifies DataStore compatibility with Zope-style schema  
    """


    layer = DataBaseLayer


    def setUp(self):
        session = self.layer.session

        # Verify versioning
        session.add_all([
            model.Schema(name='Foo', title=u'This is foo',
                create_date=time1, modify_date=time1, remove_date=time2),
            model.Schema(name='Foo', title=u'This is foo',
                create_date=time2, modify_date=time2, remove_date=time4),
            model.Schema(name='Foo', title=u'This is foo',
                create_date=time4, modify_date=time4),


            model.Schema(name='Bar', title=u'This is bar',
                create_date=time1, modify_date=time1),


            model.Schema(name='Baz', title=u'This is baz',
                create_date=time1, modify_date=time1, remove_date=time3),
            model.Schema(name='Baz', title=u'This is baz',
                create_date=time3, modify_date=time3),


            model.Schema(name='Caz', title=u'This is caz',
                create_date=time1, modify_date=time1, remove_date=time2),
            ])

        session.flush()

        self.manager = SchemaManager(session)


    def tearDown(self):
        self.manager = None


    def test_implementation(self):
        self.assertTrue(verifyClass(IManager, SchemaManager))
        self.assertTrue(verifyObject(ISchemaManagerFactory, SchemaManager))


    def test_model(self):
        session = self.layer.session
        schema = model.Schema(name='Sample')
        session.add(schema)
        self.assertRaises(sqlalchemy.exc.IntegrityError, session.flush)
        session.rollback()

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


    def test_lifecycle(self):
        manager = self.manager
        changes = manager.lifecycles('Foo')


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
            session.query(model.Schema)
            .filter(name == model.Schema.name)
            .filter(None != model.Schema.remove_date)
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
            session.query(model.Schema)
            .filter(None == model.Schema.remove_date)
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

        result = session.query(model.Schema).count()
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
        result = session.query(model.Schema).filter_by(name=name).count()
        self.assertEqual(0, result)

        # Purge only the currently active item
        name = 'Baz'
        result = manager.purge(name)
        self.assertEqual(1, result)
        result = session.query(model.Schema).filter_by(name=name).count()
        self.assertEqual(1, result)
        result = (
            session.query(model.Schema)
            .filter_by(name=name, create_date=time1)
            .count()
            )
        self.assertEqual(1, result)

        # Purge an intermediary version
        name = 'Foo'
        result = manager.purge(name, on=time3)
        self.assertEqual(1, result)
        result = (
            session.query(model.Schema)
            .filter_by(name=name, create_date=time1)
            .count()
            )
        self.assertEqual(1, result)
        result = (
            session.query(model.Schema)
            .filter_by(name=name, create_date=time4)
            .count()
            )
        self.assertEqual(1, result)

        # Purge all of name (There's only two of "Foo" left at this point)
        name = 'Foo'
        result = manager.purge(name, ever=True)
        self.assertEqual(2, result)
        result = session.query(model.Schema).filter_by(name=name).count()
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
        self.assertNotEqual(None, directives.title.bind().get(item))
        self.assertNotEqual(None, directives.version.bind().get(item))

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

        # Cannot put something that doesn't extend directive base schema class
        item = InterfaceClass('WillFail')
        directives.title.set(item, u'Will Fail')
        self.assertRaises(NotCompatibleError, manager.put, item.__name__, item)

        # Cannot put something with multiple bases classes
        fail1 = InterfaceClass('Base1')
        fail2 = InterfaceClass('Base2')
        good = createSchemaInterface('FailBase')
        item = InterfaceClass('WillFail', bases=[good, fail1, fail2])
        self.assertRaises(MultipleBasesError, manager.put, item.__name__, item)

        # Put something that has a base class
        base = createSchemaInterface('Base')
        directives.title.set(base, u'This is a base')
        item = createSchemaInterface('ContainsABase', [base])
        directives.title.set(item, u'This is a child')
        manager.put(item.__name__, item)
        # Make sure the ids match properly
        schema = session.query(model.Schema).get(directives.__id__.bind().get(item))
        self.assertEqual(directives.__id__.bind().get(base), schema.base_schema_id)


        # Now put something that's going to be versioned several times


        item = createSchemaInterface('Sample')
        directives.title.set(item, u'Sample Class')
        manager.put(item.__name__, item)

        id_1 = directives.__id__.bind().get(item)
        entry_1 = session.query(model.Schema).get(id_1)
        self.assertEqual(entry_1.name, item.__name__)
        self.assertEqual(entry_1.title, directives.title.bind().get(item))
        self.assertEqual(entry_1.description,
                         directives.description.bind().get(item))
        self.assertEqual(entry_1.create_date,
                         directives.version.bind().get(item))

        # OK, we hate the title, let's change it.
        item = createSchemaInterface('Sample')
        directives.title.set(item, u'New and Improved Sample')
        directives.description.set(item, u'Do more stuff with this.')
        manager.put(item.__name__, item)
        id_2 = directives.__id__.bind().get(item)
        entry_2 = session.query(model.Schema).get(id_2)

        self.assertNotEqual(id_1, id_2)
        self.assertNotEqual(entry_2.title, entry_1.title)
        self.assertNotEqual(entry_2.description, entry_1.description)
        self.assertEqual(entry_2.name, item.__name__)
        self.assertEqual(entry_2.title, directives.title.bind().get(item))
        self.assertEqual(entry_2.description,
                         directives.description.bind().get(item))
        self.assertEqual(entry_2.create_date,
                         directives.version.bind().get(item))

        # Make sure the new version is different from the old.
        self.assertNotEqual(None, entry_1.remove_date)
        self.assertEqual(None, entry_2.remove_date)
        self.assertTrue(entry_1.create_date <= entry_2.create_date)

        # More changes
        item = createSchemaInterface('Sample')
        directives.title.set(item, u'A work in progress')
        directives.description.set(item, u'No sleep till brooklyn.')
        manager.put(item.__name__, item)
        id_3 = directives.__id__.bind().get(item)
        entry_3 = session.query(model.Schema).get(id_3)

        self.assertNotEqual(id_1, id_3)
        self.assertNotEqual(id_2, id_3)
        self.assertNotEqual(entry_3.title, entry_1.title)
        self.assertNotEqual(entry_3.description, entry_1.description)
        self.assertNotEqual(entry_3.title, entry_2.title)
        self.assertNotEqual(entry_3.description, entry_2.description)
        self.assertEqual(entry_3.name, item.__name__)
        self.assertEqual(entry_3.title, directives.title.bind().get(item))
        self.assertEqual(entry_3.description,
                         directives.description.bind().get(item))
        self.assertEqual(entry_3.create_date,
                         directives.version.bind().get(item))


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
