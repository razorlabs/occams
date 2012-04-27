"""
Test case for schema implementations and services
"""

import unittest2 as unittest
from datetime import date
from datetime import datetime
from decimal import Decimal

import sqlalchemy.exc
from zope.schema.interfaces import IInt
from zope.schema.interfaces import IDecimal
from zope.schema.interfaces import ITextLine
from zope.schema.interfaces import IText
from zope.schema.interfaces import IBool
from zope.schema.interfaces import IDate
from zope.schema.interfaces import IDatetime
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import IList
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore.model.schema import generateChecksum
from occams.datastore.interfaces import ISchema
from occams.datastore.interfaces import IAttribute
from occams.datastore.interfaces import IChoice as dsIChoice
from occams.datastore.interfaces import ICategory
from occams.datastore.interfaces import IManager
from occams.datastore.interfaces import ISchemaManagerFactory
from occams.datastore.interfaces import NotFoundError
from occams.datastore.schema import SchemaManager
from occams.datastore.schema import HierarchyInspector
from occams.datastore.schema import copy
from occams.datastore.schema import attributeToField
from occams.datastore.testing import OCCAMS_DATASTORE_MODEL_FIXTURE


p1 = date(2012, 3, 1)
p2 = date(2012, 4, 1)
p3 = date(2012, 5, 1)
p4 = date(2012, 6, 1)


class SchemaModelTestCase(unittest.TestCase):
    """
    Verifies Schema model
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(ISchema, model.Schema))
        self.assertTrue(verifyObject(ISchema, model.Schema()))

    def testAdd(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Schema).count()
        self.assertEquals(1, schemaCount, u'Found more than one entry')

    def testSamePublishDate(self):
        # Test publish date uniqueness
        session = self.layer['session']

        # Add a published schema
        session.add(model.Schema(
            name='Foo',
            title=u'Foo',
            state='published',
            publish_date=p1
            ))
        session.flush()

        # Add a work-in-progress schema, should not interfere
        session.add(model.Schema(
            name='Foo',
            title=u'Foo',
            state='draft',
            publish_date=None
            ))
        session.flush()

        # Add another published schema (not on the same date)
        session.add(model.Schema(
            name='Foo',
            title=u'Foo',
            state='published',
            publish_date=p2
            ))
        session.flush()

        # Now try to add a schema published on the same date as another
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.add(model.Schema(
                name='Foo',
                title=u'Foo',
                state='published',
                publish_date=p1
                ))
            session.flush()

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
        self.assertEqual(False, schema.is_inline)
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
        self.assertIsNotNone(schema.publish_date)

        # It should only work if the schema is marked as published
        schema = model.Schema(name='Sample2', title=u'Sample')
        session.add(schema)
        session.flush()
        self.assertIsNone(schema.publish_date)

    def testMissingTitle(self):
        session = self.layer['session']
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.add(model.Schema(name='Sample'))
            session.flush()


class AttributeModelTestCase(unittest.TestCase):
    """
    Verifies Attribute model
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(IAttribute, model.Attribute))
        self.assertTrue(verifyObject(IAttribute, model.Attribute()))

    def testAdd(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'Foo')
        attribute = model.Attribute(
            schema=schema,
            name='foo',
            title=u'Enter Foo',
            type='string',
            order=0
            )
        session.add(attribute)
        session.flush()
        schemaCount = session.query(model.Attribute).count()
        self.assertEquals(1, schemaCount, u'Found more than one entry')


class ChoiceModelTestCase(unittest.TestCase):
    """
    Verifies Choice model
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(dsIChoice, model.Choice))
        self.assertTrue(verifyObject(dsIChoice, model.Choice()))

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
        self.assertEquals(3, schemaCount, u'Did not find choices')

class CategoryModelTestCase(unittest.TestCase):
    """
    Verifies Category model
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testImplemetation(self):
        self.assertTrue(verifyClass(ICategory, model.Category))
        self.assertTrue(verifyObject(ICategory, model.Category()))

    def testAdd(self):
        session = self.layer['session']
        category = model.Category(name='Tests', title=u'Test Schemata')
        session.add(category)
        session.flush()

        self.assertIsNotNone(category.id)
        self.assertEqual('Tests', category.name)
        self.assertEqual(u'Test Schemata', category.title)
        self.assertIsNone(category.description)

    def testAppendToSchema(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        session.add(schema)
        session.flush()

        self.assertEqual(0, len(schema.categories))
        category1 = model.Category(name='Tests', title=u'Test Schemata')
        schema.categories.add(category1)
        session.flush()
        self.assertEqual(1, len(schema.categories))

        schema.categories.add(category1)
        session.flush()
        self.assertEqual(1, len(schema.categories))

        category2 = model.Category(name='Bars', title=u'Bar Schemata')
        schema.categories.add(category2)
        self.assertEqual(2, len(schema.categories))

        # Now try a common use case: get all schema of a certain cateogry
        # First we'll need a second schema of the same category of another
        schema2 = model.Schema(name='Bar', title=u'', state='published')
        schema2.categories.add(category2)
        session.add(schema2)
        session.flush()

        # Now we want all the schemata of a certain category
        schemata = (
            session.query(model.Schema)
            .join(model.Schema.categories)
            .filter_by(name='Bars')
            .all()
            )

        # Should be the ones we just marked
        self.assertItemsEqual(['Foo', 'Bar'], [s.name for s in schemata])


class ChecksumTestCase(unittest.TestCase):

    def testGenerate(self):
        attribute1 = model.Attribute(
            schema=model.Schema(name='Sample', title=u'Sample Schema'),
            name=u'value',
            title=u'Enter value',
            type='string'
            )

        attribute2 = model.Attribute(
            schema=model.Schema(name='Sample', title=u'Sample Schema'),
            name=u'value',
            title=u'Enter value',
            type='string'
            )

        checksum1 = generateChecksum(attribute1)
        checksum2 = generateChecksum(attribute2)

        self.assertIsNotNone(checksum1)
        self.assertIsNotNone(checksum2)
        self.assertEqual(checksum1, checksum2)

        attribute2.schema.title = 'New title that makes no difference'
        checksum2 = generateChecksum(attribute2)
        self.assertEqual(checksum1, checksum2)

        attribute2.schema.name = 'ThisDoes'
        checksum2 = generateChecksum(attribute2)
        self.assertNotEqual(checksum1, checksum2)

        # Change it back
        attribute2.schema.name = 'Sample'
        checksum2 = generateChecksum(attribute2)
        self.assertEqual(checksum1, checksum2)

        attribute2.title = u'Bleh'
        checksum2 = generateChecksum(attribute2)
        self.assertNotEqual(checksum1, checksum2)

    def testGenerateWithChoices(self):
        attribute1 = model.Attribute(
            schema=model.Schema(name='Sample', title=u'Sample Schema'),
            name=u'value',
            title=u'Enter value',
            type='string',
            choices=[
                model.Choice(name='never', title=u'Never', value=u'never', order=0),
                model.Choice(name='sometimes', title=u'Sometimes', value=u'sometimes', order=1),
                model.Choice(name='always', title=u'Always', value=u'always', order=2),
                ]
            )

        attribute2 = model.Attribute(
            schema=model.Schema(name='Sample', title=u'Sample Schema'),
            name=u'value',
            title=u'Enter value',
            type='string',
            choices=[
                model.Choice(name='never', title=u'Never', value=u'never', order=0),
                model.Choice(name='sometimes', title=u'Sometimes', value=u'sometimes', order=1),
                model.Choice(name='always', title=u'Always', value=u'always', order=2),
                ]
            )

        checksum1 = generateChecksum(attribute1)
        checksum2 = generateChecksum(attribute2)

        self.assertIsNotNone(checksum1)
        self.assertIsNotNone(checksum2)
        self.assertEqual(checksum1, checksum2)

        attribute2.schema.title = 'New title that makes no difference'
        checksum2 = generateChecksum(attribute2)
        self.assertEqual(checksum1, checksum2)

        attribute2.schema.name = 'ThisDoes'
        checksum2 = generateChecksum(attribute2)
        self.assertNotEqual(checksum1, checksum2)

        # Change it back
        attribute2.schema.name = 'Sample'
        checksum2 = generateChecksum(attribute2)
        self.assertEqual(checksum1, checksum2)

        attribute2.title = u'Bleh'
        checksum2 = generateChecksum(attribute2)
        self.assertNotEqual(checksum1, checksum2)


class SchemaCopyTestCase(unittest.TestCase):
    """
    Verifies that schemata can be "deep" copied as new versions of schemata
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testBasic(self):
        session = self.layer['session']
        schema = model.Schema(
            name='Foo',
            title=u'Foo',
            attributes=dict(
                foo=model.Attribute(
                    name='foo',
                    title=u'Enter Foo',
                    type='string',
                    choices=[
                        model.Choice(name='foo', title=u'Foo', value='foo', order=0),
                        model.Choice(name='bar', title=u'Bar', value='bar', order=1),
                        model.Choice(name='baz', title=u'Baz', value='baz', order=2),
                        ],
                    order=0
                    )
                )
            )

        session.add(schema)
        session.flush()

        schemaCopy = copy(schema)

        # The ones that matter for checksums
        self.assertEqual(schema.name, schemaCopy.name)
        self.assertEqual(schema['foo'].name, schemaCopy['foo'].name)
        self.assertEqual(schema['foo'].title, schemaCopy['foo'].title)
        self.assertEqual(schema['foo'].description, schemaCopy['foo'].description)
        self.assertEqual(schema['foo'].type, schemaCopy['foo'].type)
        self.assertEqual(schema['foo'].is_collection, schemaCopy['foo'].is_collection)
        self.assertEqual(schema['foo'].is_required, schemaCopy['foo'].is_required)
        for i in range(3):
            self.assertEqual(schema['foo'].choices[i].name, schemaCopy['foo'].choices[i].name)
            self.assertEqual(schema['foo'].choices[i].title, schemaCopy['foo'].choices[i].title)
            self.assertEqual(schema['foo'].choices[i].value, schemaCopy['foo'].choices[i].value)
            self.assertEqual(schema['foo'].choices[i].order, schemaCopy['foo'].choices[i].order)

        session.add(schemaCopy)
        session.flush()
        self.assertNotEqual(schema.id, schemaCopy.id)
        self.assertEqual(schema['foo'].checksum, schemaCopy['foo'].checksum)

        schemaCopy['foo'].title = u'New Title'
        session.flush()
        self.assertNotEqual(schema['foo'].checksum, schemaCopy['foo'].checksum)

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


class DictionaryLikeTesCase(unittest.TestCase):
    """
    Tests inspection of schema/attributes as dictionaries
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testSet(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        attribute = model.Attribute(title=u'', type='string', order=0)
        schema['foo'] = attribute
        session.add(schema)
        session.flush()
        schemaCount = session.query(model.Attribute).count()
        self.assertEquals(1, schemaCount)
        self.assertEqual('foo', attribute.name)
        self.assertIsNotNone(attribute.id)

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(title=u'', type='object', object_schema=subschema, order=1)
        schema['sub'] = attribute
        subattribute = model.Attribute(title=u'', type='string', order=0)
        attribute['bar'] = subattribute
        session.flush()
        self.assertEqual('bar', subattribute.name)

    def testGet(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        attribute = model.Attribute(schema=schema, name='foo', title=u'', type='string', order=0)
        session.add(schema)
        session.flush()

        self.assertEqual(attribute.id, schema['foo'].id)
        self.assertEqual(attribute.name, schema['foo'].name)

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(schema=schema, name='sub', title=u'', type='object', object_schema=subschema, order=1)
        model.Attribute(schema=subschema, name='bar', title=u'', type='string', order=0)
        session.flush()
        self.assertEqual('bar', attribute['bar'].name)

    def testDelete(self):
        # Test deleting an attribute via dict-like API
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        model.Attribute(name='foo', schema=schema, title=u'foo', type='string', order=0)
        session.add(schema)
        session.flush()
        # The attribute should have been committed
        result = session.query(model.Attribute).filter_by(name='foo').count()
        self.assertEqual(1, result)
        # Delete it like you would a dictionary
        del schema['foo']
        session.flush()
        # Should have been deleted
        result = session.query(model.Attribute).filter_by(name='foo').count()
        self.assertEqual(0, result)

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(schema=schema, name='sub', title=u'', type='object', object_schema=subschema, order=1)
        model.Attribute(schema=subschema, name='bar', title=u'', type='string', order=0)
        session.flush()
        result = session.query(model.Attribute).filter_by(name='bar').count()
        self.assertEqual(1, result)
        del attribute['bar']
        result = session.query(model.Attribute).filter_by(name='bar').count()
        self.assertEqual(0, result)

    def testContains(self):
        # Test dict-like containment
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()
        self.assertNotIn('foo', schema)
        model.Attribute(schema=schema, name='foo', title=u'foo', type='string', order=0)
        session.flush()
        self.assertIn('foo', schema)
        self.assertNotIn('bar', schema)

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(schema=schema, name='sub', title=u'', type='object', object_schema=subschema, order=1)
        model.Attribute(schema=subschema, name='bar', title=u'', type='string', order=0)
        session.flush()
        self.assertIn('bar', attribute)

    def testKeys(self):
        # Test dict-like reporting of keys
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()
        keys = schema.keys()
        self.assertEqual(len(keys), 0)
        model.Attribute(schema=schema, name='foo', title=u'', type='string', order=0)
        model.Attribute(schema=schema, name='bar', title=u'', type='string', order=1)
        session.flush()
        keys = schema.keys()
        self.assertEqual(2, len(keys))
        self.assertItemsEqual(['bar', 'foo'], keys)

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(schema=schema, name='sub', title=u'', type='object', object_schema=subschema, order=2)
        model.Attribute(schema=subschema, name='bar', title=u'', type='string', order=0)
        model.Attribute(schema=subschema, name='baz', title=u'', type='string', order=1)
        session.flush()
        self.assertItemsEqual(['bar', 'baz'], attribute.keys())

    def testValues(self):
        # Make sure we can enumerate the attributes in the schema
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()
        values = schema.values()
        self.assertEqual(0, len(values))
        model.Attribute(schema=schema, name='foo', title=u'', type='string', order=0)
        session.flush()
        values = schema.values()
        self.assertEqual(1, len(values))
        attribute = values[0]
        self.assertEqual(schema.id, attribute.schema.id)
        self.assertEqual(attribute.name, 'foo')

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(schema=schema, name='sub', title=u'', type='object', object_schema=subschema, order=2)
        subattribtue = model.Attribute(schema=subschema, name='bar', title=u'', type='string', order=0)
        session.flush()
        values = attribute.values()
        self.assertEqual(subattribtue.id, values[0].id)

    def testItems(self):
        # Make sure we can enumerate the key/value pairs of the schema
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()
        items = schema.items()
        self.assertEqual(0, len(items))
        schema['foo'] = model.Attribute(title=u'', type='string', order=0)
        session.flush()
        items = schema.items()
        self.assertEqual(len(items), 1)
        name, attribute = items[0]
        self.assertEqual(schema, attribute.schema)
        self.assertEqual('foo', attribute.name)
        self.assertEqual(name, attribute.name)

        # Equivalent functionality as subschema
        subschema = model.Schema(name='Bar', title=u'')
        attribute = model.Attribute(schema=schema, name='sub', title=u'', type='object', object_schema=subschema, order=2)
        subattribtue = model.Attribute(schema=subschema, name='bar', title=u'', type='string', order=0)
        session.flush()
        items = attribute.items()
        self.assertEqual(subattribtue.name, items[0][0])
        self.assertEqual(subattribtue.name, items[0][1].name)

    def testOrdering(self):
        """
        Make sure attributes are reported in the correct order
        """
        session = self.layer['session']
        schema = model.Schema(name='Sample', title=u'Sample Schema')
        model.Attribute(schema=schema, name='foo', title=u'', type='string', order=0)
        model.Attribute(schema=schema, name='bar', title=u'', type='integer', order=1)
        model.Attribute(schema=schema, name='baz', title=u'', type='decimal', order=2)
        session.add(schema)
        session.flush()

        self.assertListEqual(['foo', 'bar', 'baz'], schema.keys())

        items = schema.items()
        self.assertEqual('foo', items[0][1].name)
        self.assertEqual('bar', items[1][1].name)
        self.assertEqual('baz', items[2][1].name)

        # Try moving one
        schema['foo'].order = 3
        session.flush()

        self.assertListEqual(['bar', 'baz', 'foo'], schema.keys())

        items = schema.items()
        self.assertEqual('bar', items[0][1].name)
        self.assertEqual('baz', items[1][1].name)
        self.assertEqual('foo', items[2][1].name)


class HierarchyTestCase(unittest.TestCase):
    """
    Verifies schema hierarchy listing manager
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

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
        children = hierarchy.children('Animal')
        self.assertEqual(12, len(children))

    def testChildren(self):
        # Get the actual objects
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)
        children = hierarchy.children('Bird')
        self.assertEqual(4, len(children))

    def testChildrenNames(self):
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)
        result = hierarchy.childrenNames('Bird')
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

        with self.assertRaises(NotFoundError):
            hierarchy.children('Fish')

        with self.assertRaises(NotFoundError):
            hierarchy.childrenNames('Fish')

    def testVersioned(self):
        session = self.layer['session']
        hierarchy = HierarchyInspector(session)

        # Shouldn't be able to get children that have not been published
        # as of the given date

        with self.assertRaises(NotFoundError):
            children = hierarchy.children('Animal', on=p1)

        with self.assertRaises(NotFoundError):
            names = hierarchy.childrenNames('Animal', on=p1)


class SchemaManagerTestCase(unittest.TestCase):
    """
    Verifies schema manager
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def setUp(self):
        session = self.layer['session']

        # Add dummy data with multiple versions of forms in various states
        session.add_all([
            model.Schema(name='Foo', title=u'', state='published', publish_date=p1),
            model.Schema(name='Foo', title=u'', state='published', publish_date=p2),
            model.Schema(name='Foo', title=u'', state='published', publish_date=p3),

            model.Schema(name='Bar', title=u'', state='published', publish_date=p1),

            model.Schema(name='Baz', title=u'', state='published', publish_date=p1),
            model.Schema(name='Baz', title=u'', state='published', publish_date=p3),

            model.Schema(name='Caz', title=u'', state='published', publish_date=p2),

            # Manager's only report published schemata
            model.Schema(name='Jaz', title=u'', state='draft'),
            ])

        session.flush()

    def testImplementation(self):
        self.assertTrue(verifyClass(IManager, SchemaManager))
        self.assertTrue(verifyObject(ISchemaManagerFactory, SchemaManager))

    def testKeys(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        self.assertItemsEqual(['Foo', 'Bar', 'Baz', 'Caz'], manager.keys())

        # Doesn't do anything anymore=
        self.assertItemsEqual(['Foo', 'Bar', 'Baz', 'Caz'], manager.keys(ever=True))

        # Caz should not have existed yet
        self.assertItemsEqual(['Foo', 'Bar', 'Baz'], manager.keys(on=p1))

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
        with self.assertRaises(NotFoundError):
            item = manager.get('NonExisting')

        # Get something with multiple versions
        item1 = manager.get('Foo', on=p1)
        item2 = manager.get('Foo', on=p2)
        self.assertNotEqual(item1, item2)
        self.assertEqual(item1.name, item2.name)

        # Get something that only has one version
        item = manager.get('Bar')
        self.assertEqual('Bar', item.name)
        self.assertIsNotNone(item)

        # Get something that doesn't exist yet
        with self.assertRaises(NotFoundError):
            item = manager.get('Caz', on=p1)
        # Only works if we specify the version
        item = manager.get('Caz', on=p3)
        self.assertEqual('Caz', item.name)
        self.assertIsNotNone(item)

        # Also, can't get anything that hasn't been published yet
        with self.assertRaises(NotFoundError):
            item = manager.get('Jaz')

    def testPut(self):
        session = self.layer['session']
        manager = SchemaManager(session)

        # Can't determine name
        with self.assertRaises(ValueError):
            id = manager.put(None, model.Schema(name=None, title=u''))

        schema = model.Schema(name=None, title=u'', state='published')

        # Uses the key
        id = manager.put('Foo', schema)
        self.assertEqual(id, schema.id)
        self.assertEqual('Foo', schema.name)

        # Ignores the key when given a name
        schema = model.Schema(name='Bar', title=u'', state='published')
        id = manager.put('Ignored', schema)
        self.assertEqual(id, schema.id)
        self.assertEqual('Bar', schema.name)


class AttributeToFieldTestCase(unittest.TestCase):
    """
    Verifies that a SQLAlchemy attribute can be converted to a Zope-style field
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

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
            schema['foo'] = model.Attribute(title=u'', type=name, order=0)
            for choice in choices:
                schema['foo'].choices.append(model.Choice(
                    name=str(choice),
                    title=unicode(choice),
                    value=choice
                    ))
            field = attributeToField(schema['foo'])
            self.assertTrue(IChoice.providedBy(field))

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

    def testObject(self):
        # Test as a basic sub-object
        schema = model.Schema(name='Foo', title=u'Foo')
        schema['foo'] = model.Attribute(
            title=u'',
            order=0,
            type='object',
            object_schema=model.Schema(name='Bar', title=u'Bar', is_inline=True)
            )
        with self.assertRaises(ValueError):
            field = attributeToField(schema['foo'])
