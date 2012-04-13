import datetime
import unittest2 as unittest

import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from occams.datastore import model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.interfaces import NonExistentUserError
from occams.datastore.testing import DATASTORE_LAYER


class AutoNamingTestCase(unittest.TestCase):

    def testBasic(self):
        Base = declarative_base(bind=create_engine('sqlite://'))

        class SomeClass(AutoNamed, Base):
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        Base.metadata.create_all()

        self.assertEqual('someclass', SomeClass.__table__.name)

    def testInherited(self):
        Base = declarative_base(bind=create_engine('sqlite://'))

        class BaseClass(AutoNamed, Base):
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
            type = Column(String(50))
            __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'base'}

        class SubClass(BaseClass):
            subname = Column(String(50), unique=True)
            __mapper_args__ = {'polymorphic_identity':'sub'}

        Base.metadata.create_all()
        self.assertEqual('baseclass', BaseClass.__table__.name)
        self.assertEqual('baseclass', SubClass.__table__.name)


class ModifiableMixinTestCase(unittest.TestCase):
    """
    Verifies modifiable extensions
    """

    # TODO: it would be nice to be able to test this as a datastore-unaware
    # class, but there are too many moving parts that modifiable depends on,
    # such as the ``User`` table, which is attached to the product's model
    # and would be dangerous to extend in this module as it's sitting
    # alongside the production code. Perhaps one day we can move these tests
    # into their own separate package and then extend ``Model`` in a test sample.

    layer = DATASTORE_LAYER

    def testBasic(self):
        """
        Test is new mappings obey the modifiable extension properly
        """
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()

        message = 'No metadata added to '
        for check in ('create_date', 'create_user_id', 'modify_date', 'modify_user_id'):
            self.assertIsNotNone(getattr(schema, check), message)

    def testInvalidDate(self):
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()

        # Make sure we can't use an incorrect timeline
        schema.create_date += datetime.timedelta(1)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.flush()

    def testNonExistentUser(self):
        # Use the current connection
        engine = self.layer['session'].bind

        # Use a separate session that pools users from an "unknown" source
        renegadeSession = scoped_session(sessionmaker(
            bind=engine,
            class_=model.DataStoreSession,
            user=lambda: 'nonexistent@trollolol.com'
        ))

        schema = model.Schema(name='Foo', title=u'')
        renegadeSession.add(schema)

        with self.assertRaises(NonExistentUserError):
            renegadeSession.flush()

