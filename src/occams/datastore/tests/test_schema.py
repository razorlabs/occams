"""
Test case for schema implementations and services
"""

import unittest2 as unittest
from datetime import date

import sqlalchemy.exc
from zope.schema.interfaces import IInt
from zope.schema.interfaces import IDecimal
from zope.schema.interfaces import ITextLine
from zope.schema.interfaces import IText
from zope.schema.interfaces import IBool
from zope.schema.interfaces import IDate
from zope.schema.interfaces import IDatetime
from zope.schema.interfaces import IObject
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import IList
from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore import directives
from occams.datastore.interfaces import IManager
from occams.datastore.interfaces import ISchemaManagerFactory
from occams.datastore.interfaces import ManagerKeyError
from occams.datastore.schema import SchemaManager
from occams.datastore.schema import HierarchyInspector
from occams.datastore.schema import copy
from occams.datastore.schema import schemaToInterface
from occams.datastore.schema import attributeToField
from occams.datastore.schema import interfaceToSchema
from occams.datastore.schema import fieldToAttribute
from occams.datastore.testing import DATASTORE_LAYER


p1 = date(2012, 3, 1)
p2 = date(2012, 4, 1)
p3 = date(2012, 5, 1)
p4 = date(2012, 6, 1)


class SchemaModelTestCase(unittest.TestCase):
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
        self.assertNotEqual(None, schema.create_user)
        self.assertNotEqual(None, schema.modify_date)
        self.assertNotEqual(None, schema.modify_user)

    def testMissingTitle(self):
        session = self.layer['session']
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.add(model.Schema(name='Sample'))
            session.flush()


class SchemaCopyTestCase(unittest.TestCase):
    """
    Verifies that schemata can be "deep" copied as new versions of schemata
    """

    layer = DATASTORE_LAYER

    def testCopy(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = \
            model.Attribute(name='foo', title=u'Enter Foo', type='string', order=0)
        schema['foo'].choices = [
            model.Choice(name='foo', title=u'Foo', value='foo', order=0),
            model.Choice(name='bar', title=u'Bar', value='bar', order=1),
            model.Choice(name='baz', title=u'Baz', value='baz', order=2),
            ]
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Choice).count()
        self.assertEquals(schemaCount, 3, u'Did not find choices')

        schemaCopy = copy(schema)
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
        schema['foo'] = \
            model.Attribute(name='foo', title=u'Enter Foo', type='string', order=0)
        schema['foo'].choices = [
            model.Choice(name='foo', title=u'Foo', value='foo', order=0),
            model.Choice(name='bar', title=u'Bar', value='bar', order=1),
            model.Choice(name='baz', title=u'Baz', value='baz', order=2),
            ]
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Choice).count()
        self.assertEquals(schemaCount, 3, u'Did not find choices')


class HierarchyTestCase(unittest.TestCase):
    """
    Verifies schema hierarchy listing manager
    """

    layer = DATASTORE_LAYER


    def testChildren(self):
        session = self.layer['session']

        create = lambda n, b: model.Schema(
            base_schema=b,
            name=str(n),
            title=unicode(n),
            state='published'
            )

        animal = create('Animal', None)

        bird = create('Bird', animal)
        reptile = create('Reptile', animal)
        mammal = create('Mammal', animal)
        amphibian = create('Amphibian', animal)

        session.add_all([
            create('Hawk', bird),
            create('Chicken', bird),
            create('Goose', bird),
            create('Sparrow', bird),

            create('Snake', reptile),
            create('Lizard', reptile),
            create('Turtle', reptile),

            create('Mouse', mammal),
            create('Dog', mammal),
            create('Cat', mammal),

            create('Frog', amphibian),
            create('Salamander', amphibian),
            ])

        session.flush()

        hierarchy = HierarchyInspector(session)

        names = hierarchy.getChildren('Bird')
        self.assertEqual(4, len(names))

        result = hierarchy.getChildrenNames('Bird')
        names = [n for n in result]
        self.assertEqual(4, len(names))
        self.assertIn('Hawk', names)
        self.assertIn('Hawk', names)
        self.assertIn('Chicken', names)
        self.assertIn('Goose', names)
        self.assertIn('Sparrow', names)

        with self.assertRaises(ManagerKeyError):
            hierarchy.getChildrenNames('Fish')

        names = hierarchy.getChildrenNames('Animal')
        self.assertEqual(12, len(names))


class SchemaManagerTestCase(unittest.TestCase):
    """
    Verifies schema manager
    """

    layer = DATASTORE_LAYER

    def setUp(self):
        session = self.layer['session']

        create = lambda n, s, p: model.Schema(
            name=str(n),
            title=unicode(n),
            state=s,
            publish_date=p
            )

        # Add dummy data with multiple versions of forms in various states
        session.add_all([
            create('Foo', 'published', p1),
            create('Foo', 'published', p2),
            create('Foo', 'published', p3),

            create('Bar', 'published', p1),

            create('Baz', 'published', p1),
            create('Baz', 'published', p3),

            create('Caz', 'published', p2),

            # Manager's only report published schemata
            create('Jaz', 'draft', None),
            ])

        session.flush()

    def testImplementation(self):
        self.assertTrue(verifyClass(IManager, SchemaManager))
        self.assertTrue(verifyObject(ISchemaManagerFactory, SchemaManager))

    def testKeys(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        keys = manager.keys()
        self.assertEqual(4, len(keys))

        # Doesn't do anything anymore
        keys = manager.keys(ever=True)
        self.assertEqual(4, len(keys))

        # Caz should not have existed yet
        keys = manager.keys(on=p1)
        self.assertEqual(3, len(keys))
        self.assertIn('Foo', keys)
        self.assertIn('Bar', keys)
        self.assertIn('Baz', keys)
        self.assertNotIn('Caz', keys)

    def testLifecycle(self):
        session = self.layer['session']
        manager = SchemaManager(session)
        publications = manager.lifecycles('Foo')
        self.assertEqual(3, len(publications))

    def testHas(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        # Foo existed since p1
        self.assertTrue(manager.has('Foo'))
        self.assertTrue(manager.has('Foo', on=p1))
        self.assertTrue(manager.has('Foo', ever=True))

        # Check case-sensitity
        self.assertFalse(manager.has('foo'))
        self.assertFalse(manager.has('foo', ever=False))

        # Stuff was never published
        self.assertFalse(manager.has('Stuff'))

        # Bar, on the other hand, was published
        self.assertTrue(manager.has('Bar'))

        # Caz was published
        self.assertTrue(manager.has('Caz'))
        # Caz was not published as of p1
        self.assertFalse(manager.has('Caz', on=p1))
        self.assertTrue(manager.has('Caz', ever=True))
        # Caz existed happily after p2
        self.assertTrue(manager.has('Caz', on=p2))
        self.assertTrue(manager.has('Caz', on=p3))

    def testRetire(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        # This behavior has been deprecated and should no long function
        with self.assertRaises(NotImplementedError):
            manager.retire('Foo')

    def testRestore(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        # This behavior has been deprecated and should no long function
        with self.assertRaises(NotImplementedError):
            manager.retire('Foo')

    def testPurge(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        # Shouldn't delete any non-existing schemata
        result = manager.purge('NonExisting')
        self.assertEqual(0, result)

        # Purging only affect the most recently published
        name = 'Bar'
        result = manager.purge(name)
        self.assertEqual(1, result, 'Deleted more than one schema')
        result = session.query(model.Schema).filter_by(name=name).count()
        self.assertEqual(0, result, 'Deleted record is still in the database')

        # Purge only the recently published item
        name = 'Baz'
        result = manager.purge(name)
        self.assertEqual(1, result)
        # There should still be one more recored in the database
        result = \
            session.query(model.Schema).filter_by(name=name, publish_date=p1).count()
        self.assertEqual(1, result)

        # Purge an intermediary version
        name = 'Foo'
        result = manager.purge(name, on=p2)
        # Only one as of time p2 should have been removed
        self.assertEqual(1, result)
        # The other two entries should still be in the database
        result = \
            session.query(model.Schema).filter_by(name=name, publish_date=p1).count()
        self.assertEqual(1, result)
        result = \
            session.query(model.Schema).filter_by(name=name, publish_date=p3).count()
        self.assertEqual(1, result)

        # Purge all of name (There's only two of "Foo" left at this point)
        name = 'Foo'
        result = manager.purge(name, ever=True)
        self.assertEqual(2, result)
        # NOW, there should be no entries of Foo
        result = session.query(model.Schema).filter_by(name=name).count()
        self.assertEqual(0, result)

    def testGet(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        # Get something that dosn't exist
        with self.assertRaises(ManagerKeyError):
            name = 'NonExisting'
            item = manager.get(name)

        # Get something that only has one version
        name = 'Bar'
        item = manager.get(name)
        self.assertEqual(name, item.__name__)
        self.assertNotEqual(None, item)

        # Get something that doesn't exist yet
        name = 'Caz'
        with self.assertRaises(ManagerKeyError):
            item = manager.get(name, on=p1)
        # Only works if we specify the version
        item = manager.get(name, on=p3)
        self.assertEqual(name, item.__name__)
        self.assertNotEqual(None, item)

        # Also, can't get anything that hasn't been published yet
        name = 'Jaz'
        with self.assertRaises(ManagerKeyError):
            item = manager.get(name)

    def testPut(self):
        session = self.layer['session']
        manager = SchemaManager(session)


        item = InterfaceClass('Sample', [directives.Schema])
        directives.title.set(item, u'Sample Schema')
        directives.version.set(item, p1)
        newId = manager.put(None, item)
        self.assertTrue(newId > 0)

        # Cannot insert again (as in, cannot insert existing schemata)
        with self.assertRaises(ValueError):
            newId = manager.put(None, item)

        # Suppose we want to insert a another copy of the schema
        item = InterfaceClass('Sample', [directives.Schema])
        directives.title.set(item, u'Sample Schema')
        directives.version.set(item, p2)
        newId = manager.put(None, item)
        self.assertTrue(newId > 0)

        # Needs to be a published form
        item = InterfaceClass('Fail', [directives.Schema])
        directives.title.set(item, u'Sample Schema')
        directives.version.set(item, None)
        with self.assertRaises(ValueError):
            newId = manager.put(None, item)

        # Now try putting something with base schema
        session = self.layer['session']
        manager = SchemaManager(session)
        base = InterfaceClass('Base', bases=[directives.Schema])
        directives.title.set(base, u'Base')
        directives.version.set(base, p1)
        childa = InterfaceClass('ChildA', bases=[base])
        directives.title.set(childa, u'Child A')
        directives.version.set(childa, p3)
        childb = InterfaceClass('ChildB', bases=[base])
        directives.title.set(childb, u'Child B')
        directives.version.set(childb, p4)

        # Inserting Child A should also insert it's base schema
        newId = manager.put(None, childa)
        self.assertTrue(newId > 0)

        # Inserting Child B should reuse the same base schema
        newId = manager.put(None, childb)
        self.assertTrue(newId > 0)

        # Make sure only one base schema was inserted
        count = session.query(model.Schema).filter_by(name='Base').count()
        self.assertEquals(count, 1)

        # Make sure only one child A schema was inserted
        count = session.query(model.Schema).filter_by(name='ChildA').count()
        self.assertEquals(count, 1)

        # Make sure only one child B schema was inserted
        count = session.query(model.Schema).filter_by(name='ChildB').count()
        self.assertEquals(count, 1)


class SchemaToInterfaceTestCase(unittest.TestCase):
    """
    Verifies that a schema can be converted to a Zope-style interface
    """

    layer = DATASTORE_LAYER

    def testBasic(self):
        # Cannot convert something that doesn't extend directive base schema class
        schema = model.Schema(name='Foo', title=u'Foo Schema')
        iface = schemaToInterface(schema)

        # Make sure it's valid
        self.assertTrue(directives.Schema.isEqualOrExtendedBy(iface))

    def testSubClassed(self):
        # Cannot convert something that doesn't extend directive base schema class
        base = model.Schema(name='Base', title=u'Base Schema')
        schema = model.Schema(base_schema=base, name='Foo', title=u'Foo Schema')
        iface = schemaToInterface(schema)

        # Make sure the schema (and it's base schema) are valid
        self.assertTrue(directives.Schema.isEqualOrExtendedBy(iface))
        self.assertTrue(directives.Schema.isEqualOrExtendedBy(iface.__bases__[0]))


class InterfaceToSchemaTestCase(unittest.TestCase):
    """
    Verifies that a Zope style interface can be converted to a SQLAlchemy schema
    """

    layer = DATASTORE_LAYER

    def testNonDirective(self):
        # Cannot convert something that doesn't extend directive base schema class
        item = InterfaceClass('WillFail')
        with self.assertRaises(ValueError):
            interfaceToSchema(item)

    def testMultiBase(self):
        # Cannot convert something with multiple bases classes
        fail1 = InterfaceClass('Base1')
        fail2 = InterfaceClass('Base2')
        # Shouldn't work even if one of the schema is properly structured
        good = InterfaceClass('FailBase', bases=[directives.Schema])
        item = InterfaceClass('WillFail', bases=[good, fail1, fail2])
        with self.assertRaises(ValueError):
            interfaceToSchema(item)

    def testBasic(self):
        basic = InterfaceClass('Basic', bases=[directives.Schema])
        directives.title.set(basic, u'Basic Schema')
        schema = interfaceToSchema(basic)

        # Should be able to add it to the database with no problems
        session = self.layer['session']
        session.add(schema)
        session.flush()

    def testSubClassed(self):
        # Convert something that has a base class
        base = InterfaceClass('Base', bases=[directives.Schema])
        directives.title.set(base, u'This is a base')
        item = InterfaceClass('ContainsABase', bases=[base])
        directives.title.set(item, u'This is a child')
        schema = interfaceToSchema(item)

        # Should be able to add it to the database with no problems
        session = self.layer['session']
        session.add(schema)
        session.flush()


class AttributeToFieldTestCase(unittest.TestCase):
    """
    Verifies that a SQLAlchemy attribute can be converted to a Zope-style field
    """

    layer = DATASTORE_LAYER

    def testBasic(self):
        types = dict(
            boolean=IBool,
            integer=IInt,
            decimal=IDecimal,
            string=ITextLine,
            text=IText,
            date=IDate,
            datetime=IDatetime
            )

        for name, itype in types.iteritems():
            schema = model.Schema(name='Foo', title=u'Foo')

            # Test as basic types
            schema['foo'] = model.Attribute(title=u'', type=name, order=0)
            field = attributeToField(schema['foo'])
            self.assertTrue(itype.providedBy(field))

            # Test as a collection of the type
            schema['foo'] = \
                model.Attribute(title=u'', type=name, is_collection=True, order=0)
            field = attributeToField(schema['foo'])
            self.assertTrue(IList.providedBy(field))
            self.assertTrue(itype.providedBy(field.value_type))

    def testChoices(self):
        pass

    def testObject(self):
        pass


class FieldToAttributeTestCase(unittest.TestCase):
    """
    Verifies that a Zope style field can be converted to a SQLAlchemy attribute
    """

    layer = DATASTORE_LAYER
#
#    def testInteger(self):
#        self.fail()
#
#    def testDecimal(self):
#        self.fail()
#
#    def testBoolean(self):
#        self.fail()
#
#    def testDatetime(self):
#        self.fail()
#
#    def testDate(self):
#        self.fail()
#
#    def testObject(self):
#        self.fail()
#
#    def testString(self):
#        self.fail()
#
#    def testText(self):
#        self.fail()
