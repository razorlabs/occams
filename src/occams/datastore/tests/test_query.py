"""
Tests the schema subquery converter module
"""

import unittest2 as unittest
from datetime import date

from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore import model
from occams.datastore.query import schemaToSubQuery

p1 = date(2010, 05, 01)

class SchemaToSubQueryTestCase(unittest.TestCase):
    """
    Verifies the subquery adapter
    """

    layer = DATASTORE_LAYER

    def testBasic(self):
        session = self.layer['session']
        schemaA = model.Schema(name='A', title=u'', state='published', publish_date=p1)
        session.add(schemaA)
        session.flush()

        subquery = schemaToSubQuery(session, 'A', split=True)

        print subquery

