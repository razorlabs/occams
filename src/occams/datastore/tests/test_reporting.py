u"""
Tests the schema subquery converter module
"""

import datetime
import decimal
import copy
import unittest2 as unittest

from sqlalchemy import orm

from occams.datastore import model as datastore
from occams.datastore import reporting
from occams.datastore import testing


t1 = datetime.date(2010, 3, 1)
t2 = datetime.date(2010, 9, 1)
t3 = datetime.date(2011, 8, 1)
t4 = datetime.date(2012, 5, 1)


def createEntity(schema, name, collect_date, values={}):
    u"""
    Helper method to create an entities
    """
    session = orm.object_session(schema)
    entity = datastore.Entity(
        schema=schema,
        name=name,
        title=u'',
        collect_date=collect_date
        )
    session.add(entity)
    for key, value in values.iteritems():
        entity[key] = value
    session.flush()
    return entity


def createSchema(session, name, publish_date, attributes={}):
    u"""
    Helper method to create schemata
    """
    schema = datastore.Schema(
        name=name,
        title=u'',
        state=u'published',
        publish_date=publish_date
        )
    for attribute_name, attribute in attributes.iteritems():
        schema[attribute_name] = attribute
    session.add(schema)
    session.flush()
    return schema



class HeaderTestCase(unittest.TestCase):
    u"""
    Ensures that column headers can be properly generated.
    """

    layer = testing.OCCAMS_DATASTORE_FIXTURE

    def testEmptyPublishedSchema(self):
        session = self.layer[u'session']
        session.add(datastore.Schema(name=u'A', title=u'', state=u'published'))
        session.flush()

        # by NAME
        plan = reporting.getHeaderByName(session, u'A')
        self.assertEqual(0, len(plan))

        # by CHECKSUM
        plan = reporting.getHeaderByChecksum(session, u'A')
        self.assertEqual(0, len(plan))

        # by ID
        plan = reporting.getHeaderById(session, u'A')
        self.assertEqual(0, len(plan))

    def testKeysFromSingleForm(self):
        session = self.layer[u'session']
        schema = datastore.Schema(name=u'A', title=u'', state=u'published')
        schema[u'a'] = datastore.Attribute(title=u'', type=u'string', order=0)
        session.add(schema)
        session.flush()

        # by NAME
        plan = reporting.getHeaderByName(session, u'A')
        expected = [(u'a',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))

        # by CHECKSUM
        plan = reporting.getHeaderByChecksum(session, u'A')
        expected = [(u'a', schema[u'a'].checksum)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))

        # by ID
        plan = reporting.getHeaderById(session, u'A')
        expected = [(u'a', schema[u'a'].id)]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))

    def testKeysFromMultpleVersions(self):
        session = self.layer[u'session']
        schema1 = datastore.Schema(name=u'A', title=u'', state=u'published', publish_date=t1)
        schema1[u'a'] = datastore.Attribute(title=u'', type=u'string', order=0)

        schema2 = copy.deepcopy(schema1)
        schema2.state = u'published'
        schema2.publish_date = t2

        schema3 = copy.deepcopy(schema1)
        schema3.state = u'published'
        schema3.publish_date = t3
        schema3[u'a'].title = u'prime'

        session.add_all([schema1, schema2, schema3])

        # by NAME
        plan = reporting.getHeaderByName(session, u'A')
        expected = [(u'a',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(3, len(plan[expected[0]]))

        # by CHECKSUM
        plan = reporting.getHeaderByChecksum(session, u'A')
        expected = [(u'a', schema1[u'a'].checksum), (u'a', schema3[u'a'].checksum)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(2, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))

        # by ID
        plan = reporting.getHeaderById(session, u'A')
        expected = [
            (u'a', schema1[u'a'].id),
            (u'a', schema2[u'a'].id),
            (u'a', schema3[u'a'].id)
            ]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))

    def testKeysFromSubSchema(self):
        session = self.layer[u'session']
        schema = datastore.Schema(name=u'A', title=u'', state=u'published')
        schema[u'a'] = datastore.Attribute(title=u'', type=u'string', order=0)
        schema[u'b'] = datastore.Attribute(title=u'', type=u'object', order=1)
        schema[u'b'].object_schema = datastore.Schema(name=u'B', title=u'', state=u'published')
        schema[u'b'][u'x'] = datastore.Attribute(title=u'', type=u'string', order=0)
        schema[u'b'][u'y'] = datastore.Attribute(title=u'', type=u'string', order=1)
        schema[u'b'][u'z'] = datastore.Attribute(title=u'', type=u'string', order=2)
        schema[u'c'] = datastore.Attribute(title=u'', type=u'string', order=2)
        session.add(schema)
        session.flush()

        # by NAME
        plan = reporting.getHeaderByName(session, u'A')
        expected = [(u'a',), (u'b', u'x'), (u'b', u'y'), (u'b', u'z'), (u'c',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))
        self.assertEqual(1, len(plan[expected[2]]))
        self.assertEqual(1, len(plan[expected[3]]))
        self.assertEqual(1, len(plan[expected[4]]))

        # by CHECKSUM
        plan = reporting.getHeaderByChecksum(session, u'A')
        expected = [
            (u'a', schema[u'a'].checksum),
            (u'b', u'x', schema[u'b'][u'x'].checksum),
            (u'b', u'y', schema[u'b'][u'y'].checksum),
            (u'b', u'z', schema[u'b'][u'z'].checksum),
            (u'c', schema[u'c'].checksum),
            ]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(1, len(plan[expected[0]]))
        self.assertEqual(1, len(plan[expected[1]]))
        self.assertEqual(1, len(plan[expected[2]]))
        self.assertEqual(1, len(plan[expected[3]]))
        self.assertEqual(1, len(plan[expected[4]]))

        # By id
        plan = reporting.getHeaderById(session, u'A')
        expected = [
            (u'a', schema[u'a'].id),
            (u'b', u'x', schema[u'b'][u'x'].id),
            (u'b', u'y', schema[u'b'][u'y'].id),
            (u'b', u'z', schema[u'b'][u'z'].id),
            (u'c', schema[u'c'].id),
            ]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))

    def testKeysFromSubSchemaMultipleVersions(self):
        u"""
        From the discussion Jennifer and I had:
        Time t1:
                A
              / | \
             a  b  c
              / | \
             x  y  z

        Time t2:
            ``a`` is modifiied
            ``y`` is modified
            ``b`` children are reordered (doesn't affect checksums, but
                considered on output

                A
              / | \
             a' b  c
              / | \
             z  x  y'

        Time t3:
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
        session = self.layer[u'session']
        schema1 = datastore.Schema(name=u'A', title=u'', state=u'published', publish_date=t1)
        schema1[u'a'] = datastore.Attribute(title=u'', type=u'string', order=0)
        schema1[u'b'] = datastore.Attribute(title=u'', type=u'object', order=1)
        schema1[u'b'].object_schema = datastore.Schema(name=u'B', title=u'', state=u'published', publish_date=t1)
        schema1[u'b'][u'x'] = datastore.Attribute(title=u'', type=u'string', order=0)
        schema1[u'b'][u'y'] = datastore.Attribute(title=u'', type=u'string', order=1)
        schema1[u'b'][u'z'] = datastore.Attribute(title=u'', type=u'string', order=2)
        schema1[u'c'] = datastore.Attribute(title=u'', type=u'string', order=2)

        schema2 = copy.deepcopy(schema1)
        schema2.state = schema2[u'b'].object_schema.state = u'published'
        schema2.publish_date = schema2[u'b'].object_schema.publish_date = t2
        schema2[u'a'].title = u'prime'
        schema2[u'b'][u'y'].title = u'prime'
        schema2[u'b'][u'z'].order = 0
        schema2[u'b'][u'x'].order = 1
        schema2[u'b'][u'y'].order = 2

        schema3 = copy.deepcopy(schema2)
        schema3.state = schema3[u'b'].object_schema.state = u'published'
        schema3.publish_date = schema3[u'b'].object_schema.publish_date = t3
        schema3[u'a'] = datastore.Attribute(name=u'a', title=u'', type=u'string', order=0)
        del schema3[u'b'][u'x']
        del schema3[u'b'][u'y']
        del schema3[u'c']
        schema3[u'y'] = datastore.Attribute(name=u'y', title=u'', type=u'string', order=2,)

        session.add_all([schema1, schema2, schema3])
        session.flush()

        # by NAME
        plan = reporting.getHeaderByName(session, u'A')
        expected = [(u'a',), (u'b', u'z'), (u'b', u'x'), (u'b', u'y'), (u'c',), (u'y',)]
        self.assertListEqual(expected, plan.keys())
        self.assertEqual(3, len(plan[expected[0]]))
        self.assertEqual(3, len(plan[expected[1]]))
        self.assertEqual(2, len(plan[expected[2]]))
        self.assertEqual(2, len(plan[expected[3]]))
        self.assertEqual(2, len(plan[expected[4]]))
        self.assertEqual(1, len(plan[expected[5]]))

        # by CHECKSUM
        plan = reporting.getHeaderByChecksum(session, u'A')
        expected = [
            (u'a', schema1[u'a'].checksum),
            (u'a', schema2[u'a'].checksum),
            (u'b', u'z', schema1[u'b'][u'z'].checksum),
            (u'b', u'x', schema1[u'b'][u'x'].checksum),
            (u'b', u'y', schema1[u'b'][u'y'].checksum),
            (u'b', u'y', schema2[u'b'][u'y'].checksum),
            (u'c', schema1[u'c'].checksum),
            (u'y', schema3[u'y'].checksum),
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

        # by ID
        plan = reporting.getHeaderById(session, u'A')
        expected = [
            (u'a', schema1[u'a'].id),
            (u'a', schema2[u'a'].id),
            (u'a', schema3[u'a'].id),
            (u'b', u'z', schema1[u'b'][u'z'].id),
            (u'b', u'z', schema2[u'b'][u'z'].id),
            (u'b', u'z', schema3[u'b'][u'z'].id),
            (u'b', u'x', schema1[u'b'][u'x'].id),
            (u'b', u'x', schema2[u'b'][u'x'].id),
            (u'b', u'y', schema1[u'b'][u'y'].id),
            (u'b', u'y', schema2[u'b'][u'y'].id),
            (u'c', schema1[u'c'].id),
            (u'c', schema2[u'c'].id),
            (u'y', schema3[u'y'].id),
            ]
        self.assertListEqual(expected, plan.keys())
        for e in expected:
            self.assertEqual(1, len(plan[e]))


class SchemaToQueryTestCase(unittest.TestCase):
    u"""
    Ensures that schema queries can by properly generated
    """

    layer = testing.OCCAMS_DATASTORE_FIXTURE

    def testExpectedMetadataColumns(self):
        session = self.layer[u'session']
        schema = datastore.Schema(name=u'A', title=u'', state=u'published', publish_date=t1)
        session.add(schema)
        session.flush()

        plan, subquery = reporting.schemaToReportById(session, u'A')
        self.assertIn(u'entity_id', subquery.c)

        plan, subquery = reporting.schemaToReportByName(session, u'A')
        self.assertIn(u'entity_id', subquery.c)

        plan, subquery = reporting.schemaToReportByChecksum(session, u'A')
        self.assertIn(u'entity_id', subquery.c)

    def testEmptySchema(self):
        session = self.layer[u'session']
        schema = datastore.Schema(name=u'A', title=u'', state=u'published', publish_date=t1)
        session.add(schema)
        session.flush()

        plan, subquery = reporting.schemaToReportByName(session, u'A')

        self.assertEqual(0, session.query(subquery).count())

        entity = datastore.Entity(schema=schema, name=u'Sample', title=u'')
        session.add(entity)
        session.flush()

        self.assertEqual(1, session.query(subquery).count())

    def testFlatSchema(self):
        session = self.layer[u'session']

        schema1 = createSchema(session, u'Sample', t1, dict(
            textValue=datastore.Attribute(title=u'', type=u'text', order=0),
            stringValue=datastore.Attribute(title=u'', type=u'string', order=1),
            integerValue=datastore.Attribute(title=u'', type=u'integer', order=2),
            decimalValue=datastore.Attribute(title=u'', type=u'decimal', order=3),
            booleanValue=datastore.Attribute(title=u'', type=u'boolean', order=4),
            dateValue=datastore.Attribute(title=u'', type=u'date', order=5),
            datetimeValue=datastore.Attribute(title=u'', type=u'datetime', order=6),
            ))

        entity1 = createEntity(schema1, u'Foo', t1, dict(
            textValue=u'some\nfoovalue',
            stringValue=u'foovalue',
            integerValue=10,
            decimalValue=decimal.Decimal(u'5.1'),
            booleanValue=True,
            dateValue=datetime.date(2010, 10, 1),
            datetimeValue=datetime.datetime(2010, 10, 1, 5, 10, 30),
            ))

        entity2 = createEntity(schema1, u'Bar', t1, dict(
            textValue=u'some\nbarvalue',
            stringValue=u'barvalue',
            integerValue=30,
            decimalValue=decimal.Decimal(u'1.89'),
            booleanValue=False,
            dateValue=datetime.date(2012, 5, 1),
            datetimeValue=datetime.datetime(2012, 5, 1, 16, 19),
            ))

        playn, subquery = reporting.schemaToReportByName(session, u'Sample')

        result = session.query(subquery).filter_by(entity_id=entity1.id).one()
        self.assertEqual(entity1[u'textValue'], result.textValue)
        self.assertEqual(entity1[u'stringValue'], result.stringValue)
        self.assertEqual(entity1[u'integerValue'], result.integerValue)
        self.assertEqual(entity1[u'booleanValue'], result.booleanValue)
        self.assertEqual(str(entity1[u'dateValue']), str(result.dateValue))
        self.assertEqual(str(entity1[u'datetimeValue']), str(result.datetimeValue))

        result = session.query(subquery).filter_by(entity_id=entity2.id).one()
        self.assertEqual(entity2[u'textValue'], result.textValue)
        self.assertEqual(entity2[u'stringValue'], result.stringValue)
        self.assertEqual(entity2[u'integerValue'], result.integerValue)
        self.assertEqual(entity2[u'booleanValue'], result.booleanValue)
        self.assertEqual(str(entity2[u'dateValue']), str(result.dateValue))
        self.assertEqual(str(entity2[u'datetimeValue']), str(result.datetimeValue))

#        # Now add a new version
#        schema2 = copy.deepcopy(schema1)
#        schema2.state = u'published'
#        schema2.publish_date = t2
#        schema2['a'].title = u'prime'
#        session.add(schema2)
#        session.flush()
#
#        entity3 = self.createEntity(schema2, u'Baz', t2, dict(a=u'bazvalue'))
#
#        plan, subquery = reporting.schemaToSubquery(session, u'A', reporting.BY_NAME)

