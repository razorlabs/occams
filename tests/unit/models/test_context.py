"""
Test for contextual associations
"""

import unittest2 as unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from occams.datastore import model
from occams.datastore.model.storage import HasEntities


class HasEntitiesTestCase(unittest.TestCase):
    """
    Test the mixin class
    """

    def testUsage(self):
        session = scoped_session(sessionmaker(
            bind=create_engine('sqlite://'),
            class_=model.DataStoreSession,
            user=lambda:'foo@foo.com'
        ))

        class SampleClass1(model.DataStoreModel, HasEntities):
            __tablename__ = 'sampleclass1'

            id = Column(Integer, primary_key=True)

            name = Column(String, nullable=False)

        class SampleClass2(model.DataStoreModel, HasEntities):
            __tablename__ = 'sampleclass2'

            id = Column(Integer, primary_key=True)

            name = Column(String, nullable=False)

        # Register a default user
        model.DataStoreModel.metadata.create_all(session.bind)
        session.add(model.User(key='foo@foo.com'))
        session.flush()

        # Sample schemata
        schemaA = model.Schema(name=u'A', title=u'', state='published')
        schemaB = model.Schema(name=u'B', title=u'', state='published')

        session.add_all([
            SampleClass1(
                name='Foo',
                entities=[
                    model.Entity(schema=schemaA, name='foo', title=u''),
                    model.Entity(schema=schemaA, name='bar', title=u''),
                    model.Entity(schema=schemaB, name='baz', title=u''),
                    ]
                ),
            SampleClass2(
                name='Bar',
                entities=[
                    model.Entity(schema=schemaA, name='caz', title=u''),
                    model.Entity(schema=schemaB, name='raz', title=u''),
                    ]
                )
            ])

        session.flush()

        # Verify that the data was correctly associated
        sc1 = session.query(SampleClass1).filter_by(name='Foo').one()
        self.assertEqual(3, len(sc1.entities))
        self.assertItemsEqual(['foo', 'bar', 'baz'], [e.name for e in sc1.entities])

        # Add one more to verify collection_class is of type "set"
        sc1.entities.add(model.Entity(schema=schemaB, name='car', title=u''),)
        session.flush()
        self.assertItemsEqual(['foo', 'bar', 'baz', 'car'], [e.name for e in sc1.entities])

        sc2 = session.query(SampleClass2).filter_by(name='Bar').one()
        self.assertEqual(2, len(sc2.entities))
        self.assertItemsEqual(['raz', 'caz'], [e.name for e in sc2.entities])

        # I want a SampleClass1 that contains specific schemata
        query = (
            session.query(SampleClass1)
            .filter(SampleClass1.name == 'Foo')
            .filter(SampleClass1.entities.any(model.Schema.name == u'A'))
            )

        sc1 = query.one()
        self.assertIsNotNone(sc1)

        # Now suppose that we only have an fooEntity and want to know its parents
        # Example: get all the SomeClassX references of an fooEntity

        fooEntity = session.query(model.Entity).filter_by(name=u'foo').one()

        sc1list = [c.sampleclass1_parent.name for c in fooEntity.contexts if c.sampleclass1_parent]
        self.assertItemsEqual(['Foo'], sc1list)

        # Querying them directly
        # There is no clean way of querying for an fooEntity by context in
        # a generic association setting, as it would have to know about
        # all ``HasEntities`` classes that reference it
        sc1EntitiesQuery = (
            session.query(model.Entity)
            .join(model.Entity.contexts)
            .filter(model.Context.external == u'sampleclass1')
            .join(SampleClass1, (SampleClass1.id == model.Context.key))
            .filter(SampleClass1.name == 'Foo')
            )

        entitylist = [e.name for e in sc1EntitiesQuery]
        self.assertItemsEqual(['foo', 'bar', 'car', 'baz'], entitylist)

        # Now try adding the fooEntity to an additional context
        session.add(SampleClass1(name='Jar', entities=[fooEntity]))
        session.flush()

        sc1list = [c.sampleclass1_parent.name for c in fooEntity.contexts if c.sampleclass1_parent]
        self.assertItemsEqual(['Foo', 'Jar'], sc1list)

        # But what if you want to query them directly? Same as above, query
        # for a SampleClass that contains the specific schemata you want
        hasFooQuery = (
            session.query(SampleClass1)
            .filter(SampleClass1.entities.any(model.Entity.name == u'foo'))
            )

        sc1list = [sc1.name for sc1 in hasFooQuery]
        self.assertItemsEqual(['Foo', 'Jar'], sc1list)

        # Now try deleting a context object
        sc1 = session.query(SampleClass1).filter_by(name=u'Foo').one()
        session.delete(sc1)
        session.flush()

        self.assertEqual(0, sc1EntitiesQuery.count())

        # Make sure we didn't accidentally remote the data from 'Jar'
        sc1list = [sc1.name  for sc1 in hasFooQuery]
        self.assertItemsEqual(['Jar'], sc1list)

        # Double check just in case
        self.assertEqual(1, session.query(model.Context).filter_by(external='sampleclass1').count())
        self.assertEqual(1, session.query(model.Entity).filter_by(name=u'foo').count())

        # TODO Currently there is absolutely no way to remove orphans. The
        # application must do this manually. This is because assocation proxies
        # cannot delete orphans and the way the relationships are setup, it
        # does not allow this..
        #self.assertEqual(0, session.query(model.Entity).filter_by(name=u'bar').count())
        #self.assertEqual(0, session.query(model.Entity).filter_by(name=u'baz').count())

