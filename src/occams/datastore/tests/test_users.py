import datetime
import unittest2 as unittest

import sqlalchemy.exc
from occams.datastore.interfaces import NotFoundError
from occams.datastore import model
from occams.datastore.testing import OCCAMS_DATASTORE_FIXTURE
from occams.datastore.users import UserManager


class UserModelTestCase(unittest.TestCase):
    """
    Verifies user storage
    """

    layer = OCCAMS_DATASTORE_FIXTURE

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
        user = model.User(key='mr.foo@foomail.com')
        session.add(user)
        session.flush()
        self.assertIsNotNone(user.id, 'User was not flushed')

        # Make sure the dates are valid
        self.assertEqual(user.create_date, user.modify_date, 'Different create dates')

        # Make sure we can't use an incorrect timeline
        user.create_date += datetime.timedelta(1)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.flush()

        # Clear the transaction in case we want to do anything else
        session.rollback()

    def testRemoteFailOnActiveUser(self):
        # Should not be able to remove a user that has modified the data
        pass


class UserManagerTestCase(unittest.TestCase):

    layer = OCCAMS_DATASTORE_FIXTURE

    def testKeys(self):
        session = self.layer['session']
        manager = UserManager(session)
        self.assertNotIn('foo@foo.com', manager.keys())
        session.add(model.User(key='foo@foo.com'))
        session.flush()
        self.assertIn('foo@foo.com', manager.keys())

    def testHas(self):
        session = self.layer['session']
        manager = UserManager(session)
        self.assertFalse(manager.has('foo@foo.com'))
        session.add(model.User(key='foo@foo.com'))
        session.flush()
        self.assertTrue(manager.has('foo@foo.com'))

    def testPurge(self):
        session = self.layer['session']
        manager = UserManager(session)
        self.assertEqual(0, manager.purge('foo@foo.com'))
        session.add(model.User(key='foo@foo.com'))
        session.flush()
        self.assertEqual(1, manager.purge('foo@foo.com'))

    def testPut(self):
        session = self.layer['session']
        manager = UserManager(session)
        with self.assertRaises(NotFoundError):
            manager.get('foo@foo.com')

        user = model.User(key='foo@foo.com')
        session.add(user)
        session.flush()
        guser = manager.get('foo@foo.com')
        self.assertEqual(user, guser)

    def testGet(self):
        session = self.layer['session']
        manager = UserManager(session)

        # Needs a name
        with self.assertRaises(ValueError):
            manager.put(None, model.User())

        # Auto sets the name from the key
        user = model.User()
        id = manager.put('foo@foo.com', user)
        self.assertEqual('foo@foo.com', user.key)
        self.assertEqual(id, user.id)
        self.assertEqual(user, session.query(model.User).get(id))

        # Ignores the key since the item already has one
        user = model.User(key='bar@foo.com')
        id = manager.put(None, user)
        self.assertEqual(id, user.id)
        self.assertEqual(user, session.query(model.User).get(id))

