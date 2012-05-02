"""
Tests the schema subquery converter module
"""

import unittest2 as unittest
from datetime import date
from datetime import datetime
from decimal import Decimal

from occams.datastore.testing import OCCAMS_DATASTORE_MODEL_FIXTURE
from occams.datastore import model
from occams.datastore.interfaces import InvalidEntitySchemaError
from occams.datastore.query import Split
from occams.datastore.query import schemaToSubquery
from occams.datastore.query import getColumnPlan
from occams.datastore.schema import copy


p1 = date(2010, 3, 1)
p2 = date(2010, 9, 1)
p3 = date(2011, 8, 1)
p4 = date(2012, 5, 1)


class ColumnPlanTestCase(unittest.TestCase):
    """
    Verifies column header
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testUnpublishedSchema(self):
        session = self.layer['session']
        session.add(model.Schema(name='A', title=u'', state='draft'))
        session.flush()

        with self.assertRaises(InvalidEntitySchemaError):
            plan = getColumnPlan(session, 'A')

    def testEmptyPublishedSchema(self):
        session = self.layer['session']
        session.add(model.Schema(name='A', title=u'', state='published'))
        session.flush()
        plan = getColumnPlan(session, 'A')
        self.assertEqual(0, len(plan))

    def testKeysFromSingleForm(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='published',
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                )
            )
        session.add(schema)
        session.flush()

        # By Name
        plan = getColumnPlan(session, 'A', split=Split.NAME)
        expected = [('a',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))

        # By Checksum
        plan = getColumnPlan(session, 'A', split=Split.CHECKSUM)
        expected = [('a', schema['a'].checksum)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))

        # By id
        plan = getColumnPlan(session, 'A', split=Split.ID)
        expected = [('a', schema['a'].id)]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))

    def testKeysFromMultpleVersions(self):
        session = self.layer['session']
        schema1 = model.Schema(name='A', title=u'', state='published', publish_date=p1,
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                )
            )

        schema2 = copy(schema1)
        schema2.state = 'published'
        schema2.publish_date = p2

        schema3 = copy(schema1)
        schema3.state = 'published'
        schema3.publish_date = p3
        schema3['a'].title = u'prime'

        session.add_all([schema1, schema2, schema3])

        # By Name
        plan = getColumnPlan(session, 'A', split=Split.NAME)
        expected = [('a',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(3, len(plan[expected[0]]))

        # By Checksum
        plan = getColumnPlan(session, 'A', split=Split.CHECKSUM)
        expected = [('a', schema1['a'].checksum), ('a', schema3['a'].checksum)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(2, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))

        # By id
        plan = getColumnPlan(session, 'A', split=Split.ID)
        expected = [
            ('a', schema1['a'].id),
            ('a', schema2['a'].id),
            ('a', schema3['a'].id)
            ]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))

    def testKeysFromSubSchema(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='published',
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                b=model.Attribute(name='b', title=u'', type='object', order=1,
                    object_schema=model.Schema(name='B', title=u'', state='published',
                        attributes=dict(
                            x=model.Attribute(name='x', title=u'', type='string', order=0,),
                            y=model.Attribute(name='y', title=u'', type='string', order=1,),
                            z=model.Attribute(name='z', title=u'', type='string', order=2,),
                            )
                        )
                    ),
                c=model.Attribute(name='c', title=u'', type='string', order=2),
                )
            )
        session.add(schema)
        session.flush()

        # By Name
        plan = getColumnPlan(session, 'A', split=Split.NAME)
        expected = [('a',), ('b', 'x'), ('b', 'y'), ('b', 'z'), ('c',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))
        self.assertEqual(1, len(plan[expected[2]]))
        self.assertEqual(1, len(plan[expected[3]]))
        self.assertEqual(1, len(plan[expected[4]]))

        # By Checksum
        plan = getColumnPlan(session, 'A', split=Split.CHECKSUM)
        expected = [
            ('a', schema['a'].checksum),
            ('b', 'x', schema['b']['x'].checksum),
            ('b', 'y', schema['b']['y'].checksum),
            ('b', 'z', schema['b']['z'].checksum),
            ('c', schema['c'].checksum),
            ]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))
        self.assertEqual(1, len(plan[expected[2]]))
        self.assertEqual(1, len(plan[expected[3]]))
        self.assertEqual(1, len(plan[expected[4]]))

        # By id
        plan = getColumnPlan(session, 'A', split=Split.ID)
        expected = [
            ('a', schema['a'].id),
            ('b', 'x', schema['b']['x'].id),
            ('b', 'y', schema['b']['y'].id),
            ('b', 'z', schema['b']['z'].id),
            ('c', schema['c'].id),
            ]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))

    def testKeysFromSubSchemaMultipleVersions(self):
        """
        From the discussion Jennifer and I had:
        Time p1:
                A
              / | \
             a  b  c
              / | \
             x  y  z

        Time p2:
            ``a`` is modifiied
            ``y`` is modified
            ``b`` children are reordered (doesn't affect checksums, but
                considered on output

                A
              / | \
             a' b  c
              / | \
             z  x  y'

        Time p3:
            ``a`` is restored
            ``x`` is removed
            ``y`` is removed
            ``y*`` is added to the parent schema (interpreted as new attribute
                because it belongs to a new partent)

                A
              / | \
             a  b  y*
                |
                z
        """
        session = self.layer['session']
        schema1 = model.Schema(name='A', title=u'', state='published', publish_date=p1,
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                b=model.Attribute(name='b', title=u'', type='object', order=1,
                    object_schema=model.Schema(name='B', title=u'', state='published', publish_date=p1,
                        attributes=dict(
                            x=model.Attribute(name='x', title=u'', type='string', order=0,),
                            y=model.Attribute(name='y', title=u'', type='string', order=1,),
                            z=model.Attribute(name='z', title=u'', type='string', order=2,),
                            )
                        )
                    ),
                c=model.Attribute(name='c', title=u'', type='string', order=2),
                )
            )

        schema2 = copy(schema1)
        schema2.state = schema2['b'].object_schema.state = 'published'
        schema2.publish_date = schema2['b'].object_schema.publish_date = p2
        schema2['a'].title = u'prime'
        schema2['b']['y'].title = u'prime'
        schema2['b']['z'].order = 0
        schema2['b']['x'].order = 1
        schema2['b']['y'].order = 2

        schema3 = copy(schema2)
        schema3.state = schema3['b'].object_schema.state = 'published'
        schema3.publish_date = schema3['b'].object_schema.publish_date = p3
        schema3['a'] = model.Attribute(name='a', title=u'', type='string', order=0)
        del schema3['b']['x']
        del schema3['b']['y']
        del schema3['c']
        schema3['y'] = model.Attribute(name='y', title=u'', type='string', order=2,)

        session.add_all([schema1, schema2, schema3])
        session.flush()

        # By Name
        plan = getColumnPlan(session, 'A', split=Split.NAME)
        expected = [('a',), ('b', 'z'), ('b', 'x'), ('b', 'y'), ('c',), ('y',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(3, len(plan[expected[0]]))
        self.assertEqual(3, len(plan[expected[1]]))
        self.assertEqual(2, len(plan[expected[2]]))
        self.assertEqual(2, len(plan[expected[3]]))
        self.assertEqual(2, len(plan[expected[4]]))
        self.assertEqual(1, len(plan[expected[5]]))

        # By Checksum
        plan = getColumnPlan(session, 'A', split=Split.CHECKSUM)
        expected = [
            ('a', schema1['a'].checksum),
            ('a', schema2['a'].checksum),
            ('b', 'z', schema1['b']['z'].checksum),
            ('b', 'x', schema1['b']['x'].checksum),
            ('b', 'y', schema1['b']['y'].checksum),
            ('b', 'y', schema2['b']['y'].checksum),
            ('c', schema1['c'].checksum),
            ('y', schema3['y'].checksum),
            ]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(2, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))
        self.assertEqual(3, len(plan[expected[2]]))
        self.assertEqual(2, len(plan[expected[3]]))
        self.assertEqual(1, len(plan[expected[4]]))
        self.assertEqual(1, len(plan[expected[5]]))
        self.assertEqual(2, len(plan[expected[6]]))
        self.assertEqual(1, len(plan[expected[7]]))

        # By id
        plan = getColumnPlan(session, 'A', split=Split.ID)
        expected = [
            ('a', schema1['a'].id),
            ('a', schema2['a'].id),
            ('a', schema3['a'].id),
            ('b', 'z', schema1['b']['z'].id),
            ('b', 'z', schema2['b']['z'].id),
            ('b', 'z', schema3['b']['z'].id),
            ('b', 'x', schema1['b']['x'].id),
            ('b', 'x', schema2['b']['x'].id),
            ('b', 'y', schema1['b']['y'].id),
            ('b', 'y', schema2['b']['y'].id),
            ('c', schema1['c'].id),
            ('c', schema2['c'].id),
            ('y', schema3['y'].id),
            ]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))


class SchemaToSubqueryTestCase(unittest.TestCase):
    """
    Verifies subquery exporting
    """

    layer = OCCAMS_DATASTORE_MODEL_FIXTURE

    def testExpectedMetadataColumns(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='published', publish_date=p1)
        session.add(schema)
        session.flush()

        plan, subquery = schemaToSubquery(session, 'A')
        self.assertIn('entity_id', subquery.c)

    def testEmptySchema(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='published', publish_date=p1)
        session.add(schema)
        session.flush()

        plan, subquery = schemaToSubquery(session, 'A', Split.NAME)

        self.assertEqual(0, session.query(subquery).count())

        entity = model.Entity(schema=schema, name='Sample', title=u'')
        session.add(entity)
        session.flush()

        self.assertEqual(1, session.query(subquery).count())

    def createEntity(self, schema, name, collect_date, values):
        session = self.layer['session']
        entity = model.Entity(schema=schema, name=name, title=u'', collect_date=collect_date)
        session.add(entity)
        for key, value in values.iteritems():
            entity[key] = value
        session.flush()
        return entity

    def createSchema(self, name, publish_date, attributes):
        session = self.layer['session']
        schema = model.Schema(
            name=name,
            title=u'',
            state='published',
            publish_date=publish_date,
            attributes=attributes
            )
        session.add(schema)
        session.flush()
        return schema

    def testFlatSchema(self):
        session = self.layer['session']

        schema1 = self.createSchema('Sample', p1, dict(
            textValue=model.Attribute(name='textValue', title=u'', type='text', order=0),
            stringValue=model.Attribute(name='stringValue', title=u'', type='string', order=1),
            integerValue=model.Attribute(name='integerValue', title=u'', type='integer', order=2),
            decimalValue=model.Attribute(name='decimalValue', title=u'', type='decimal', order=3),
            booleanValue=model.Attribute(name='booleanValue', title=u'', type='boolean', order=4),
            dateValue=model.Attribute(name='dateValue', title=u'', type='date', order=5),
            datetimeValue=model.Attribute(name='datetimeValue', title=u'', type='datetime', order=6),
            ))

        entity1 = self.createEntity(schema1, 'Foo', p1, dict(
            textValue=u'some\nfoovalue',
            stringValue=u'foovalue',
            integerValue=10,
            decimalValue=Decimal('5.1'),
            booleanValue=True,
            dateValue=date(2010, 10, 1),
            datetimeValue=datetime(2010, 10, 1, 5, 10, 30),
            ))

        entity2 = self.createEntity(schema1, 'Bar', p1, dict(
            textValue=u'some\nbarvalue',
            stringValue=u'barvalue',
            integerValue=30,
            decimalValue=Decimal('1.89'),
            booleanValue=False,
            dateValue=date(2012, 5, 1),
            datetimeValue=datetime(2012, 5, 1, 16, 19),
            ))

        plan, subquery = schemaToSubquery(session, 'Sample', Split.NAME)

        result = session.query(subquery).filter_by(entity_id=entity1.id).one()
        self.assertEqual(entity1['textValue'], result.textValue)
        self.assertEqual(entity1['stringValue'], result.stringValue)
        self.assertEqual(entity1['integerValue'], result.integerValue)
        self.assertEqual(entity1['booleanValue'], result.booleanValue)
        self.assertEqual(str(entity1['dateValue']), str(result.dateValue))
        self.assertEqual(str(entity1['datetimeValue']), str(result.datetimeValue))

        result = session.query(subquery).filter_by(entity_id=entity2.id).one()
        self.assertEqual(entity2['textValue'], result.textValue)
        self.assertEqual(entity2['stringValue'], result.stringValue)
        self.assertEqual(entity2['integerValue'], result.integerValue)
        self.assertEqual(entity2['booleanValue'], result.booleanValue)
        self.assertEqual(str(entity2['dateValue']), str(result.dateValue))
        self.assertEqual(str(entity2['datetimeValue']), str(result.datetimeValue))

#        # Now add a new version
#        schema2 = copy(schema1)
#        schema2.state = 'published'
#        schema2.publish_date = p2
#        schema2['a'].title = u'prime'
#        session.add(schema2)
#        session.flush()
#
#        entity3 = self.createEntity(schema2, 'Baz', p2, dict(a=u'bazvalue'))
#
#        plan, subquery = schemaToSubquery(session, 'A', Split.NAME)

