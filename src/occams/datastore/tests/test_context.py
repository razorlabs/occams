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

    def testAdd(self):
        session = scoped_session(sessionmaker(
            bind=create_engine('sqlite://'),
            class_=model.DataStoreSession,
            user=lambda:'foo@foo.com'
        ))

        class SampleClass1(model.Model, HasEntities):
            __tablename__ = 'sampleclass1'

            id = Column(Integer, primary_key=True)

            name = Column(String, nullable=False)

        class SampleClass2(model.Model, HasEntities):
            __tablename__ = 'sampleclass2'

            id = Column(Integer, primary_key=True)

            name = Column(String, nullable=False)

        # Register a default user
        model.Model.metadata.create_all(session.bind)
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

        # Now suppose that we only have an entity and want to know its parents
        # Example: get all the SomeClassX references of an entity

        query = session.query(model.Entity).filter_by(name=u'foo')
        entity = query.one()

        sc1list = [c.sampleclass1_parent.name for c in entity.contexts if c.sampleclass1_parent]
        self.assertItemsEqual(['Foo'], sc1list)

        # Now try adding the entity to an additional context
        session.add(SampleClass1(name='Jar', entities=[entity]))
        session.flush()

        sc1list = [c.sampleclass1_parent.name for c in entity.contexts if c.sampleclass1_parent]
        self.assertItemsEqual(['Foo', 'Jar'], sc1list)

        # But what if you want to query them directly? Same as above, query
        # for a SampleClass that contains the specific schemata you want
        query = (
            session.query(SampleClass1)
            .filter(SampleClass1.entities.any(model.Entity.name == u'foo'))
            )

        sc1list = [sc1.name for sc1 in query]
        self.assertItemsEqual(['Foo', 'Jar'], sc1list)
