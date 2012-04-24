"""
Tests the schema subquery converter module
"""

import unittest2 as unittest
from datetime import date

from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore import model
from occams.datastore.interfaces import InvalidEntitySchemaError
from occams.datastore.query import Split
from occams.datastore.query import schemaToSubQuery
from occams.datastore.query import getAttributes
from occams.datastore.schema import copy


p1 = date(2010, 3, 1)
p2 = date(2010, 9, 1)
p3 = date(2011, 8, 1)
p4 = date(2012, 5, 1)


class QueryTestCase(unittest.TestCase):
    """
    Verifies the subquery adapter
    """

    layer = DATASTORE_LAYER

    def testGetAttributes(self):
        session = self.layer['session']
        schema1 = model.Schema(
            name='A',
            title=u'',
            state='published',
            publish_date=p1,
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                )
            )
        session.add(schema1)

        names, columns = getAttributes(session, 'A', split=Split.NAME)
        self.assertItemsEqual(['a'], names)
        self.assertItemsEqual(['a'], columns.keys())

        names, columns = getAttributes(session, 'A', split=Split.CHECKSUM)
        expected = ['a_' + schema1['a'].checksum]
        self.assertItemsEqual(expected, names)
        self.assertItemsEqual(expected, columns.keys())

        schema2 = model.Schema(
            name='A',
            title=u'',
            state='published',
            publish_date=p2,
            attributes=dict(
                a=model.Attribute(name='a', title=u'New title', type='string', order=0),
                )
            )
        session.add(schema2)

        names, columns = getAttributes(session, 'A', split=Split.NAME)
        self.assertItemsEqual(['a'], names)
        self.assertItemsEqual(['a'], columns.keys())

        names, columns = getAttributes(session, 'A', split=Split.CHECKSUM)
        expected = ['a_' + schema1['a'].checksum, 'a_' + schema2['a'].checksum]
        self.assertItemsEqual(expected, names)
        self.assertItemsEqual(expected, columns.keys())

    def testGetAttributesWithSubSchema(self):
        session = self.layer['session']
        schema1 = model.Schema(
            name='Main',
            title=u'',
            state='published',
            publish_date=p1,
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                sub=model.Attribute(
                    name='sub',
                    title=u'',
                    type='object',
                    order=1,
                    object_schema=model.Schema(
                        name='Sub',
                        title=u'',
                        state='published',
                        publish_date=p1,
                        attributes=dict(
                            x=model.Attribute(name='x', title=u'', type='string', order=0),
                            )
                        )
                    )
                )
            )
        session.add(schema1)

        names, columns = getAttributes(session, 'Main', split=Split.NAME)
        expected = ['a', 'sub_x']
        self.assertItemsEqual(expected, names)
        self.assertItemsEqual(expected, columns.keys())

        names, columns = getAttributes(session, 'Main', split=Split.CHECKSUM)
        expected = ['a_' + schema1['a'].checksum, 'sub_x_' + schema1['sub']['x'].checksum]
        self.assertItemsEqual(expected, names)
        self.assertItemsEqual(expected, columns.keys())

        schema2 = copy(schema1)
        schema2.state = u'published'
        schema2.publish_date = p2
        schema2['sub'].object_schema.state = u'published'
        schema2['sub'].object_schema.publish_date = p2
        schema2['sub']['x'].title = u'New title'
        session.add(schema2)
        session.flush()

        names, columns = getAttributes(session, 'Main', split=Split.NAME)
        expected = ['a', 'sub_x']
        self.assertItemsEqual(expected, names)
        self.assertItemsEqual(expected, columns.keys())

        names, columns = getAttributes(session, 'Main', split=Split.CHECKSUM)
        expected = [
            'a_' + schema1['a'].checksum,
            'sub_x_' + schema1['sub']['x'].checksum,
            'sub_x_' + schema2['sub']['x'].checksum,
            ]

        self.assertItemsEqual(expected, names)
        self.assertItemsEqual(expected, columns.keys())

    def testUnpublishedSchema(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='draft')
        session.add(schema)
        session.flush()

        with self.assertRaises(InvalidEntitySchemaError):
            subquery = schemaToSubQuery(session, 'A', split=False)

    def testEmptySchema(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='published', publish_date=p1)
        session.add(schema)
        session.flush()

        subquery = schemaToSubQuery(session, 'A', split=True)

        self.assertEqual(0, session.query(subquery).count())

        entity = model.Entity(schema=schema, name='Sample', title=u'')
        session.add(entity)
        session.flush()

        self.assertEqual(1, session.query(subquery).count())

    def testFlatSchemaWithString(self):
        session = self.layer['session']
        schema = model.Schema(
            name='A',
            title=u'',
            state='published',
            publish_date=p1,
            attributes=dict(
                a=model.Attribute(name='a', title=u'', type='string', order=0),
                )
            )
        session.add(schema)
        session.flush()

        entity = model.Entity(schema=schema, name='Foo', title=u'')
        session.add(entity)
        entity['a'] = u'foo'
        session.flush()

        entity = model.Entity(schema=schema, name='Bar', title=u'')
        session.add(entity)
        entity['a'] = u'Bar'
        session.flush()

        subquery = schemaToSubQuery(session, 'A', split=True)
        for s in session.query(subquery):
            print s

    def testSubSchemataWithString(self):
        pass
