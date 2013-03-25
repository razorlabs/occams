u"""
Tests the schema report converter module
"""

import datetime
import decimal
import copy
import unittest2 as unittest

import sqlalchemy as sa
from sqlalchemy import orm

from occams.datastore import model
from occams.datastore import reporting
from occams.datastore import testing


t1 = datetime.date(2010, 3, 1)
t2 = datetime.date(2010, 9, 1)
t3 = datetime.date(2011, 8, 1)
t4 = datetime.date(2012, 5, 1)

BY_ID = lambda a: (a.name, a.id)
BY_NAME = lambda a: (a.name,)
BY_CHECKSUM = lambda a: (a.name, a.checksum)


class BuildDataDicTestCase(unittest.TestCase):

    layer = testing.OCCAMS_DATASTORE_FIXTURE

    def testEmptyPublishedSchema(self):
        session = self.layer[u'session']
        testing.createSchema(session, u'A', t1)
        data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        self.assertEqual(0, len(data_dict))

    def testKeysFromSingleForm(self):
        session = self.layer[u'session']
        schema = testing.createSchema(session, u'A', t1, dict(
            a=model.Attribute(type=u'string', order=0)))

        data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        expected = [(u'a',)]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(1, len(data_dict[expected[0]].attributes))

        data_dict = reporting.buildDataDict(session, u'A', BY_CHECKSUM)
        expected = [(u'a', schema[u'a'].checksum)]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(1, len(data_dict[expected[0]].attributes))

        data_dict = reporting.buildDataDict(session, u'A', BY_ID)
        expected = [(u'a', schema[u'a'].id)]
        self.assertListEqual(expected, data_dict.paths())
        for e in expected:
            self.assertEqual(1, len(data_dict[e].attributes))

    def testKeysFromMultpleVersions(self):
        session = self.layer[u'session']
        schema1 = testing.createSchema(session, u'A', t1, dict(
            a=model.Attribute(type=u'string', order=0)))

        schema2 = copy.deepcopy(schema1)
        schema2.state = u'published'
        schema2.publish_date = t2

        schema3 = copy.deepcopy(schema1)
        schema3.state = u'published'
        schema3.publish_date = t3
        schema3[u'a'].title = u'prime'

        session.add_all([schema1, schema2, schema3])

        data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        expected = [(u'a',)]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(3, len(data_dict[expected[0]].attributes))

        data_dict = reporting.buildDataDict(session, u'A', BY_CHECKSUM)
        expected = [(u'a', schema1[u'a'].checksum), (u'a', schema3[u'a'].checksum)]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(2, len(data_dict[expected[0]].attributes))
        self.assertEqual(1, len(data_dict[expected[1]].attributes))

        # by ID
        data_dict = reporting.buildDataDict(session, u'A', BY_ID)
        expected = [
            (u'a', schema1[u'a'].id),
            (u'a', schema2[u'a'].id),
            (u'a', schema3[u'a'].id)
            ]
        self.assertListEqual(expected, data_dict.paths())
        for e in expected:
            self.assertEqual(1, len(data_dict[e].attributes))

    def testKeysFromSubSchema(self):
        session = self.layer[u'session']
        schema = model.Schema(name=u'A', title=u'', state=u'published')
        schema[u'a'] = model.Attribute(title=u'', type=u'string', order=0)
        schema[u'b'] = model.Attribute(title=u'', type=u'object', order=1)
        schema[u'b'].object_schema = model.Schema(name=u'B', title=u'', state=u'published')
        schema[u'b'][u'x'] = model.Attribute(title=u'', type=u'string', order=0)
        schema[u'b'][u'y'] = model.Attribute(title=u'', type=u'string', order=1)
        schema[u'b'][u'z'] = model.Attribute(title=u'', type=u'string', order=2)
        schema[u'c'] = model.Attribute(title=u'', type=u'string', order=2)
        session.add(schema)
        session.flush()

        # by NAME
        data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        expected = [(u'a',), (u'b', u'x'), (u'b', u'y'), (u'b', u'z'), (u'c',)]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(1, len(data_dict[expected[0]].attributes))
        self.assertEqual(1, len(data_dict[expected[1]].attributes))
        self.assertEqual(1, len(data_dict[expected[2]].attributes))
        self.assertEqual(1, len(data_dict[expected[3]].attributes))
        self.assertEqual(1, len(data_dict[expected[4]].attributes))

        # by CHECKSUM
        data_dict = reporting.buildDataDict(session, u'A', BY_CHECKSUM)
        expected = [
            (u'a', schema[u'a'].checksum),
            (u'b', u'x', schema[u'b'][u'x'].checksum),
            (u'b', u'y', schema[u'b'][u'y'].checksum),
            (u'b', u'z', schema[u'b'][u'z'].checksum),
            (u'c', schema[u'c'].checksum),
            ]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(1, len(data_dict[expected[0]].attributes))
        self.assertEqual(1, len(data_dict[expected[1]].attributes))
        self.assertEqual(1, len(data_dict[expected[2]].attributes))
        self.assertEqual(1, len(data_dict[expected[3]].attributes))
        self.assertEqual(1, len(data_dict[expected[4]].attributes))

        # By ID
        data_dict = reporting.buildDataDict(session, u'A', BY_ID)
        expected = [
            (u'a', schema[u'a'].id),
            (u'b', u'x', schema[u'b'][u'x'].id),
            (u'b', u'y', schema[u'b'][u'y'].id),
            (u'b', u'z', schema[u'b'][u'z'].id),
            (u'c', schema[u'c'].id),
            ]
        self.assertListEqual(expected, data_dict.paths())
        for e in expected:
            self.assertEqual(1, len(data_dict[e].attributes))

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
        schema1 = model.Schema(name=u'A', title=u'', state=u'published', publish_date=t1)
        schema1[u'a'] = model.Attribute(title=u'', type=u'string', order=0)
        schema1[u'b'] = model.Attribute(title=u'', type=u'object', order=1)
        schema1[u'b'].object_schema = model.Schema(name=u'B', title=u'', state=u'published', publish_date=t1)
        schema1[u'b'][u'x'] = model.Attribute(title=u'', type=u'string', order=0)
        schema1[u'b'][u'y'] = model.Attribute(title=u'', type=u'string', order=1)
        schema1[u'b'][u'z'] = model.Attribute(title=u'', type=u'string', order=2)
        schema1[u'c'] = model.Attribute(title=u'', type=u'string', order=2)

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
        schema3[u'a'] = model.Attribute(name=u'a', title=u'', type=u'string', order=0)
        del schema3[u'b'][u'x']
        del schema3[u'b'][u'y']
        del schema3[u'c']
        schema3[u'y'] = model.Attribute(name=u'y', title=u'', type=u'string', order=2,)

        session.add_all([schema1, schema2, schema3])
        session.flush()

        # by NAME
        data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        expected = [(u'a',), (u'b', u'z'), (u'b', u'x'), (u'b', u'y'), (u'c',), (u'y',)]
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(3, len(data_dict[expected[0]].attributes))
        self.assertEqual(3, len(data_dict[expected[1]].attributes))
        self.assertEqual(2, len(data_dict[expected[2]].attributes))
        self.assertEqual(2, len(data_dict[expected[3]].attributes))
        self.assertEqual(2, len(data_dict[expected[4]].attributes))
        self.assertEqual(1, len(data_dict[expected[5]].attributes))

        # by CHECKSUM
        data_dict = reporting.buildDataDict(session, u'A', BY_CHECKSUM)
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
        self.assertListEqual(expected, data_dict.paths())
        self.assertEqual(2, len(data_dict[expected[0]].attributes))
        self.assertEqual(1, len(data_dict[expected[1]].attributes))
        self.assertEqual(3, len(data_dict[expected[2]].attributes))
        self.assertEqual(2, len(data_dict[expected[3]].attributes))
        self.assertEqual(1, len(data_dict[expected[4]].attributes))
        self.assertEqual(1, len(data_dict[expected[5]].attributes))
        self.assertEqual(2, len(data_dict[expected[6]].attributes))
        self.assertEqual(1, len(data_dict[expected[7]].attributes))

        # by ID
        data_dict = reporting.buildDataDict(session, u'A', BY_ID)
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
        self.assertListEqual(expected, data_dict.paths())
        for e in expected:
            self.assertEqual(1, len(data_dict[e].attributes))


#class ValueColumnTestCase(unittest.TestCase):
    #u"""
    #Collection of tests for scalar column generation
    #*Note* that these tests only use the header data to generate the
    #appropriately typed column, they assume nothing about the
    #separation algorithm used.
    #"""

    #layer = testing.OCCAMS_DATASTORE_FIXTURE

    #def testStringColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'string', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'string', value_class.__tablename__)
        #self.assertTrue(isinstance(value_column.type, sa.Unicode))

    #def testTextColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'text', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'string', value_class.__tablename__)
        #self.assertTrue(isinstance(value_column.type, sa.Unicode))

    #def testIntegerColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'integer', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'integer', value_class.__tablename__)
        #self.assertTrue(isinstance(value_column.type, sa.Integer))

    #def testDecimalColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'decimal', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'decimal', value_class.__tablename__)
        #self.assertTrue(isinstance(value_column.type, sa.Numeric))

    #@unittest.skipIf('sqlite' in testing.DEFAULT_URI, u'Vendor does not support date/time')
    #def testDateColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'date', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'datetime', value_class.__tablename__)
        #self.assertTrue(isinstance(value_column.type, sa.Date))

    #@unittest.skipIf('sqlite' not in testing.DEFAULT_URI, u'Vendor supports date/time')
    #def testStringDateColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'date', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'datetime', value_class.__tablename__)
        #self.assertEquals(u'date', value_column.name)

    #@unittest.skipIf('sqlite' in testing.DEFAULT_URI, u'Vendor does not support date/time')
    #def testDatetimeColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'datetime', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'datetime', value_class.__tablename__)
        #self.assertTrue(isinstance(value_column.type, sa.DateTime))

    #@unittest.skipIf('sqlite' not in testing.DEFAULT_URI, u'Vendor supports date/time')
    #def testStringDatetimeColumn(self):
        #session = self.layer[u'session']
        #testing.createSchema(session, u'A', t1, dict(
            #a=model.Attribute(type=u'datetime', order=0),
            #))
        #data_dict = reporting.buildDataDict(session, u'A', BY_NAME)
        #path, attributes = data_dict.items()[0]
        #value_class, value_column = reporting.getValueColumn(path, attributes)
        #self.assertEquals(u'datetime', value_class.__tablename__)
        #self.assertEquals(u'datetime', value_column.name)


class SchemaToQueryTestCase(unittest.TestCase):
    u""" Ensures that schema queries can by properly generated """

    layer = testing.OCCAMS_DATASTORE_FIXTURE

    def testExpectedMetadataColumns(self):
        session = self.layer[u'session']
        testing.createSchema(session, u'A', t1)

        data_dict, report = reporting.schemaToReportById(session, u'A')
        self.assertIn(u'entity_id', report.c)

        data_dict, report = reporting.schemaToReportByName(session, u'A')
        self.assertIn(u'entity_id', report.c)

        data_dict, report = reporting.schemaToReportByChecksum(session, u'A')
        self.assertIn(u'entity_id', report.c)

    def testEmptySchema(self):
        session = self.layer[u'session']
        schema = testing.createSchema(session, u'A', t1)

        data_dict, report = reporting.schemaToReportByName(session, u'A')
        self.assertEqual(0, session.query(report).count())

        testing.createEntity(schema, u'Sample', None)
        self.assertEqual(1, session.query(report).count())

    def testScalarValues(self):
        session = self.layer[u'session']

        # first version of the sample schema
        schema1 = testing.createSchema(session, u'Sample', t1, dict(
            value=model.Attribute(type=u'string', order=0),
            ))

        # add some entries for the schema
        entity1 = testing.createEntity(schema1, u'Foo', t1, dict(
            value=u'foovalue',
            ))

        # generate report by name, should be able to access attributes as columns
        data_dict, report = reporting.schemaToReportByName(session, u'Sample')
        result = session.query(report).filter_by(entity_id=entity1.id).one()
        self.assertEqual(entity1[u'value'], result.value)

    @unittest.skipIf(u'postgres' not in testing.DEFAULT_URI, u'Not using postgres')
    def testArrayCollectionValues(self):
        session = self.layer[u'session']

        schema1 = testing.createSchema(session, u'Sample', t1, dict(
            value=model.Attribute(type=u'string', is_collection=True, order=0),
            ))

        entity1 = testing.createEntity(schema1, u'Foo', t1, dict(
            value=[u'one', u'two'],
            ))

        data_dict, report = reporting.schemaToReportByName(session, u'Sample')
        result = session.query(report).filter_by(entity_id=entity1.id).one()
        self.assertListEqual(entity1[u'value'], result.value)

    @unittest.skipIf(u'postgres' in testing.DEFAULT_URI, u'Using ARRAY type')
    def testDelimitedCollectionValues(self):
        session = self.layer[u'session']

        schema1 = testing.createSchema(session, u'Sample', t1, dict(
            value=model.Attribute(type=u'string', is_collection=True, order=0),
            ))

        entity1 = testing.createEntity(schema1, u'Foo', t1, dict(
            value=[u'one', u'two'],
            ))

        data_dict, report = reporting.schemaToReportByName(session, u'Sample')
        result = session.query(report).filter_by(entity_id=entity1.id).one()
        expected_value = ','.join(entity1[u'value'])
        result_value = ','.join(entity1[u'value'])
        self.assertEqual(expected_value, result_value)

    def testObjectValues(self):
        session = self.layer[u'session']

        schema1 = model.Schema(
            name=u'Sample',
            title=u'',
            state=u'published',
            publish_date=t1
            )
        schema1[u'sub'] = model.Attribute(title=u'', type=u'object', order=0)
        schema1[u'sub'].object_schema = model.Schema(
            name=u'Sub',
            title=u'',
            state=u'published',
            publish_date=schema1.publish_date,
            is_inline=True
            )
        schema1[u'sub']['value'] = model.Attribute(title=u'', type=u'string', order=0)
        session.add(schema1)
        session.flush()

        entity1 = model.Entity(schema=schema1, name=u'Foo', title=u'', collect_date=t1)
        session.add(entity1)
        session.flush()
        entity1[u'sub'] = model.Entity(
            schema=schema1['sub'].object_schema, name=u'SubFoo', title=u'', collect_date=t1)
        session.flush()
        entity1[u'sub'][u'value'] = u'foovalue'
        session.flush()

        data_dict, report = reporting.schemaToReportByName(session, u'Sample')
        result = session.query(report).filter_by(entity_id=entity1.id).one()
        self.assertEqual(entity1[u'sub'][u'value'], result.sub_value)

