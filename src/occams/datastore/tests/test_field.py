
import unittest2 as unittest
from datetime import datetime

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from zope.interface.interface import InterfaceClass
import zope.schema
from zope.schema.interfaces import WrongType

import sqlalchemy.exc

from occams.datastore import directives
from occams.datastore import model
from occams.datastore.interfaces import IManager
from occams.datastore.interfaces import IFieldManagerFactory
from occams.datastore.interfaces import TypeNotSupportedError
from occams.datastore.schema import FieldManager

from occams.datastore.testing import DATABASE_LAYER


time1 = datetime.now()
time2 = datetime.now()
time3 = datetime.now()
time4 = datetime.now()


class FieldManagementTestCase(unittest.TestCase):
    """
    Verifies DataStore compatibility with Zope-style fields
    """

    layer = DATABASE_LAYER


    def setUp(self):

        self.session = self.layer['session']

        schema = model.Schema(
            name='Sample',
            title=u'Sample Form',
            create_date=time1,
            modify_date=time1,
            )

        self.session.add_all([
            schema,

            model.Schema(
                name='Evil',
                title=u'Pure Evil',
                description=u'Just to throw things off.',
                create_date=time1,
                modify_date=time1,
                ),

            model.Attribute(
                schema=schema, type='string', order=1,
                name='Foo', title=u'This is foo',
                create_date=time1, modify_date=time1, remove_date=time2
                ),
            model.Attribute(
                schema=schema, type='string', order=1,
                name='Foo', title=u'This is foo',
                create_date=time2, modify_date=time2, remove_date=time4
                ),
            model.Attribute(
                schema=schema, type='string', order=1,
                name='Foo', title=u'This is foo',
                create_date=time4, modify_date=time4
                ),


            model.Attribute(
                schema=schema, type='string', order=2,
                name='Bar', title=u'This is bar',
                create_date=time1, modify_date=time1
                ),


            model.Attribute(
                schema=schema, type='string', order=3,
                name='Baz', title=u'This is baz',
                create_date=time1, modify_date=time1, remove_date=time3
                ),

            model.Attribute(
                schema=schema, type='string', order=3,
                name='Baz', title=u'This is baz',
                create_date=time3, modify_date=time3
                ),


            model.Attribute(
                schema=schema, type='string', order=4,
                name='Caz', title=u'This is caz',
                create_date=time1, modify_date=time1, remove_date=time2
                ),
            ])

        self.session.flush()

        self.manager = FieldManager(schema)


    def tearDown(self):
        self.manager = None


    def test_implementation(self):
        self.assertTrue(verifyClass(IManager, FieldManager))
        self.assertTrue(verifyObject(IFieldManagerFactory, FieldManager))


    def test_model(self):
        session = self.session

        attribute = model.Attribute(name='foo')
        session.add(attribute)
        self.assertRaises(sqlalchemy.exc.IntegrityError, session.flush)
        session.rollback()

        attribute = model.Attribute(name='foo', title=u'Foo')
        session.add(attribute)
        self.assertRaises(sqlalchemy.exc.IntegrityError, session.flush)
        session.rollback()

        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        session.add(attribute)
        self.assertRaises(sqlalchemy.exc.IntegrityError, session.flush)
        session.rollback()

        schema = model.Schema(name='Sample', title=u'Sample')
        attribute = model.Attribute(schema=schema, name='foo', title=u'Foo',
                                    type='string', order=1)
        session.add(attribute)
        session.flush()

        # Check that all properties are working properly
        self.assertEqual(None, attribute.description)
        self.assertEqual(False, attribute.is_collection)
        self.assertEqual(False, attribute.is_required)
        self.assertEqual(False, attribute.is_readonly)
        self.assertEqual(None, attribute.is_inline_object)
        self.assertEqual(None, attribute.object_schema_id)
        self.assertEqual(None, attribute.url_template)
        self.assertEqual(None, attribute.min)
        self.assertEqual(None, attribute.max)
        self.assertEqual(None, attribute.default)
        self.assertEqual(None, attribute.validator)
        self.assertEqual(None, attribute.widget)
        self.assertNotEqual(None, attribute.order)
        self.assertNotEqual(None, attribute.create_date)
        self.assertNotEqual(None, attribute.modify_date)
        self.assertEqual(None, attribute.remove_date)


    def test_keys(self):
        manager = self.manager

        keys = manager.keys()
        self.assertEqual(3, len(keys))

        keys = manager.keys(ever=True)
        self.assertEqual(7, len(keys))

        keys = manager.keys(on=time2)
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
            session.query(model.Attribute)
            .filter(name == model.Attribute.name)
            .filter(None != model.Attribute.remove_date)
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
            session.query(model.Attribute)
            .filter(None == model.Attribute.remove_date)
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

        result = session.query(model.Attribute).count()
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
        result = session.query(model.Attribute).filter_by(name=name).count()
        self.assertEqual(0, result)

        # Purge only the currently active item
        name = 'Baz'
        result = manager.purge(name)
        self.assertEqual(1, result)
        result = session.query(model.Attribute).filter_by(name=name).count()
        self.assertEqual(1, result)
        result = (
            session.query(model.Attribute)
            .filter_by(name=name, create_date=time1)
            .count()
            )
        self.assertEqual(1, result)

        # Purge an intermediary version
        name = 'Foo'
        result = manager.purge(name, on=time3)
        self.assertEqual(1, result)
        result = (
            session.query(model.Attribute)
            .filter_by(name=name, create_date=time1)
            .count()
            )
        self.assertEqual(1, result)
        result = (
            session.query(model.Attribute)
            .filter_by(name=name, create_date=time4)
            .count()
            )
        self.assertEqual(1, result)

        # Purge all of name (There's only two of "Foo" left at this point)
        name = 'Foo'
        result = manager.purge(name, ever=True)
        self.assertEqual(2, result)
        result = session.query(model.Attribute).filter_by(name=name).count()
        self.assertEqual(0, result)


    def test_get(self):
        manager = self.manager

        # Get something that dosn't exist
        name = 'NonExisting'
        field = manager.get(name)
        self.assertEqual(None, field)

        # Get something that only has one version
        name = 'Foo'
        field = manager.get(name)
        self.assertNotEqual(None, field)
        self.assertEqual(name, field.__name__)
        self.assertNotEqual(None, field.title)
        self.assertNotEqual(None, directives.__id__.bind().get(field))
        self.assertEqual(time4, directives.version.bind().get(field))

        # Get something that's been removed
        name = 'Caz'
        field = manager.get(name)
        self.assertEqual(None, field)
        # Only works if we specify the version
        field = manager.get(name, on=time1)
        self.assertNotEqual(None, field)
        self.assertEqual(time1, directives.version.bind().get(field))


    def test_put(self):
        manager = self.manager
        session = self.manager.session

        # Cannot put unsupported type
        name = 'WillFail'
        item = zope.schema.URI(__name__=name, title=unicode(name))
        directives.title.set(item, u'Will Fail')
        self.assertRaises(TypeNotSupportedError, manager.put, item.__name__, item)


        # Now put something that's going to be versioned several times


        item = zope.schema.Choice(
            __name__='Sample',
            title=u'Sample',
            values=[u'bad', u'good']
            )
        directives.type.set(item, 'integer')
        self.assertRaises(WrongType, manager.put, item.__name__, item)
        directives.type.set(item, 'string')

        manager.put(item.__name__, item)
        id_1 = directives.__id__.bind().get(item)
        entry_1 = session.query(model.Attribute).get(id_1)
        self.assertEqual(entry_1.name, item.__name__)
        self.assertEqual(entry_1.title, item.title)
        self.assertEqual(entry_1.description, item.description)
        self.assertEqual(entry_1.create_date, directives.version.bind().get(item))
        self.assertEqual(2, len(entry_1.choices))

        # OK, we hate the title, let's change it.
        item = zope.schema.Choice(
            __name__='Sample',
            title=u'New and Improved Sample',
            description=u'Do more stuff with this.',
            values=[u'bad', u'ok', u'good']
            )
        directives.type.set(item, 'string')
        manager.put(item.__name__, item)
        id_2 = directives.__id__.bind().get(item)
        entry_2 = session.query(model.Attribute).get(id_2)
        self.assertNotEqual(id_1, id_2)
        self.assertNotEqual(entry_2.title, entry_1.title)
        self.assertNotEqual(entry_2.description, entry_1.description)
        self.assertEqual(entry_2.name, item.__name__)
        self.assertEqual(entry_2.title, item.title)
        self.assertEqual(entry_2.description, item.description)
        self.assertEqual(entry_2.create_date, directives.version.bind().get(item))
        self.assertEqual(3, len(entry_2.choices))
        # Make sure the new version is different from the old.
        self.assertNotEqual(None, entry_1.remove_date)
        self.assertEqual(None, entry_2.remove_date)
        self.assertTrue(entry_1.create_date <= entry_2.create_date)

        # More changes
        item = zope.schema.Choice(
            __name__='Sample',
            title=u'A work in progress',
            description=u'Another dimension.',
            values=[u'really bad', u'bad', u'ok', u'good', u'really good']
            )
        directives.type.set(item, 'string')
        manager.put(item.__name__, item)
        id_3 = directives.__id__.bind().get(item)
        entry_3 = session.query(model.Attribute).get(id_3)
        self.assertNotEqual(id_1, id_3)
        self.assertNotEqual(id_2, id_3)
        self.assertNotEqual(entry_3.title, entry_1.title)
        self.assertNotEqual(entry_3.description, entry_1.description)
        self.assertNotEqual(entry_3.title, entry_2.title)
        self.assertNotEqual(entry_3.description, entry_2.description)
        self.assertEqual(entry_3.name, item.__name__)
        self.assertEqual(entry_3.title, item.title)
        self.assertEqual(entry_3.description, item.description)
        self.assertEqual(entry_3.create_date, directives.version.bind().get(item))
        self.assertEqual(5, len(entry_3.choices))
