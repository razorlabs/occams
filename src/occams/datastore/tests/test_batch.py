
import unittest2 as unittest
import plone.testing
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base
from zope.interface.verify import verifyClass
from zope.interface.common.sequence import IFiniteSequence
from z3c.batching.interfaces import IBatch

from occams.datastore.batch import SqlBatch
from occams.datastore.batch import SqlBatches


Base = declarative_base()


class Sample(Base):
    __tablename__ = 'sample'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def objectify(self):
        """
        Make sure the legacy crap still works...
        """
        return self


class BatchingTestCase(unittest.TestCase):
    """
    Verifies proper sqlalchemy batching
    """

    class BatchingLayer(plone.testing.Layer):
        """
        Local layer for testing made-up mappers
        """

        def setUp(self):
            engine = create_engine('sqlite://')
            self['session'] = scoped_session(sessionmaker(bind=engine))
            Base.metadata.create_all(engine)

        def testTearDown(self):
            self['session'].rollback()

    layer = BatchingLayer()

    def setUp(self):
        session = self.layer['session']

        # Sample test data so that we don't have to keep recreating it
        session.add_all([
            Sample(name='Bar'), # 0
            Sample(name='Baz'), # 1
            Sample(name='Caz'), # 2
            Sample(name='Foo'), # 3
            Sample(name='Jaz'), # 4
            Sample(name='Raz'), # 5
            ])
        session.flush()

    def testImplementation(self):
        self.assertTrue(verifyClass(IBatch, SqlBatch))
        self.assertTrue(verifyClass(IFiniteSequence, SqlBatches))

    def testInit(self):
        session = self.layer['session']
        # Validate proper starting point with empty sequence
        query = session.query(Sample).limit(0)
        batch = SqlBatch(query)
        self.assertEqual(0, batch.start)
        self.assertEqual(0, batch.end)

        # Validate improper starting point past the length
        query = session.query(Sample)
        with self.assertRaises(IndexError):
            batch = SqlBatch(query, start=10)

        # Validate correct "true size" (the number of remaining items in the batch)
        query = session.query(Sample)
        batch = SqlBatch(query, start=0, size=3)
        self.assertEqual(3, batch._trueSize)
        self.assertEqual(2, batch.end)

        # Since the batch is greater than the total number of items, it will
        # just return the number of remaining
        batch = SqlBatch(query, start=0, size=10)
        self.assertEqual(6, batch._trueSize)
        self.assertEqual(5, batch.end)

    def testFirstElement(self):
        session = self.layer['session']
        query = session.query(Sample).order_by(Sample.name)
        batch = SqlBatch(query)
        (id, item) = batch.firstElement
        self.assertIsNotNone(id)
        self.assertEqual(item.name, 'Bar')

    def testLastElement(self):
        session = self.layer['session']
        query = session.query(Sample).order_by(Sample.name)
        batch = SqlBatch(query)
        (id, item) = batch.lastElement
        self.assertIsNotNone(id)
        self.assertEqual(item.name, 'Raz')

    def testGetItem(self):
        session = self.layer['session']
        query = session.query(Sample).order_by(Sample.name)
        batch = SqlBatch(query)
        (id, item) = batch[3]
        self.assertIsNotNone(id)
        self.assertEqual(item.name, 'Foo')
        with self.assertRaises(IndexError):
            batch[10]

    def testLen(self):
        session = self.layer['session']

        query = session.query(Sample).limit(0)
        batch = SqlBatch(query)
        self.assertEqual(0, len(batch))

        query = session.query(Sample).order_by(Sample.name)
        batch = SqlBatch(query)
        self.assertEqual(len(batch), 6)

    def testContains(self):
        session = self.layer['session']
        query = session.query(Sample).order_by(Sample.name)
        batch = SqlBatch(query)
        item = self.layer['session'].query(Sample).filter_by(name='Bar').one()
        self.assertIn(item, batch)

        item = Sample(id=99, name='Blarg')
        self.assertNotIn(item, batch)

    def testGetSlice(self):
        session = self.layer['session']
        query = session.query(Sample).order_by(Sample.name)
        batch = SqlBatch(query)

        # Doesn't like negative numbers
        batch[-1:4]

        generator = batch[2:4]
        self.assertIsNotNone(generator)
        names = [r.name for i, r in generator]
        self.assertListEqual(['Caz', 'Foo'], names)

        # Should anchor to the "tru size"
        generator = batch[4:200]
        names = [r.name for i, r in generator]
        self.assertListEqual(['Jaz', 'Raz'], names)

    def testEquals(self):
        session = self.layer['session']
        query = session.query(Sample)
        batch = SqlBatch(query)
        other = SqlBatch(query)
        # Works with batches with the same query instance
        self.assertEqual(batch, other)
        other = SqlBatch(session.query(Sample))
        # Doesn't work with same query, yet different query object
        self.assertNotEqual(batch, other)
        other = SqlBatch(query, size=1000)
        self.assertNotEqual(batch, other)

    def testBatches(self):
        session = self.layer['session']
        query = session.query(Sample)
        # Will generate three "pages" of two items each
        batch = SqlBatch(query, size=2)
        page1 = batch.batches[0]
        self.assertEqual(batch, page1)

        page2 = batch.batches[1]
        self.assertNotEqual(batch, page2)
        self.assertListEqual(['Caz', 'Foo'], [r.name for i, r in page2])

        # Not go backwards, by getting the last page
        last = batch.batches[-1]
        self.assertNotEqual(batch, last)
        self.assertListEqual(['Jaz', 'Raz'], [r.name for i, r in last])
