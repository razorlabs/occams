
import unittest2 as unittest

from zope.interface.verify import verifyClass

from zope.interface.common.sequence import IFiniteSequence

from z3c.batching.interfaces import IBatch

from occams.datastore import model
from occams.datastore.batch import SqlBatch
from occams.datastore.batch import SqlBatches

from occams.datastore.testing import DATABASE_LAYER


class BatchingTestCase(unittest.TestCase):
    """
    Verifies DataStore Entity storage
    """

    layer = DATABASE_LAYER

    def setUp(self):
        self.session = self.layer['session']
        self.session.add_all([
            model.Schema(name='Bar', title=u'Doesn\'t matter'), # 0
            model.Schema(name='Baz', title=u'Doesn\'t matter'), # 1
            model.Schema(name='Caz', title=u'Doesn\'t matter'), # 2
            model.Schema(name='Foo', title=u'Doesn\'t matter'), # 3
            model.Schema(name='Jaz', title=u'Doesn\'t matter'), # 4
            model.Schema(name='Raz', title=u'Doesn\'t matter'), # 5
            ])
        self.session.flush()

    def test_implementation(self):
        self.assertTrue(verifyClass(IBatch, SqlBatch))
        self.assertTrue(verifyClass(IFiniteSequence, SqlBatches))

    def test_first_element(self):
        session = self.session
        query = session.query(model.Schema).order_by(model.Schema.name)
        batch = SqlBatch(query)
        (id, item) = batch.firstElement
        self.assertNotEqual(id, None)
        self.assertTrue(item.name, 'Bar')

    def test_last_element(self):
        session = self.session
        query = session.query(model.Schema).order_by(model.Schema.name)
        batch = SqlBatch(query)
        (id, item) = batch.firstElement
        self.assertNotEqual(id, None)
        self.assertTrue(item.name, 'Raz')

    def test_getitem(self):
        session = self.session
        query = session.query(model.Schema).order_by(model.Schema.name)
        batch = SqlBatch(query)
        (id, item) = batch[3]
        self.assertNotEqual(id, None)
        self.assertTrue(item.name, 'Foo')
        self.assertRaises(IndexError, batch.__getitem__, 10)

    def test_len(self):
        session = self.session
        query = session.query(model.Schema).order_by(model.Schema.name)
        batch = SqlBatch(query)
        self.assertTrue(len(batch), 6)

    def test_contains(self):
        session = self.session
        query = session.query(model.Schema).order_by(model.Schema.name)
        batch = SqlBatch(query)
        item = session.query(model.Schema).filter_by(name='Bar').first()
        self.assertTrue(item in batch)

        item = model.Schema(id=99, name='Blarg', title=u'Blah')
        self.assertFalse(item in batch)

    def test_getslice_(self):
        session = self.session
        query = session.query(model.Schema).order_by(model.Schema.name)
        batch = SqlBatch(query)
        generator = batch[2:4]
        self.assertNotEqual(None, generator)
        names = tuple([r.name for i, r in generator])
        self.assertEqual(('Caz', 'Foo'), names)

    def test_eq(self):
        session = self.session
        query = session.query(model.Schema)
        batch = SqlBatch(query)
        other = SqlBatch(query)
        # Works with batches with the same query instance
        self.assertEqual(batch, other)
        other = SqlBatch(session.query(model.Schema))
        # Doesn't work with same query, yet different query object
        self.assertNotEqual(batch, other)
        other = SqlBatch(query, size=1000)
        self.assertNotEqual(batch, other)
