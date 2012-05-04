"""
Tests for storage implementations and services
"""

import time
import unittest2 as unittest
from datetime import date
from datetime import datetime
from decimal import Decimal

import sqlalchemy.exc
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore.model.storage import nameModelMap
from occams.datastore.testing import OCCAMS_DATASTORE_FIXTURE
from occams.datastore.interfaces import  IEntity
from occams.datastore.interfaces import InvalidEntitySchemaError
from occams.datastore.interfaces import ConstraintError


class EntityModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_DATASTORE_FIXTURE

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

    def testAddUnpublishedSchema(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        with self.assertRaises(InvalidEntitySchemaError):
            session.flush()

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

    def testTypes(self):
        session = self.layer['session']
        sample = [
            ('integer', 5, 8, [1, 2, 3]),
            ('decimal', Decimal('16.4'), Decimal('12.3'),
                    [Decimal('1.5'), Decimal('12.1'), Decimal('3.0')]),
            ('boolean', True, False, [True, False]),
            ('string', u'foo', u'bar', [u'foo', u'bar', u'baz']),
            ('text', u'foo\nbar', u'foo\nbario', [u'par\n1', u'par\n2', u'par\n3']),
            ('date', date(2010, 3, 1), date(2010, 4, 1),
                [date(2010, 1, 1), date(2010, 2, 1), date(2010, 3, 1)]),
            ('datetime', datetime(2010, 3, 1, 5, 3, 0), datetime(2011, 3, 1, 5, 3, 0),
                [
                datetime(2010, 3, 1, 5, 3, 0),
                datetime(2010, 5, 1, 5, 3, 0),
                datetime(2010, 8, 1, 5, 3, 0),
                ]),
            ]

        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        order = 0

        for typeName, simple, update, collection in sample:
            ModelClass = nameModelMap[typeName]

            # Do simple values
            simpleName = typeName + 'simple'
            schema[simpleName] = model.Attribute(title=u'', type=typeName, is_required=False, order=order)
            entity[simpleName] = None
            session.flush()
            self.assertEqual(None, entity[simpleName])

            entity[simpleName] = simple
            session.flush()
            self.assertEqual(simple, entity[simpleName])

            # Double check auditing
            valueQuery = session.query(ModelClass).filter_by(attribute=schema[simpleName])
            valueObject = valueQuery.one()
            self.assertEqual(2, valueObject.revision)

            # Try updating
            entity[simpleName] = update
            session.flush()
            self.assertEqual(update, entity[simpleName])

            # Triple check auditing
            valueObject = valueQuery.one()
            self.assertEqual(3, valueObject.revision)

            order += 1

            # Now try collections
            collectionName = typeName + 'collection'
            schema[collectionName] = model.Attribute(title=u'', type=typeName, is_collection=True, order=order)
            entity[collectionName] = collection
            session.flush()
            self.assertItemsEqual(collection, entity[collectionName])

            valueQuery = session.query(ModelClass).filter_by(attribute=schema[collectionName])

            order += 1

            # Make sure we can also update
            entity[collectionName] = collection[:2]
            session.flush()
            self.assertItemsEqual(collection[:2], entity[collectionName])
            self.assertEqual(2, valueQuery.count())

            # Lists are not audited, they're just removed and a new one is
            # set
            self.assertItemsEqual([1, 1], [v.revision for v in valueQuery])

    def testSubObject(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        subschema = model.Schema(name='Sub', title=u'', state='published')
        model.Attribute(schema=schema, name='sub', title=u'', type='object', order=0, object_schema=subschema)
        session.flush()
        self.assertIsNone(entity['sub'])

        subentity = model.Entity(schema=subschema, name='Sub', title=u'')
        entity['sub'] = subentity
        session.flush()
        self.assertEqual(subentity.id, entity['sub'].id)

        # Update the subentity, should be ok
        subentity = model.Entity(schema=subschema, name='NewSub', title=u'')
        entity['sub'] = subentity
        session.flush()
        self.assertEqual(subentity.id, entity['sub'].id)

        # Because there is not enough confidence in subobjects, try every
        # single possible type
        sample = [
            ('integer', 5, [1, 2, 3]),
            ('decimal', Decimal('16.4'), [Decimal('1.5'), Decimal('12.1'), Decimal('3.0')]),
            ('boolean', True, [True, False]),
            ('string', u'foo', [u'foo', u'bar', u'baz']),
            ('text', u'foo\nbar', [u'par\n1', u'par\n2', u'par\n3']),
            ('date', date(2010, 3, 1), [date(2010, 1, 1), date(2010, 2, 1), date(2010, 3, 1)]),
            ('datetime', datetime(2010, 3, 1, 5, 3, 0), [
                datetime(2010, 3, 1, 5, 3, 0),
                datetime(2010, 5, 1, 5, 3, 0),
                datetime(2010, 8, 1, 5, 3, 0),
                ]),
            ]

        order = 0

        for typeName, simple, collection in sample:
            # Do simple values
            simpleName = typeName + 'simple'
            subschema[simpleName] = model.Attribute(title=u'', type=typeName, order=order)
            entity['sub'][simpleName] = simple
            session.flush()
            self.assertEqual(simple, entity['sub'][simpleName])

            order += 1

            # Now try collections
            collectionName = typeName + 'collection'
            subschema[collectionName] = model.Attribute(title=u'', type=typeName, is_collection=True, order=order)
            entity['sub'][collectionName] = collection
            session.flush()
            self.assertItemsEqual(collection, entity['sub'][collectionName])

            order += 1

    def testAttributeRequiredConstraint(self):
        # An attribute is required to set a value
        with self.assertRaises(ConstraintError):
            value = model.ValueString(value=u'Foo')

    def testValueMinConstraint(self):
        session = self.layer['session']
        tests = (
            # (type, limit, below, equal, over)
            ('string', 5, 'foo', 'foooo', 'foobario'),
            ('integer', 5, 2, 5, 10),
            ('decimal', 5, Decimal('2.0'), Decimal('5.0'), Decimal('10.0')),
            ('date', time.mktime(date(2009, 5, 6).timetuple()), date(2001, 2, 8), date(2009, 5, 6), date(2010, 4, 6)),
            ('datetime', time.mktime(date(2009, 5, 6).timetuple()), datetime(2001, 2, 8), datetime(2009, 5, 6), datetime(2010, 4, 6)),
            )

        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        for i, test in enumerate(tests):
            type_, limit, below, equal, over = test
            model.Attribute(schema=schema, name=type_, title=u'', type=type_, is_required=False, value_min=limit, order=i)

            with self.assertRaises(ConstraintError):
                entity[type_] = below

            entity[type_] = None
            entity[type_] = equal
            entity[type_] = over

        model.Attribute(schema=schema, name='boolean', title=u'', type='boolean', value_min=10, order=100)
        with self.assertRaises(NotImplementedError):
            entity['boolean'] = True

    def testValueMaxConstraint(self):
        session = self.layer['session']
        tests = (
            # (type, limit, below, equal, over)
            ('string', 5, 'foo', 'foooo', 'foobario'),
            ('integer', 5, 2, 5, 10),
            ('decimal', 5, Decimal('2.0'), Decimal('5.0'), Decimal('10.0')),
            ('date', time.mktime(date(2009, 5, 6).timetuple()), date(2001, 2, 8), date(2009, 5, 6), date(2010, 4, 6)),
            ('datetime', time.mktime(date(2009, 5, 6).timetuple()), datetime(2001, 2, 8), datetime(2009, 5, 6), datetime(2010, 4, 6)),
            )

        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        for i, test in enumerate(tests):
            type_, limit, below, equal, over = test
            model.Attribute(schema=schema, name=type_, title=u'', type=type_, is_required=False, value_max=limit, order=i)

            entity[type_] = None
            entity[type_] = below
            entity[type_] = equal

            with self.assertRaises(ConstraintError):
                entity[type_] = over

        model.Attribute(schema=schema, name='boolean', title=u'', type='boolean', value_max=10, order=100)
        with self.assertRaises(NotImplementedError):
            entity['boolean'] = True

    def testValidatorConstraint(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        model.Attribute(
            schema=schema,
            name='test',
            title=u'',
            type='string',
            is_required=False,
            # Valid US phone number
            validator=r'\d{3}-\d{3}-\d{4}',
            order=0
            )
        session.add(schema)
        session.flush()

        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)

        entity['test'] = None

        with self.assertRaises(ConstraintError):
            entity['test'] = u'trollol'

        entity['test'] = '123-456-7890'
        session.flush()
        self.assertEqual('123-456-7890', entity['test'])

    def testChoiceConstraint(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        model.Attribute(schema=schema, name='test', title=u'', type='string', is_required=False, order=0, choices=[
            model.Choice(name='foo', title=u'Foo', value=u'foo', order=0),
            model.Choice(name='bar', title=u'Bar', value=u'bar', order=1),
            model.Choice(name='baz', title=u'Baz', value=u'baz', order=2),
            ])
        session.add(schema)
        session.flush()

        entity = model.Entity(schema=schema, name=u'FooEntry', title=u'')
        session.add(entity)

        entity['test'] = None
        entity['test'] = u'foo'
        session.flush()

        entry = session.query(model.ValueString).filter_by(value=u'foo').one()
        self.assertIsNotNone(entry.choice, u'Choice not set')

        # Should not be able to set it to something outside of the specified
        # choice constraints

        with self.assertRaises(ConstraintError):
            entity['test'] = u'umadbro?'

    def testDictLike(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'', state='published')
        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        session.flush()

        # The schema does not define the target attribute, so it should error
        with self.assertRaises(KeyError):
            entity['foo'] = 5

        # Basic datatypes
        schema['foo'] = model.Attribute(title=u'', type='integer', order=0)
        self.assertIsNone(entity['foo'])
        entity['foo'] = 5
        session.flush()
        self.assertEqual(5, entity['foo'])

        schema['bar'] = model.Attribute(title=u'', type='integer', is_collection=True, order=1)
        self.assertListEqual([], entity['bar'])
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
