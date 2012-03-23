"""
Test case for schema implementations and services
"""

import unittest2 as unittest
from datetime import date
from datetime import datetime
from decimal import Decimal

import sqlalchemy.exc
import zope.schema
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

    def testDefaultPublishDate(self):
        # Make sure the system can auto-assign a publish date to schemata
        # that are marked as published
        session = self.layer['session']
        schema = model.Schema(name='Sample', title=u'Sample', state='published')
        session.add(schema)
        session.flush()
        self.assertNotEqual(schema.publish_date, None)

    def testMissingTitle(self):
        session = self.layer['session']
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.add(model.Schema(name='Sample'))
            session.flush()

    def testDelete(self):
        # Test deleting an attribute via dict-like API
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(title=u'foo', type='string', order=0)
        session.add(schema)
        session.flush()
        # The attribute should have been committed
        result = session.query(model.Attribute).filter_by(name='foo').count()
        self.assertEqual(result, 1)
        # Delete it like you would a dictionary
        del schema['foo']
        session.flush()
        # Should have been deleted
        result = session.query(model.Attribute).filter_by(name='foo').count()
        self.assertEqual(result, 0)

    def testContains(self):
        # Test dict-like containment
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        self.assertNotIn('foo', schema)
        schema['foo'] = model.Attribute(title=u'foo', type='string', order=0)
        session.flush()
        self.assertIn('foo', schema)
        self.assertNotIn('bar', schema)

    def testKeys(self):
        # Test dict-like containment
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        keys = schema.keys()
        self.assertEqual(len(keys), 0)
        schema['foo'] = model.Attribute(title=u'foo', type='string', order=0)
        schema['bar'] = model.Attribute(title=u'bar', type='string', order=1)
        session.flush()
        keys = schema.keys()
        self.assertEqual(len(keys), 2)
        self.assertIn('foo', keys)
        self.assertIn('bar', keys)
        self.assertNotIn('baz', keys)

    def testValues(self):
        # Make sure we can enumerate the attributes in the schema
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        values = schema.values()
        self.assertEqual(len(values), 0)
        schema['foo'] = model.Attribute(title=u'foo', type='string', order=0)
        session.flush()
        values = schema.values()
        self.assertEqual(len(values), 1)
        attribute = values[0]
        self.assertEqual(schema, attribute.schema)
        self.assertEqual(attribute.name, 'foo')

    def testItems(self):
        # Make sure we can enumerate the key/value pairs of the schema
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        items = schema.items()
        self.assertEqual(len(items), 0)
        schema['foo'] = model.Attribute(title=u'foo', type='string', order=0)
        session.flush()
        items = schema.items()
        self.assertEqual(len(items), 1)
        name, attribute = items[0]
        self.assertEqual(schema, attribute.schema)
        self.assertEqual(attribute.name, 'foo')
        self.assertEqual(attribute.name, name)


class SchemaCopyTestCase(unittest.TestCase):
    """
    Verifies that schemata can be "deep" copied as new versions of schemata
    """

    layer = DATASTORE_LAYER

    def testBasic(self):
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

    def testWithSubObject(self):
        session = self.layer['session']
        schema = model.Schema(
            name='Foo',
            title=u'Foo',
            attributes=dict(
                bar=model.Attribute(
                    name='bar',
                    title=u'Bar',
                    type='object',
                    order=0,
                    object_schema=model.Schema(
                        name='Bar',
                        title=u'Bar',
                        is_inline=True,
                        )
                    )
                )
            )

        session.add(schema)
        session.flush()

        schemaCopy = copy(schema)
        session.add(schemaCopy)
        session.flush()

        self.assertNotEqual(schema, schemaCopy)
        self.assertEqual(schema.name, schemaCopy.name)
        self.assertNotEqual(schema['bar'].object_schema, schemaCopy['bar'].object_schema)


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

    def setUp(self):
        session = self.layer['session']

        create = lambda n, b: model.Schema(
            base_schema=b,
            name=str(n),
            title=unicode(n),
            state='published',
            publish_date=p3,
            )

        # Create some dummy data
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

    def testDistantRoot(self):
        # Make sure we can get the leaf nodes from higher up the family tree
        # (such as the root)
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)
        children = hierarchy.getChildren('Animal')
        self.assertEqual(len(children), 12)

    def testChildren(self):
        # Get the actual objects
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)
        children = hierarchy.getChildren('Bird')
        self.assertEqual(4, len(children))

        self.assertTrue(directives.Schema.isEqualOrExtendedBy(children[0]))
        self.assertTrue(directives.Schema.isEqualOrExtendedBy(children[1]))
        self.assertTrue(directives.Schema.isEqualOrExtendedBy(children[2]))
        self.assertTrue(directives.Schema.isEqualOrExtendedBy(children[3]))

    def testChildrenNames(self):
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)
        result = hierarchy.getChildrenNames('Bird')
        names = [n for n in result]
        self.assertEqual(4, len(names))
        self.assertIn('Hawk', names)
        self.assertIn('Hawk', names)
        self.assertIn('Chicken', names)
        self.assertIn('Goose', names)
        self.assertIn('Sparrow', names)

    def testNonExistent(self):
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)

        with self.assertRaises(ManagerKeyError):
            hierarchy.getChildren('Fish')

        with self.assertRaises(ManagerKeyError):
            hierarchy.getChildrenNames('Fish')

    def testVersioned(self):
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)

        # Shouldn't be able to get children that have not been published
        # as of the given date

        with self.assertRaises(ManagerKeyError):
            children = hierarchy.getChildren('Animal', on=p1)

        with self.assertRaises(ManagerKeyError):
            names = hierarchy.getChildrenNames('Animal', on=p1)


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
            manager.restore('Foo')

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

    def testWithAttributes(self):
        # Make sure that a schema with attributes can be converted
        iface = InterfaceClass(
            name='Foo',
            bases=[directives.Schema],
            attrs=dict(foo=zope.schema.TextLine(__name__='foo', title=u''))
            )

        schema = interfaceToSchema(iface)
        self.assertIn('foo', schema)


class AttributeToFieldTestCase(unittest.TestCase):
    """
    Verifies that a SQLAlchemy attribute can be converted to a Zope-style field
    """

    layer = DATASTORE_LAYER

    def testBasic(self):
        types = dict(
            boolean=(IBool, [True, False]),
            integer=(IInt, [1, 7]),
            decimal=(IDecimal, [Decimal('3.4'), Decimal('4.5')]),
            string=(ITextLine, ['foo', 'bar']),
            text=(IText, ['Some\nFoo', 'Some\nBar']),
            date=(IDate, [date(2011, 01, 03), date(2012, 02, 19)]),
            datetime=(IDatetime, [datetime(2011, 01, 03), datetime(2012, 02, 19)]),
            )

        for (name, (itype, choices)) in types.iteritems():
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

            # Test with choices
            schema['foo'] = \
                model.Attribute(title=u'', type=name, order=0)
            for choice in choices:
                schema['foo'].choices.append(model.Choice(
                    name=str(choice),
                    title=unicode(choice),
                    value=choice
                    ))
            field = attributeToField(schema['foo'])
            self.assertTrue(IChoice.providedBy(field))
            self.assertEqual(directives.type.bind().get(field), name)

            # Test with choices AND as a collection
            schema['foo'] = \
                model.Attribute(title=u'', type=name, is_collection=True, order=0)
            for choice in choices:
                schema['foo'].choices.append(model.Choice(
                    name=str(choice),
                    title=unicode(choice),
                    value=choice
                    ))
            field = attributeToField(schema['foo'])
            self.assertTrue(IList.providedBy(field))
            self.assertTrue(IChoice.providedBy(field.value_type))
            self.assertEqual(directives.type.bind().get(field), name)

    def testObject(self):
        # Test as a basic sub-object
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(
            title=u'',
            order=0,
            type='object',
            object_schema=model.Schema(name='Bar', title=u'Bar', is_inline=True)
            )
        field = attributeToField(schema['foo'])
        self.assertTrue(IObject.providedBy(field))
        self.assertEqual(directives.type.bind().get(field), 'object')

        # Test as a collection
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(
            title=u'',
            order=0,
            type='object',
            is_collection=True,
            object_schema=model.Schema(name='Bar', title=u'Bar', is_inline=True)
            )
        field = attributeToField(schema['foo'])
        self.assertTrue(IList.providedBy(field))
        self.assertTrue(IObject.providedBy(field.value_type))
        self.assertEqual(directives.type.bind().get(field), 'object')


class FieldToAttributeTestCase(unittest.TestCase):
    """
    Verifies that a Zope style field can be converted to a SQLAlchemy attribute
    """

    layer = DATASTORE_LAYER

    def testBasic(self):
        types = dict(
            boolean=(zope.schema.Bool, [True, False]),
            integer=(zope.schema.Int, [1, 7]),
            decimal=(zope.schema.Decimal, [Decimal('3.4'), Decimal('4.5')]),
            string=(zope.schema.TextLine, [u'foo', u'bar']),
            text=(zope.schema.Text, [u'Some\nFoo', u'Some\nBar']),
            date=(zope.schema.Date, [date(2011, 01, 03), date(2012, 02, 19)]),
            datetime=(zope.schema.Datetime,
                [datetime(2011, 01, 03), datetime(2012, 02, 19)]),
            )

        for name, (ztype, choices) in types.items():
            # Test as a basic field type
            field = ztype(__name__='Foo', title=u'Foo')
            attribute = fieldToAttribute(field)
            self.assertEqual(attribute.type, name)

            # Test as a collection
            field = zope.schema.List(__name__='Foo', title=u'Foo', value_type=ztype())
            attribute = fieldToAttribute(field)
            self.assertEqual(attribute.type, name)
            self.assertTrue(attribute.is_collection)

            # Test with answer choices
            field = zope.schema.Choice(__name__='Foo', title=u'Foo', values=choices)
            # Cannot convert a choice field without a directive
            with self.assertRaises(ValueError):
                attribute = fieldToAttribute(field)
            directives.type.set(field, name)
            attribute = fieldToAttribute(field)
            self.assertEqual(attribute.type, name)


    def testObject(self):
        field = zope.schema.Object(
            __name__='foo',
            title=u'Foo',
            schema=InterfaceClass('Foo')
            )
        # Same deal, cannot add an object that doesn't use the directive base
        with self.assertRaises(ValueError):
            attribute = fieldToAttribute(field)

        # Add the proper base and try again, should work correctly now
        field.schema = InterfaceClass('Foo', bases=[directives.Schema])
        attribute = fieldToAttribute(field)
        self.assertEqual(attribute.type, 'object')
        self.assertTrue(attribute.object_schema is not None)
        self.assertEqual(attribute.object_schema.name, 'Foo')
