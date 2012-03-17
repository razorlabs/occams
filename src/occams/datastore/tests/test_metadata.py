import datetime
import unittest2 as unittest

from sqlalchemy import DDL
import sqlalchemy.exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declared_attr

from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.metadata import buildModifiableConstraints
from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER


class UserTestCase(unittest.TestCase):
    """
    Verifies user storage
    """

    layer = DATASTORE_LAYER

    def testAdd(self):
        session = self.layer['session']

        # Try adding a faulty user
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            user = model.User()
            session.add(user)
            session.flush()

        # That should have not worked, in which case we'll clear the transaction
        session.rollback()

        # Try adding a valid user now
        user = model.User(email='mr.foo@foomail.com')
        session.add(user)
        session.flush()
        self.assertIsNotNone(user.id, 'User was not flushed')

        # Make sure the dates are valid
        self.assertTrue(user.create_date == user.modify_date, 'Different create dates')

        # Make sure we can't use an incorrect timeline
        user.create_date += datetime.timedelta(1)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.flush()

        # Clear the transaction in case we want to do anything else
        session.rollback()


class ModifiableTestCase(unittest.TestCase):
    """
    Verifies modifiable extensions
    """

    def testExtension(self):
        """
        Test is new mappings obey the modifiable extension properly
        """

        # Creating a table commits the connection (and our setup data, which
        # we con't want), so we'll need a separate session to work with
        engine = create_engine('sqlite:///')
        DDL('PRAGMA foreign_keys=ON').execute(engine)
        session = scoped_session(sessionmaker(engine))
        model.User.__table__.create(engine)

        class Foo(model.Model, Modifiable):
            __tablename__ = 'foo'

            id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

            value = sqlalchemy.Column(sqlalchemy.Unicode, nullable=False)

            @declared_attr
            def __table_args__(cls):
                return buildModifiableConstraints(cls)

        Foo.__table__.create(bind=session.bind)

        foo = Foo(value=u'foo')
        session.add(foo)
        session.flush()

        message = 'No metadata added to '
        for check in ('create_date', 'create_user_id', 'modify_date', 'modify_user_id'):
            self.assertIsNotNone(getattr(foo, check), message)

        import pdb; pdb.set_trace()

        # Make sure we can't use an incorrect timeline
        foo.create_date += datetime.timedelta(1)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.flush()

        # Clear the transaction in case we want to do anything else
        session.rollback()

        foo = Foo(value=u'foo')
        session.add(foo)
        session.flush()


