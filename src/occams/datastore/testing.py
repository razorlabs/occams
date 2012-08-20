u"""
Application layers
"""

import sqlalchemy as sa
from sqlalchemy import orm
import plone.testing

from occams.datastore import model as datastore


# Vendor-specific URIs, note that some tests still use the SQLite URI for
# general proof-of-concept testing (auditing, metadata, batching, etc)

SQLITE_URI = u'sqlite://'

# Use this if you have a testing database setup, if only there was an in-memory
# postgres database...
PSQL_URI = u'postgresql://tester:test1234@localhost/datastore_test'

DEFAULT_URI = SQLITE_URI
#DEFAULT_URI = PSQL_URI


class OccamsDataStoreLayer(plone.testing.Layer):
    u"""
    DataBase application layer for tests.

    Important GOTCHA:  if you are plugging into DataStore with additional models,
    make sure that their metadata has been loaded into the ``Model`` declarative
    base, otherwise they wont be available during testing. Rarely will
    this be an issue and will possibly even go unnoticed, unless the client
    application is doing something exotic like deferring the loading of the
    model classes.
    """

    def setUp(self):
        u"""
        Creates the database structures.
        """
        engine = sa.create_engine(DEFAULT_URI, echo=False)
        datastore.DataStoreModel.metadata.drop_all(engine, checkfirst=True)
        datastore.DataStoreModel.metadata.create_all(engine, checkfirst=False)
        self[u'session'] = orm.scoped_session(orm.sessionmaker(
            bind=engine,
            class_=datastore.DataStoreSession,
            user=lambda: u'bitcore@ucsd.edu'
            ))

    def tearDown(self):
        u"""
        Destroys the database structures.
        """
        self[u'session'].close()
        del self[u'session']

    def testSetUp(self):
        u"""
        Preloads data for each test case method
        """
        session = self[u'session']
        user = datastore.User(key=u'bitcore@ucsd.edu')
        session.add(user)
        session.flush()
        self[u'user'] = user

    def testTearDown(self):
        u"""
        Cancels the transaction after each test case method.
        """
        self[u'session'].rollback()


OCCAMS_DATASTORE_FIXTURE = OccamsDataStoreLayer()


def createSchema(session, name, publish_date=None, attributes=None):
    u"""
    Helper method to create schemata
    """
    schema = datastore.Schema(name=name, title=u'')
    if publish_date is not None:
        schema.state = u'published'
        schema.publish_date = publish_date
    if attributes:
        for attribute_name, attribute in attributes.iteritems():
            if attribute.title is None:
                # Set empty title if lazy
                attribute.title = u''
            schema[attribute_name] = attribute
    session.add(schema)
    session.flush()
    return schema


def createEntity(schema, name, collect_date, values=None):
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
    if values is not None:
        for key, value in values.iteritems():
            entity[key] = value
    session.flush()
    return entity

