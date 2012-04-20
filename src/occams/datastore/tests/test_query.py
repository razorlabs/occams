"""
Tests the schema subquery converter module
"""

import unittest2 as unittest
from datetime import date

from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore import model
from occams.datastore.query import schemaToSubQuery
from occams.datastore.schema import copy


p1 = date(2010, 3, 1)
p2 = date(2010, 9, 1)
p3 = date(2011, 8, 1)
p4 = date(2012, 5, 1)


class SchemaToSubQueryTestCase(unittest.TestCase):
    """
    Verifies the subquery adapter
    """

    layer = DATASTORE_LAYER

    def testUnpublished(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='draft')
        session.add(schema)
        session.flush()

#        subquery = schemaToSubQuery(session, 'A', split=True)

    def testEmpty(self):
        session = self.layer['session']
        schema = model.Schema(name='A', title=u'', state='published', publish_date=p1)
        session.add(schema)
        session.flush()

        subquery = schemaToSubQuery(session, 'A', split=True)

    def testFlatString(self):
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

    def testSubSchemata(self):
        pass


